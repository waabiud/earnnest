from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = [
        'username', 'email', 'phone_number',
        'is_activated', 'wallet_balance', 'date_joined'
    ]
    list_filter = ['is_activated', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'phone_number']
    readonly_fields = ['date_joined', 'last_login', 'referral_code']

    fieldsets = UserAdmin.fieldsets + (
        ('Earnnest Info', {
            'fields': (
                'phone_number', 'referral_code',
                'referred_by', 'is_activated', 'wallet_balance'
            )
        }),
    )
