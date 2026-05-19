from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Referral


@admin.register(Referral)
class ReferralAdmin(ModelAdmin):
    list_display = [
        'referrer', 'referred_user',
        'bonus_amount', 'bonus_paid', 'created_at'
    ]
    list_filter = ['bonus_paid']
    search_fields = ['referrer__username', 'referred_user__username']
    readonly_fields = ['created_at']
