from django.contrib import admin
from .models import Chats,Messages
# Register your models here.
@admin.register(Chats)
class ChatsAdmin(admin.ModelAdmin):
    list_display = ('id','pdf_name','pdf_url','created_at','user','file_key')
    

@admin.register(Messages)
class MessagesAdmin(admin.ModelAdmin):
    list_display = ('id','content','role','created_at','chat',)