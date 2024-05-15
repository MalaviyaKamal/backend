from rest_framework import serializers
from .models import Course, Unit, Chapter,Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question', 'answer', 'options', 'chapter']

class ChapterSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(many=True,read_only=True)
    class Meta:
        model = Chapter
        fields = ['id', 'name', 'youtubeSearchQuery', 'videoId', 'summary','question']

class UnitSerializer(serializers.ModelSerializer):
    chapter = ChapterSerializer(many=True, read_only=True)


    class Meta:
        model = Unit
        fields = ['id', 'name', 'chapter']

class CourseSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'image', 'user', 'units']
        
