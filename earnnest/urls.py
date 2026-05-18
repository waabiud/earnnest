from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('accounts:login'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('payments/', include('payments.urls')),
    path('investments/', include('investments.urls')),
    path('referrals/', include('referrals.urls')),
    path('withdrawals/', include('withdrawals.urls')),
    path('game/', include('game.urls')),
    path('notifications/', include('notifications.urls')),
    path('dashboard/', include('dashboard.urls')),
]
