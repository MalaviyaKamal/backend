from django.contrib import admin
from .models import UserAccount
# Register your models here.
@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name','last_name','is_active','is_staff','is_superuser','credits','image')