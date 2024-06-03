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
from .models import PDFDocument
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PDFDocumentSerializer,MessagesSerializer

class UploadPDF(APIView):
    def post(self, request):
        if request.FILES.get('file'):
            file = request.FILES['file']
            pdf_name = request.data.get('pdf_name', file.name)
            print("pdf_name",pdf_name)
            user = request.user
            serializer = PDFDocumentSerializer(data={'file': file, 'pdf_name': pdf_name, 'user': user.id})
            
            if serializer.is_valid():
                serializer.save()
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
class ProcessPDF(APIView):
    def post(self, request, chatId):
        print("pdf_id::", chatId)
        try:
            pdf_document = get_object_or_404(PDFDocument, id=chatId)
        except:
            return JsonResponse({'error': 'Invalid PDF ID'}, status=404)

        # Check if the user making the request has access to the PDF document
        if pdf_document.user != request.user:
            return JsonResponse({'error': 'You do not have permission to access this document.'}, status=403)

        # Proceed with processing the PDF document
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
                docs = knowledge_base.similarity_search(question)
                llm = HuggingFaceHub(repo_id="google/flan-t5-large", model_kwargs={"temperature": 5, "max_length": 64})
                chain = load_qa_chain(llm, chain_type="stuff")
                answer = chain.run(input_documents=docs, question=question)
                answer_serializer = MessagesSerializer(data={'chat': pdf_document.id, 'content': answer, 'role': 'system'})
                if answer_serializer.is_valid():
                    answer_serializer.save()
                return JsonResponse({'response': answer})

        return JsonResponse({'error': 'No question provided'}, status=400)