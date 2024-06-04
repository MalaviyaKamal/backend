# urls.py
from django.urls import path
from .views import CreateChapterAPIView,CourseListAPIView,CourseRetrieveAPIView,ChapterInfoAPIView

urlpatterns = [
    path('createchapter/', CreateChapterAPIView.as_view(), name='create_chapter'),
    path('courseget/', CourseListAPIView.as_view(), name='getall course'),
    path('courseget/<int:pk>/', CourseRetrieveAPIView.as_view(), name='get_course'),
    path('chaptergetinfo/', ChapterInfoAPIView.as_view(), name='chapter info'),
]
