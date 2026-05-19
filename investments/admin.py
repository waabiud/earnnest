from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Investment


@admin.register(Investment)
class InvestmentAdmin(ModelAdmin):
    list_display = [
        'user', 'amount', 'profit',
        'status', 'maturity_date', 'notified', 'created_at'
    ]
    list_filter = ['status', 'notified']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'maturity_date', 'profit']
    ordering = ['-created_at']
