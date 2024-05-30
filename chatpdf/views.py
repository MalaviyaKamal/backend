import time
import boto3
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import Chats
from .serializers import ChatSerializer
import os
import hashlib
from pinecone import Pinecone
from .s3_server import download_from_s3
from .embeddings import get_embeddings
from langchain_community.document_loaders import PyPDFLoader
from .utils import convert_to_ascii
from langchain.docstore.document import Document
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

def get_pinecone_client():
    return Pinecone(
        environment="us-west1-gcp",
        api_key="4a574746-607d-41cd-8a8e-51f9483cf45c"
    )
class CreateChat(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            # Call load_s3_into_pinecone after saving chat information
            try:
        # 1. Obtain the PDF -> Download and read from PDF
        print("Downloading from S3 into file system")
        file_name = await download_from_s3(file_key)
        if not file_name:
            raise Exception("Could not download from S3")

        print("Loading PDF into memory:", file_name)
        loader = PDFLoader(file_name)
        pages = await loader.load()

        # 2. Split and segment the PDF
        documents = await prepare_documents(pages)

        # 3. Vectorize and embed individual documents
        vectors = []
        for doc in documents:
            vectors.extend(await embed_document(doc))

        # 4. Upload to Pinecone
        client = get_pinecone_client()
        pinecone_index = await client.index("chat-pdf")
        namespace = pinecone_index.namespace(convert_to_ascii(file_key))

        print("Inserting vectors into Pinecone")
        await namespace.upsert(vectors)

        return documents[0]
    except Exception as e:
        print("Error:", e)
        raise

async def embed_document(doc):
    try:
        embeddings = await get_embeddings(doc.page_content)
        hash_val = hashlib.md5(doc.page_content.encode()).hexdigest()

        return PineconeRecord(
            id=hash_val,
            values=embeddings,
            metadata={
                'text': doc.metadata['text'],
                'pageNumber': doc.metadata['pageNumber']
            }
        )
    except Exception as e:
        print("Error embedding document:", e)
        raise

async def prepare_documents(pages):
    documents = []
    for page in pages:
        page_content = page['pageContent'].replace("\n", "")
        metadata = {
            'pageNumber': page['metadata']['loc']['pageNumber'],
            'text': truncate_string_by_bytes(page_content, 36000)
        }
        # Split the docs
        splitter = RecursiveCharacterTextSplitter()
        docs = await splitter.split_documents([
            Document(page_content=page_content, metadata=metadata)
        ])
        documents.extend(docs)
    return documents

def truncate_string_by_bytes(s, bytes):
    enc = s.encode('utf-8')
    return enc[:bytes].decode('utf-8', 'ignore')
            
            return Response({'chat_id': serializer.data['id'], "message": "successfully chat created"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
