from django.db import models
from users.models import UserAccount 
from django.conf import settings

# class Chats(models.Model):
#     id = models.AutoField(primary_key=True)
#     pdf_name = models.CharField(max_length=255)
#     pdf_url = models.CharField(max_length=1000)
#     created_at = models.DateTimeField(auto_now_add=True)
#     user =  models.ForeignKey(UserAccount, on_delete=models.CASCADE)
#     file_key = models.CharField(max_length=255)
    
class PDFDocument(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to='pdfs/')
    pdf_name = models.CharField(max_length=255, blank=False, null=False, default='pdf')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    
class Messages(models.Model):
    id = models.AutoField(primary_key=True)
    chat = models.ForeignKey(PDFDocument, on_delete=models.CASCADE)
    content = models.CharField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(choices=[('system', 'system'), ('user', 'user')], max_length=20)

