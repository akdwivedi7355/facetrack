from django.contrib import admin
from django.urls import path, include
from myapp import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),  # Use 'myapp' here
    path('video_feed/', views.video_feed, name='video_feed'),
    path('visitor_list/', views.visitor_list, name='visitor_list'),
    path('visitor_details/<int:visitor_id>/', views.visitor_details, name='visitor_details'),

]
