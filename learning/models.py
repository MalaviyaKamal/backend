from django.db import models
from users.models import UserAccount 
from django.conf import settings

# Create your models here.
class  Course(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    image = models.CharField(max_length=255)
    user =  models.ForeignKey(UserAccount, on_delete=models.CASCADE)

    def _str_(self):
        return self.name

class Unit(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='units')
  
    def __str__(self):
        return self.name

class Chapter(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    youtubeSearchQuery = models.CharField(max_length=255)
    videoId = models.CharField(max_length=300000,blank=True, null=True)
    summary = models.CharField(max_length=3000, blank=True, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='chapter')

class Question(models.Model):
    id = models.AutoField(primary_key=True)
    question = models.CharField(max_length=3000)
    answer = models.CharField(max_length=3000)
    options = models.CharField(max_length=3000)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)