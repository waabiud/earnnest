from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_index, name='index'),
    path('unread/', views.unread_count, name='unread_count'),
]
