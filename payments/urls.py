from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('activate/', views.activate_account, name='activate'),
    path('activate/pending/', views.activation_pending, name='activation_pending'),
    path('activate/status/', views.check_activation_status, name='activation_status'),
    path('callback/', views.mpesa_callback, name='callback'),
]
