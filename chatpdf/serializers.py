from rest_framework import serializers
from .models import Messages,PDFDocument

# class ChatSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Chats
#         fields = ['id', 'pdf_name', 'pdf_url', 'created_at','file_key']

class PDFDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDFDocument
        fields = ['id', 'file', 'pdf_name','uploaded_at', 'user']

class MessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Messages
        fields = ['chat', 'content', 'role']