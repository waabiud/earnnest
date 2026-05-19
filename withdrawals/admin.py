from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Withdrawal


@admin.register(Withdrawal)
class WithdrawalAdmin(ModelAdmin):
    list_display = [
        'user', 'amount', 'phone_number',
        'status', 'created_at'
    ]
    list_filter = ['status']
    search_fields = ['user__username', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    actions = ['mark_paid', 'mark_rejected']

    def mark_paid(self, request, queryset):
        for w in queryset:
            w.status = 'paid'
            w.save()
            # Notify user
            from notifications.models import Notification
            Notification.objects.create(
                user=w.user,
                notification_type='withdrawal_approved',
                title='Withdrawal Approved!',
                message=(
                    f'Your withdrawal of Ksh {w.amount} has been approved '
                    f'and sent to {w.phone_number}.'
                )
            )
        self.message_user(request, f'{queryset.count()} withdrawal(s) marked as paid.')
    mark_paid.short_description = 'Mark selected as Paid'

    def mark_rejected(self, request, queryset):
        for w in queryset:
            w.status = 'rejected'
            w.save()
            from notifications.models import Notification
            Notification.objects.create(
                user=w.user,
                notification_type='withdrawal_rejected',
                title='Withdrawal Rejected',
                message=(
                    f'Your withdrawal of Ksh {w.amount} was rejected. '
                    f'Contact support for more information.'
                )
            )
        self.message_user(request, f'{queryset.count()} withdrawal(s) marked as rejected.')
    mark_rejected.short_description = 'Mark selected as Rejected'
