from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('', views.investment_list, name='list'),
    path('create/', views.create_investment, name='create'),
    path('pending/', views.investment_pending, name='pending'),
]
