from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'phone_number', 'is_activated', 'wallet_balance']
    list_filter = ['is_activated', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Earnnest Info', {
            'fields': ('phone_number', 'referral_code', 'referred_by', 'is_activated', 'wallet_balance')
        }),
    )
