# urls.py
from django.urls import path
from .views import UploadToS3,CreateChat

urlpatterns = [
    path('upload/', UploadToS3.as_view(), name='upload_to_s3'),
    path('createchat/',CreateChat.as_view(),name='create_chat'),

]
