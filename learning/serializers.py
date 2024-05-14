from rest_framework import serializers
from .models import Course, Unit, Chapter

class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'name', 'youtubeSearchQuery', 'videoId', 'summary']

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