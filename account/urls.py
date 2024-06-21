from django.urls import path
from .views import UserCreateView, SubjectView, RoomView


urlpatterns = [
    path('create/', UserCreateView.as_view(), name='create'),
    path('subject/', SubjectView.as_view(), name='subject'),
    path('room/', RoomView.as_view(), name='room'),
]