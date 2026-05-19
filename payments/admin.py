from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = [
        'user', 'payment_type', 'amount',
        'phone_number', 'status', 'created_at'
    ]
    list_filter = ['status', 'payment_type']
    search_fields = ['user__username', 'reference', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
