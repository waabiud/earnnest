from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.game_index, name='index'),
    path('play/', views.place_guess, name='play'),
    path('pending/', views.game_pending, name='pending'),
    path('history/', views.game_history, name='history'),
]
