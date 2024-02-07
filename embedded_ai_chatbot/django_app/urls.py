from django.urls import path
from embedded_ai_chatbot import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.chat_with_user, name='chat_with_user'),
]