from django.contrib import admin
from .models import Chats,Messages
# Register your models here.
@admin.register(Chats)
class ChatsAdmin(admin.ModelAdmin):
    list_display = ('id','pdf_name','pdf_url','file_key','created_at','user')
    

@admin.register(Messages)
class MessagesAdmin(admin.ModelAdmin):
    list_display = ('id','content','role','created_at','chat',)