import os
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from django.contrib.auth.models import User
from langchain.chains.question_answering import load_qa_chain
from langchain import HuggingFaceHub
from .models import PDFDocument,Messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PDFDocumentSerializer,MessagesSerializer
import google.generativeai as genai
from rest_framework import generics
from subscription.models import UserSubscription

class UploadPDF(APIView):
    def post(self, request):
        if request.FILES.get('file'):
            file = request.FILES['file']
            pdf_name = request.data.get('pdf_name', file.name)
            print("pdf_name",pdf_name)
            user = request.user

            # Check user's subscription status
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
                return Response({"error": "No credits remaining"})

            serializer = PDFDocumentSerializer(data={'file': file, 'pdf_name': pdf_name, 'user': user.id})
            
            if serializer.is_valid():
                serializer.save()

                if not has_active_subscription:
                    user.credits -= 1
                    user.save()

                return Response({'id': serializer.data['id'], "message": "successfully pdf uploaded"}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)


class GetAllPDFs(APIView):
    def get(self, request):
        try:
            user = request.user
            pdf_documents = PDFDocument.objects.filter(user=user)
            serializer = PDFDocumentSerializer(pdf_documents, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
print(os.environ["HUGGINGFACEHUB_API_TOKEN"])


genai.configure(api_key="AIzaSyD3fNrZOMYf3cvqcUDmEWfS0V-QgI_dlAs")
model = genai.GenerativeModel('gemini-pro')

def clean_text(text):
    """Remove special formatting from text."""
    clean_text = text.replace('\n', ' ').replace('*', '').replace('**', '')
    return clean_text
class ProcessPDF(APIView):
    def post(self, request, chatId):
        print("pdf_id::", chatId)
        try:
            pdf_document = get_object_or_404(PDFDocument, id=chatId)
        except:
            return JsonResponse({'error': 'Invalid PDF ID'}, status=404)

        if pdf_document.user != request.user:
            return JsonResponse({'error': 'You do not have permission to access this document.'}, status=403)

        file_path = pdf_document.file.path
        if file_path is not None:
            pdf_reader = PdfReader(file_path)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()

            text_splitter = CharacterTextSplitter(
                separator="\n",
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            chunks = text_splitter.split_text(text)

            embeddings = HuggingFaceEmbeddings()
            knowledge_base = FAISS.from_texts(chunks, embeddings)

            question = request.data.get('question')
            if question:
                question_serializer = MessagesSerializer(data={'chat': pdf_document.id, 'content': question, 'role': 'user'})
                if question_serializer.is_valid():
                    question_serializer.save()

                try:
                    docs = knowledge_base.similarity_search(question)
                    if docs:
                        llm = HuggingFaceHub(repo_id="google/flan-t5-large", model_kwargs={"temperature": 5, "max_length": 64})
                        chain = load_qa_chain(llm, chain_type="stuff")
                        answer = chain.run(input_documents=docs, question=question)

                        # Check if the answer is inadequate
                        if "not enough information" in answer.lower():
                            raise ValueError("Inadequate response from the document")
                    else:
                        # If no relevant documents are found, raise an exception
                        raise ValueError("No relevant documents found")

                    answer_serializer = MessagesSerializer(data={'chat': pdf_document.id, 'content': answer, 'role': 'system'})
                    if answer_serializer.is_valid():
                        answer_serializer.save()
                    return JsonResponse({'response': answer})

                except ValueError as e:
                    # Call Gemini AI if the response from the document is inadequate or no documents found
                    if 'Inadequate response from the document' in str(e) or 'No relevant documents found' in str(e):
                        prompt = ( f"Please provide an answer to the following question: {question}")
                        gemini_response = model.generate_content(prompt)
                        print("answer",gemini_response)
                        print(gemini_response.candidates[0].content.parts[0].text)
                        gemini_text = gemini_response.candidates[0].content.parts[0].text
                        gemini_answer = clean_text(gemini_text)

                        answer_serializer = MessagesSerializer(data={'chat': pdf_document.id, 'content': gemini_answer, 'role': 'system'})
                        if answer_serializer.is_valid():
                            answer_serializer.save()
                        return JsonResponse({'response': gemini_answer})
                    else:
                        return JsonResponse({'error': str(e)}, status=500)

                except Exception as e:
                    traceback.print_exc()
                    return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'error': 'No question provided'}, status=400)
    
class ChatMessagesAPIView(generics.ListAPIView):
    serializer_class = MessagesSerializer

    def get_queryset(self):
        chat_id = self.kwargs.get('chat_id')
        user = self.request.user
        try:
            pdf_document = PDFDocument.objects.get(id=chat_id, user=user)
            return Messages.objects.filter(chat_id=chat_id)
        except PDFDocument.DoesNotExist:
            return []

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset:
            return Response({'error': 'No chat found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)