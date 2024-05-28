from rest_framework import serializers
from .models import UserAccount
        
class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ['id', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser', 'credits', 'image']
        read_only_fields = ['email','is_active', 'is_staff', 'is_superuser', 'credits']

    def update(self, instance, validated_data):
        validated_data.pop('email', None)
        validated_data.pop('is_active', None)
        validated_data.pop('is_staff', None)
        validated_data.pop('is_superuser', None)
        validated_data.pop('credits', None)
        return super().update(instance, validated_data)