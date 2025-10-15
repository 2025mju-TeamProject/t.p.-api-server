from django.urls import path
from . import views

urlpatterns = [
    path('<int:other_user_id>/', views.chat_room, name='chat_room'),
]