from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import google.generativeai as genai
from .models import Course, Unit, Chapter,Question
from subscription.models import UserSubscription
from .gpt import generate_chapters,model
from django.shortcuts import get_object_or_404
from .serializers import CourseSerializer,ChapterSerializer
from rest_framework.permissions import BasePermission
from rest_framework.generics import ListAPIView
from django.db.models import Prefetch
from django.core.exceptions import ObjectDoesNotExist
from .youtube import search_youtube, get_transcript, get_questions_from_transcript
from rest_framework import generics
import traceback
import json
import random
import ast
from django.utils import timezone
from datetime import timedelta
from rest_framework.pagination import PageNumberPagination

class CreateChapterAPIView(APIView):
    def post(self, request):
        title = request.data.get('title')
        units = request.data.get('units', [])
        user_id = request.user.id  

        if not title or not units:
            return Response({"error": "Title and units are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = request.user
            user_subscription = UserSubscription.objects.filter(user=user).first()
            has_active_subscription = False

            if user_subscription:
                DAY_IN_MS = timedelta(days=1)
                current_time = timezone.now()
                has_active_subscription = (
                    user_subscription.stripe_price_id and
                    user_subscription.stripe_current_period_end and
                    (user_subscription.stripe_current_period_end + DAY_IN_MS) > current_time
                )

            if not has_active_subscription and user.credits <= 0:
                return Response({"error": "No credits remaining"}, status=status.HTTP_402_PAYMENT_REQUIRED)

            response_data = generate_chapters(title, units, user_id)

            if not has_active_subscription:
                user.credits -= 1
                user.save()

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CourseListAPIView(ListAPIView):
    serializer_class = CourseSerializer
    def get_queryset(self):
        try:
            user = self.request.user
            query = self.request.query_params.get('search')

            if query:
               queryset = Course.objects.filter(user=user, name__icontains=query)
            else:
               queryset =  Course.objects.filter(user=user)
               
            return queryset
        except ObjectDoesNotExist:
            raise Http404("No Course matches the given query.")
        except Exception as e:
            raise Http404("An error occurred while fetching courses: {}".format(str(e)))
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({'message': 'No search results found.'}, status=status.HTTP_404_NOT_FOUND)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
class IsCourseOwner(BasePermission):
   
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
    
class CourseRetrieveAPIView(ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsCourseOwner]
    def list(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        user = request.user 
        try:
            course = Course.objects.get(pk=pk)
            units = Unit.objects.filter(course=course).prefetch_related('chapter')
            course.units.set(units)
            serializer = self.get_serializer(course)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return Response({"error": "Course with id {} does not exist".format(pk), 'message': 'No search results found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e), 'message': 'No search results found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
class ChapterInfoAPIView(APIView):
    def post(self, request, *args, **kwargs):
        chapter_id = request.data.get('chapterId')
        if not chapter_id:
            return Response({"success": False, "error": "Invalid body"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            chapter = Chapter.objects.get(id=chapter_id)
        except Chapter.DoesNotExist:
            return Response({"success": False, "error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # print("chapter title", chapter.youtubeSearchQuery)
            video_id = search_youtube(chapter.youtubeSearchQuery)
            # print("video id", video_id)
            if not video_id:
                return Response({"success": False, "error": "Video not found"}, status=status.HTTP_404_NOT_FOUND)
            
            transcript = get_transcript(video_id)
            # print("transcript_view:", transcript)
            
            if not transcript:
                chapter.videoId = video_id
                chapter.save()
                
                return Response({"success": True, "videoId": video_id, "error": "Transcript not found"}, status=status.HTTP_200_OK)
            
            summary = model.generate_content(
                "You are an AI capable of summarising a YouTube transcript. Summarise in 250 words or less and do not talk of the sponsors or anything unrelated to the main topic. Also, do not introduce what the summary is about.\n" + transcript
            )
            # print("summary===========",summary)
            
            summary_text = summary._result.candidates[0].content.parts[0].text
            # print("summary_text", summary_text)
            
            questions = get_questions_from_transcript(transcript, chapter.name)
            # print("question view file", questions)
            
            chapter.videoId = video_id
            chapter.summary = summary_text
            chapter.save()

            if 'parts' in questions:
                for question in questions['parts']:
                    if 'text' in question:
                        question_dict = ast.literal_eval(question['text'])
                        options = [question_dict['answer'], question_dict['option1'], question_dict['option2'], question_dict['option3']]
                        options.sort(key=lambda _: random.random())
                        Question.objects.create(
                            question=question_dict['question'],
                            answer=question_dict['answer'],
                            options=options,
                            chapter=chapter
                        )
                # chapter.videoId = video_id
                # chapter.summary = summary_text
                # chapter.save()
            return Response({"success": True, "videoId": video_id, "transcript": transcript, "summary": summary_text}, status=status.HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



