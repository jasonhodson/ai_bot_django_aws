from django.contrib import admin
from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('django_app.urls')),
    path('delete_files/', views.delete_files, name='delete_files'),
]