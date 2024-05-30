from rest_framework import serializers
from .models import Chats,Messages

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chats
        fields = ['id', 'pdf_name', 'pdf_url', 'created_at','file_key']

class MessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Messages
        fields = '__all__'