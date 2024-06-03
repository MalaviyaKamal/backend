# # # urls.py
# from django.urls import path
# from .views import UploadToS3,AskQuestionView

# urlpatterns = [
#     path('upload/', UploadToS3.as_view(), name='upload_to_s3'),
# #     # path('createchat/',CreateChat.as_view(),name='create_chat'),
#     path('ask/<int:chat_id>/', AskQuestionView.as_view(), name='ask-question'),
# ]
# # # urls.py
from django.urls import path
from .views import  UploadPDF,ProcessPDF,GetAllPDFs

urlpatterns = [
    path('upload/', UploadPDF.as_view(), name='upload_to_s3'),
#     # path('createchat/',CreateChat.as_view(),name='create_chat'),
    path('ask/<int:chatId>/', ProcessPDF.as_view(), name='ask-question'),
    path('chat/',GetAllPDFs.as_view(),name="pdf-name")
    
]
