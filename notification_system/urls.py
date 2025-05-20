from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notifications'),
    path('read/<int:pk>/', views.mark_as_read, name='mark_as_read'),
    path('read_all/', views.mark_all_as_read, name='mark_all_as_read'),
    path('new/', views.new_notification, name='new_notification'),
] 