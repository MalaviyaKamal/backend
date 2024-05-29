from rest_framework import serializers
from .models import Chats

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chats
        fields = ['id', 'pdf_name', 'pdf_url', 'created_at','file_key']
