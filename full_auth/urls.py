from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('djoser.urls')),
    path('api/', include('users.urls')),
    path('api/course/', include('learning.urls')),
    path('api/stripe/',include('subscription.urls')),
    path('api/chatpdf/',include('chatpdf.urls'))

]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
