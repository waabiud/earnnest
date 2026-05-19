from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('activate/', views.activate_account, name='activate'),
    path('activate/pending/', views.activation_pending, name='activation_pending'),
    path('activate/status/', views.check_activation_status, name='activation_status'),
    path('topup/', views.topup_wallet, name='topup'),
    path('topup/pending/', views.topup_pending, name='topup_pending'),
    path('topup/status/', views.check_topup_status, name='topup_status'),
    path('callback/', views.mpesa_callback, name='callback'),
]