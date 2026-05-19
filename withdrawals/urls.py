from django.urls import path
from . import views

app_name = 'withdrawals'

urlpatterns = [
    path('', views.withdrawal_index, name='index'),
    path('request/', views.request_withdrawal, name='request'),
    path('history/', views.withdrawal_history, name='history'),
]
