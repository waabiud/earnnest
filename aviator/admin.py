from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AviatorRound, AviatorBet


@admin.register(AviatorRound)
class AviatorRoundAdmin(ModelAdmin):
    list_display = ['id', 'crash_point', 'status', 'betting_ends_at', 'flying_ends_at', 'created_at']
    list_filter = ['status']
    readonly_fields = ['created_at', 'betting_ends_at', 'flying_ends_at']
    ordering = ['-created_at']


@admin.register(AviatorBet)
class AviatorBetAdmin(ModelAdmin):
    list_display = [
        'user', 'round', 'bet_amount',
        'auto_cashout', 'cashout_multiplier',
        'winnings', 'status', 'created_at'
    ]
    list_filter = ['status']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'cashed_out_at']
    ordering = ['-created_at']
