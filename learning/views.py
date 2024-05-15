

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import google.generativeai as genai
from .models import Course, Unit, Chapter,Question
from .gpt import generate_chapters,model
from django.shortcuts import get_object_or_404
from .serializers import CourseSerializer,ChapterSerializer
from rest_framework.generics import ListAPIView
from django.db.models import Prefetch
from django.core.exceptions import ObjectDoesNotExist
from .youtube import search_youtube, get_transcript, get_questions_from_transcript
import traceback
import json
import random
import ast
class CreateChapterAPIView(APIView):
    def post(self, request):
        title = request.data.get('title')
        units = request.data.get('units', [])
        user_id = request.user.id  

        if not title or not units:
            return Response({"error": "Title and units are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            response_data = generate_chapters(title, units, user_id)
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CourseListAPIView(ListAPIView):
    # queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
    # def get_queryset(self):
    #     all_course  = Course.objects.all().prefetch_related(
    #         Prefetch('units', queryset=Unit.objects.all().prefetch_related('chapter'))
    #     )
    #     print(all_course.__dict__)
    #     return all_course
    
    # def get_queryset(self):
    #     user = self.request.user
    #     all_course  = Course.objects.filter(user=user).prefetch_related(
    #     Prefetch('units', queryset=Unit.objects.all().prefetch_related('chapter'))
    #     )
    #     print(all_course.__dict__)
    #     return all_course
    def get_queryset(self):
        try:
            user = self.request.user
            all_course = Course.objects.filter(user=user).prefetch_related(
                Prefetch('units', queryset=Unit.objects.all().prefetch_related('chapter'))
            )
            print(all_course.__dict__)
            return all_course
        except ObjectDoesNotExist:
            raise Http404("No Course matches the given query.")
        except Exception as e:
            raise
    
    
class CourseRetrieveAPIView(ListAPIView):
    serializer_class = CourseSerializer
    
    def list(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
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
            print("chapter title", chapter.youtubeSearchQuery)
            video_id = search_youtube(chapter.youtubeSearchQuery)
            print("video id", video_id)
            if not video_id:
                return Response({"success": False, "error": "Video not found"}, status=status.HTTP_404_NOT_FOUND)
            
            transcript = get_transcript(video_id)
            print("transcript_view:", transcript)
            
            if not transcript:
                chapter.videoId = video_id
                chapter.save()
                
                return Response({"success": True, "videoId": video_id, "error": "Transcript not found"}, status=status.HTTP_200_OK)
            
            summary = model.generate_content(
                "You are an AI capable of summarising a youtube transcript. Summarise in 250 words or less and do not talk of the sponsors or anything unrelated to the main topic. Also, do not introduce what the summary is about.\n" + transcript
            )
            summary_text = summary._result.candidates[0].content.parts[0].text
            print("summary_text", summary_text)
            
            questions = get_questions_from_transcript(transcript, chapter.name)
            print("question view file", questions)
            
            if 'parts' in questions:
                for question in questions['parts']:
                    if 'text' in question:
                        question_dict = ast.literal_eval(question['text'])
                        options = [question_dict['answer'], question_dict['option1'], question_dict['option2'], question_dict['option3']]
                        options.sort(key=lambda _: random.random())
                        chapter_instance = get_object_or_404(Chapter, id=chapter_id)
                        Question.objects.create(
                            question=question_dict['question'],
                            answer=question_dict['answer'],
                            options=options,
                            chapter=chapter_instance
                        )
            
            chapter.videoId = video_id
            chapter.summary = summary_text
            chapter.save()

            return Response({"success": True, "videoId": video_id, "transcript": transcript, "summary": summary_text}, status=status.HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
