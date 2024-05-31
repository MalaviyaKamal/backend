import time
import boto3
import logging
import os
import hashlib
import re
from .models import Chats
from pinecone import Pinecone
from django.conf import settings
from rest_framework import status
from .utils import convert_to_ascii
from .embeddings import get_embeddings
from .serializers import ChatSerializer
from .s3_server import download_from_s3
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from langchain_community.document_loaders import PyPDFLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter

class UploadToS3(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        s3 = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        file_key = 'uploads/' + str(int(time.time())) + file.name.replace(' ', '-')

        try:
            s3.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, file_key)
            pdf_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.ap-southeast-2.amazonaws.com/{file_key}"
            return Response({'file_key': file_key, 'pdf_name': file.name,'pdf_url': pdf_url}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"

def get_pinecone_client():
    return Pinecone(
        environment="us-east-1-aws",
        api_key="4a574746-607d-41cd-8a8e-51f9483cf45c"
    )

class CreateChat(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            try:
                file_key = request.data.get('file_key')
                file_name = download_from_s3(file_key)
                if not file_name:
                    raise Exception("Could not download from S3")

                loader = PyPDFLoader(file_name)
                pages = loader.load()

                documents = prepare_documents(pages)

                vectors = []
                for doc in documents:
                    vectors.extend(embed_document(doc))

                client = get_pinecone_client()
                pinecone_index = client.index("chat-pdf")
                namespace = pinecone_index.namespace(convert_to_ascii(file_key))

                namespace.upsert(vectors)

                return Response({'chat_id': serializer.data['id'], "message": "Chat created successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error("Error creating chat: %s", str(e))
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.error("Invalid serializer data: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def embed_document(doc):
    try:
        # Initialize the embeddings model
        embeddings_model = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        prine("kmalamamk")
        # Generate embeddings for the document content
        embeddings = embeddings_model.embed_documents(doc['page_content'])
        
        print("embeddings",embeddings)
        # Create a hash for the document ID
        hash_val = hashlib.md5(doc['page_content'].encode()).hexdigest()

        return [{
            'id': hash_val,
            'values': embeddings,
            'metadata': {
                'text': doc['metadata']['text'],
                'pageNumber': doc['metadata']['pageNumber']
            }
        }]
    except Exception as e:
        logger.error("Error embedding document: %s", str(e))
        raise

def prepare_documents(pages):
    documents = []
    logger.debug("Preparing documents from pages")
    try:
        for page in pages:
            page_content = clean_text(page.page_content)  # Access page content directly
            metadata = {
                'pageNumber': page.metadata.get('page', 'N/A'),  # Safely access metadata
                'text': truncate_string_by_bytes(page_content, 36000)
            }
            documents.append({
                'page_content': page_content,
                'metadata': metadata
            })
        logger.debug("Documents prepared: %s", documents)
    except Exception as e:
        logger.error("Error preparing documents: %s", str(e))
        raise
    return documents

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def truncate_string_by_bytes(s, bytes):
    enc = s.encode('utf-8')
    return enc[:bytes].decode('utf-8', 'ignore')

def convert_to_ascii(s):
    return re.sub(r'[^\x00-\x7F]+', '', s)
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
        
        
        
        
# import time
# import boto3
# import hashlib
# import logging
# from rest_framework.views import APIView
# from django.conf import settings
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from .models import Chats
# from .serializers import ChatSerializer
# from .s3_server import download_from_s3
# from .embeddings import get_embeddings
# from .pinecone import upsert_vectors
# from .utils import truncate_string_by_bytes, convert_to_ascii
# from langchain_community.document_loaders import PyPDFLoader
# import langchain
# import json
# import nltk
# from nltk.tokenize import sent_tokenize

# logger = logging.getLogger(__name__)
# nltk.download('punkt')

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

# class CreateChat(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         logger.debug("Starting CreateChat POST request")
        
#         if not request.user.is_authenticated:
#             logger.debug("User not authenticated")
#             return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
#         file_key = request.data.get('file_key')
#         file_name = request.data.get('pdf_name')
#         print(f"Received request with file_key: {file_key}, file_name: {file_name}")

#         if not file_key or not file_name:
#             logger.debug("Missing file_key or file_name")
#             return Response({'error': 'file_key and file_name are required'}, status=status.HTTP_400_BAD_REQUEST)

#         # Download file from S3
#         try:
#             print("Downloading file from S3")
#             file_path = download_from_s3(file_key)
#             if not file_path:
#                 raise Exception("File path is None after download")
#         except Exception as e:
#             logger.error(f"Error downloading file from S3: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         # Load PDF into memory
#         try:
#             print("Loading PDF pages")
#             print("file_path", file_path)
#             loader = PyPDFLoader(file_path)
#             pages = loader.load()
#             print("load success", pages)
#         except Exception as e:
#             logger.error(f"Error loading PDF pages: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#         documents = []
#         try:
#             print("hello dcbhsgc")
#             # Use NLTK for sentence tokenization
#             for page in pages:
#                 page_content = page.page_content.replace('\n', '')
#                 sentences = sent_tokenize(page_content)
#                 for sentence in sentences:
#                     documents.append(sentence)
#             print("documents=================", documents)
#         except Exception as e:
#             logger.error(f"Error splitting and segmenting PDF: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#         # Vectorize and embed individual documents
#         vectors = []
#         try:
#             for doc in documents:
#                 embeddings = get_embeddings(doc) 
#                 print("embeddings================================",embeddings)# Assuming get_embeddings function is defined elsewhere
#                 hash_val = hashlib.md5(doc.encode()).hexdigest()
#                 vector = {'id': hash_val, 'values': embeddings, 'metadata': {'text': doc}}
#                 vectors.append(vector)
#         except Exception as e:
#             logger.error(f"Error vectorizing and embedding documents: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#         # Upload vectors to Pinecone
#         try:
#             logger.debug("Uploading vectors to Pinecone")
#             upsert_vectors(vectors)  # Assuming upsert_vectors function is defined elsewhere
#         except Exception as e:
#             logger.error(f"Error uploading vectors to Pinecone: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         # Save chat information to database
#         try:
#             serializer = ChatSerializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.save(user=request.user)
#                 return Response({'chat_id': serializer.data['id'], "message": "successfully chat created"}, status=status.HTTP_200_OK)
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error saving chat to database: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



















# import time
# import boto3
# import hashlib
# import langchain
# from rest_framework.views import APIView
# from django.conf import settings
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from .models import Chats
# from .serializers import ChatSerializer
# from .s3_server import download_from_s3
# from .embeddings import get_embeddings
# from .pinecone import upsert_vectors
# from .utils import truncate_string_by_bytes, convert_to_ascii
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# import logging
# from pinecone import 

# logger = logging.getLogger(__name__)

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

# class CreateChat(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         logger.debug("Starting CreateChat POST request")
        
#         if not request.user.is_authenticated:
#             logger.debug("User not authenticated")
#             return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
#         file_key = request.data.get('file_key')
#         file_name = request.data.get('pdf_name')
#         print(f"Received request with file_key: {file_key}, file_name: {file_name}")

#         if not file_key or not file_name:
#             logger.debug("Missing file_key or file_name")
#             return Response({'error': 'file_key and file_name are required'}, status=status.HTTP_400_BAD_REQUEST)

#         # Download file from S3
#         try:
#             print("Downloading file from S3")
#             file_path = download_from_s3(file_key)
#             if not file_path:
#                 raise Exception("File path is None after download")
#         except Exception as e:
#             logger.error(f"Error downloading file from S3: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         # Load PDF into memory
#         try:
#             print("Loading PDF pages")
#             print("file_path",file_path)
#             loader = PyPDFLoader(file_path)
#             pages = loader.load()
#             print("load success",pages)
#         except Exception as e:
#             logger.error(f"Error loading PDF pages: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#         documents = []
#         try:
#             print("hello dcbhsgc")
#             splitter = RecursiveCharacterTextSplitter()
#             for page in pages:
#                 page_content = page.page_content.replace('\n', '')
#                 doc = Document(page_content=page_content, metadata={'page_number': page.metadata['loc']['page_number'], 'text': truncate_string_by_bytes(page_content, 36000)})
                
#                 documents.append(doc)
#             print("docu",doc)   
#         except Exception as e:
#             logger.error(f"Error splitting and segmenting PDF: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#         # Vectorize and embed individual documents
#         vectors = []
#         try:
#             for doc in documents:
#                 embeddings = get_embeddings(doc.page_content)
#                 hash_val = hashlib.md5(doc.page_content.encode()).hexdigest()
#                 vector = {'id': hash_val, 'values': embeddings, 'metadata': {'text': doc.metadata['text'], 'page_number': doc.metadata['page_number']}}
#                 vectors.append(vector)
#         except Exception as e:
#             logger.error(f"Error vectorizing and embedding documents: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#         # Upload vectors to Pinecone
#         try:
#             logger.debug("Uploading vectors to Pinecone")
#             upsert_vectors(vectors)
#         except Exception as e:
#             logger.error(f"Error uploading vectors to Pinecone: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         # Save chat information to database
#         try:
#             serializer = ChatSerializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.save(user=request.user)
#                 return Response({'chat_id': serializer.data['id'], "message": "successfully chat created"}, status=status.HTTP_200_OK)
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error saving chat to database: {e}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
