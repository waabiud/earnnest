from django.urls import path
from . import views

app_name = 'aviator'

urlpatterns = [
    path('', views.aviator_index, name='index'),
    path('bet/', views.place_bet, name='bet'),
    path('cashout/', views.cashout, name='cashout'),
    path('status/', views.round_status, name='status'),
]
