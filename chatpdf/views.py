# import os
# import boto3
# import time
# from django.conf import settings
# from rest_framework.views import APIView
# from django.http import JsonResponse
# from rest_framework.response import Response
# from django.shortcuts import get_object_or_404
# from PyPDF2 import PdfReader
# from langchain.text_splitter import CharacterTextSplitter
# from langchain.embeddings.huggingface import HuggingFaceEmbeddings
# from langchain.vectorstores import FAISS
# from langchain.chains.question_answering import load_qa_chain
# from langchain import HuggingFaceHub
# from .models import Chats
# from rest_framework.parsers import MultiPartParser
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status
# from io import BytesIO
# from .serializers import serializers
# from .s3_server import download_from_s3
# class UploadToS3(APIView):
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         file = request.FILES.get('file')
#         if not file:
#             return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

#         s3 = boto3.client(
#             's3',
#             region_name=settings.AWS_S3_REGION_NAME,
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
#         )

#         file_key = 'uploads/' + str(int(time.time())) + file.name.replace(' ', '-')

#         try:
#             s3.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, file_key)
#             pdf_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.ap-southeast-2.amazonaws.com/{file_key}"
#             return Response({'file_key': file_key, 'pdf_name': file.name,'pdf_url': pdf_url}, status=status.HTTP_201_CREATED)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class AskQuestionView(APIView):
#     def post(self, request, chat_id):
#         user = request.user
#         chat = get_object_or_404(Chats, id=chat_id, user=user)
#         question = request.data.get('question')
#         print("ques",question)
#         file_key = request.data.get('file_key')
#         file_name = download_from_s3(file_key)
#         # Download PDF from S3
#         print("file_name",file_name)
#         serializer = ChatSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
     
#         if not file_name:
#             raise Exception("Could not download from S3")

#         # loader = PyPDFLoader(file_name)
#         #  pages = loader.load()
#         # Process PDF
#         pdf_reader = PdfReader(file_name)
#         file("pdf_reader",pdf_reader)
#         text = ""
#         for page in pdf_reader.pages:
#             text += page.extract_text()

#         # Split into chunks
#         text_splitter = CharacterTextSplitter(
#             separator="\n",
#             chunk_size=1000,
#             chunk_overlap=200,
#             length_function=len
#         )
#         chunks = text_splitter.split_text(text)

#         # Create embeddings and knowledge base
#         embeddings = HuggingFaceEmbeddings()
#         knowledge_base = FAISS.from_texts(chunks, embeddings)

#         # Answer question
#         docs = knowledge_base.similarity_search(question)
#         llm = HuggingFaceHub(repo_id="google/flan-t5-large", model_kwargs={"temperature": 5, "max_length": 64})
#         chain = load_qa_chain(llm, chain_type="stuff")
#         response = chain.run(input_documents=docs, question=question)

#         return JsonResponse({'answer': response,"message":"success created"})


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
from .serializers import PDFDocumentSerializer

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
# print(os.environ["HUGGINGFACEHUB_API_TOKEN"])
class ProcessPDF(APIView):
    def get(self, request, pdf_id):
        print("pdf_id::", pdf_id)
        try:
            pdf_document = get_object_or_404(PDFDocument, id=pdf_id)
        except:
            return JsonResponse({'error': 'Invalid PDF ID'}, status=404)
        
        # Check if the logged-in user is the owner of the PDF document
        if pdf_document.user != request.user:
            return JsonResponse({'error': 'You do not have permission to access this document.'}, status=403)

        file_path = pdf_document.file.path
        print("file_path::", file_path)
        if file_path:
            pdf_reader = PdfReader(file_path)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            print("pdf_reader", pdf_reader)

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
                docs = knowledge_base.similarity_search(question)
                llm = HuggingFaceHub(repo_id="google/flan-t5-large", model_kwargs={"temperature": 5, "max_length": 64})
                chain = load_qa_chain(llm, chain_type="stuff")
                answer = chain.run(input_documents=docs, question=question)
                print("answer",answer)
                return JsonResponse({'response': answer})

        return JsonResponse({'error': 'No question provided'}, status=400)



# import time
# import boto3
# import logging
# import os
# import hashlib
# import re
# from .models import Chats
# from pinecone import Pinecone, ServerlessSpec
# from django.conf import settings
# from rest_framework import status
# from .utils import convert_to_ascii
# from .serializers import ChatSerializer
# from .s3_server import download_from_s3
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser
# from rest_framework.permissions import IsAuthenticated
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from .embeddings import get_embeddings

# class UploadToS3(APIView):
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         file = request.FILES.get('file')
#         if not file:
#             return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

#         s3 = boto3.client(
#             's3',
#             region_name=settings.AWS_S3_REGION_NAME,
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
#         )

#         file_key = 'uploads/' + str(int(time.time())) + file.name.replace(' ', '-')

#         try:
#             s3.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, file_key)
#             pdf_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.ap-southeast-2.amazonaws.com/{file_key}"
#             return Response({'file_key': file_key, 'pdf_name': file.name,'pdf_url': pdf_url}, status=status.HTTP_201_CREATED)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# # Configure logging
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)
# os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"

# # Initialize Pinecone client
# pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"), environment="us-west1-gcp")

# # Create index if it doesn't exist
# index_name = "chat-pdf"

# if index_name not in pc.list_indexes().names():
#     pc.create_index(
#         name=index_name,
#         dimension=19999 ,  # Specify the dimension based on your embeddings
#         metric="cosine",
#         spec=ServerlessSpec(
#             cloud='aws',
#             region='us-east-1'
#         )
#     )


# class CreateChat(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = ChatSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             try:
#                 file_key = request.data.get('file_key')
#                 file_name = download_from_s3(file_key)
#                 if not file_name:
#                     raise Exception("Could not download from S3")

#                 loader = PyPDFLoader(file_name)
#                 pages = loader.load()

#                 documents = prepare_documents(pages)

#                 vectors = []
#                 for doc in documents:
#                     vectors.extend(embed_document(doc))
#                 print("this vector data",vectors)
#                 index = pc.Index(index_name)

#                 index.upsert(
#                     vectors=vectors,
#                     namespace=convert_to_ascii(file_key)
#                 )

#                 return Response({'chat_id': serializer.data['id'], "message": "Chat created successfully"},
#                                 status=status.HTTP_200_OK)
#             except Exception as e:
#                 logger.error("Error creating chat: %s", str(e))
#                 return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         else:
#             logger.error("Invalid serializer data: %s", serializer.errors)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# def embed_document(doc):
#     try:
#         # Initialize the embeddings model
#         embeddings_model = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
#         # Generate embeddings for the document content
#         embeddings = embeddings_model.embed_documents(doc['page_content'])

#         # Flatten the list of lists
#         flattened_embeddings = [item for sublist in embeddings for item in sublist]
#         # print("Flattened embeddings:", flattened_embeddings)
#         # Create a hash for the document ID
#         hash_val = hashlib.md5(doc['page_content'].encode()).hexdigest()
#         return [{
#             'id': hash_val,
#             'values': flattened_embeddings,
#             'metadata': {
#                 'text': doc['metadata']['text'],
#                 'pageNumber': doc['metadata']['pageNumber']
#             }
#         }]
#     except Exception as e:
#         logger.error("Error embedding document: %s", str(e))
#         raise


# def prepare_documents(pages):
#     documents = []
#     logger.debug("Preparing documents from pages")
#     try:
#         for page in pages:
#             page_content = clean_text(page.page_content)  
#             print("page_content",page_content)
#             metadata = {
#                 'pageNumber': page.metadata.get('page', 'N/A'),  
#                 'text': truncate_string_by_bytes(page_content, 36000)
#             }
#             documents.append({
#                 'page_content': page_content,
#                 'metadata': metadata
#             })
#         logger.debug("Documents prepared: %s", documents)
#     except Exception as e:
#         logger.error("Error preparing documents: %s", str(e))
#         raise
#     return documents


# def clean_text(text):
#     return re.sub('/\n/g', ' ', text).strip()


# def truncate_string_by_bytes(s, bytes):
#     enc = s.encode('utf-8')
#     return enc[:bytes].decode('utf-8', 'ignore')


# def convert_to_ascii(s):
#     return re.sub(r'[^\x00-\x7F]+', '', s)
# class CreateChat(APIView):
#     def post(self, request):
#         if not request.user.is_authenticated:
#             return Response({'error': 'unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
#         serializer = ChatSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response({'chat_id': serializer.data['id'],"message":"successfully chat created"}, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
