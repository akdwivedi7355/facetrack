from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('visitor_list/', views.visitor_list, name='visitor_list'),
    path('visitor_details/<int:visitor_id>/', views.visitor_details, name='visitor_details'),


]
