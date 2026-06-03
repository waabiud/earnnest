from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.register, name='api_register'),
    path('auth/login/', views.login, name='api_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('auth/profile/', views.profile, name='api_profile'),

    # Dashboard
    path('dashboard/', views.dashboard, name='api_dashboard'),

    # Payments
    path('payments/activate/', views.activate_account, name='api_activate'),
    path('payments/topup/', views.topup_wallet, name='api_topup'),
    path('payments/status/<str:reference>/', views.payment_status, name='api_payment_status'),

    # Investments
    path('investments/', views.investment_list, name='api_investments'),
    path('investments/create/', views.create_investment, name='api_create_investment'),

    # Withdrawals
    path('withdrawals/', views.withdrawal_list, name='api_withdrawals'),
    path('withdrawals/create/', views.create_withdrawal, name='api_create_withdrawal'),

    # Referrals
    path('referrals/', views.referral_list, name='api_referrals'),

    # Notifications
    path('notifications/', views.notification_list, name='api_notifications'),

    # Game
    path('game/', views.game_status, name='api_game'),
    path('game/play/', views.place_game_guess, name='api_game_play'),

    # Aviator
    path('aviator/', views.aviator_status, name='api_aviator'),
    path('aviator/bet/', views.aviator_bet, name='api_aviator_bet'),
    path('aviator/cashout/', views.aviator_cashout, name='api_aviator_cashout'),
]
