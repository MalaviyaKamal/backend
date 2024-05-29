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



class CreateChat(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'chat_id': serializer.data['id']}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)