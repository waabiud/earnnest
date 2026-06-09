from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.views.generic import TemplateView


def home_redirect(request):
    if request.user.is_authenticated:
        if request.user.is_activated:
            return redirect('dashboard:home')
        return redirect('payments:activate')
    return TemplateView.as_view(template_name='home.html')(request)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('accounts/', include('accounts.urls')),
    path('payments/', include('payments.urls')),
    path('investments/', include('investments.urls')),
    path('referrals/', include('referrals.urls')),
    path('withdrawals/', include('withdrawals.urls')),
    path('aviator/', include('aviator.urls')),
    path('game/', include('game.urls')),
    path('notifications/', include('notifications.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/', include('api.urls')),
]