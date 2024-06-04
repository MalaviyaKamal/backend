
from django.urls import path
from .views import  UploadPDF,ProcessPDF,GetAllPDFs,ChatMessagesAPIView

urlpatterns = [
    path('upload/', UploadPDF.as_view(), name='upload_to_s3'),
    path('ask/<int:chatId>/', ProcessPDF.as_view(), name='ask-question'),
    path('chat/',GetAllPDFs.as_view(),name="pdf-name"),
    path('messages/<int:chat_id>/', ChatMessagesAPIView.as_view(), name='chat-messages'),

    
]
