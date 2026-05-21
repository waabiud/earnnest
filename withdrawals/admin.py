from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from unfold.admin import ModelAdmin
from .models import Withdrawal
from notifications.models import Notification


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
            Notification.objects.create(
                user=w.user,
                notification_type='withdrawal_approved',
                title='Withdrawal Approved!',
                message=(
                    f'Your withdrawal of Ksh {w.amount} has been approved '
                    f'and sent to {w.phone_number}. '
                    f'Thank you for using Earnnest!'
                )
            )

            # Email user
            try:
                send_mail(
                    subject='Earnnest - Withdrawal Approved',
                    message=(
                        f'Hi {w.user.username},\n\n'
                        f'Your withdrawal of Ksh {w.amount} '
                        f'has been approved and sent to {w.phone_number}.\n\n'
                        f'Thank you for using Earnnest!'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[w.user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

        self.message_user(
            request,
            f'{queryset.count()} withdrawal(s) marked as paid.'
        )
    mark_paid.short_description = 'Mark selected as Paid'

    def mark_rejected(self, request, queryset):
        for w in queryset:
            w.status = 'rejected'
            w.save()

            # Notify user
            Notification.objects.create(
                user=w.user,
                notification_type='withdrawal_rejected',
                title='Withdrawal Rejected',
                message=(
                    f'Your withdrawal of Ksh {w.amount} was rejected. '
                    f'Your funds have been returned to your wallet. '
                    f'Contact support for more information.'
                )
            )

            # Refund wallet
            w.user.wallet_balance += w.amount
            w.user.save()

            # Email user
            try:
                send_mail(
                    subject='Earnnest - Withdrawal Rejected',
                    message=(
                        f'Hi {w.user.username},\n\n'
                        f'Your withdrawal of Ksh {w.amount} was rejected.\n'
                        f'Your funds have been returned to your wallet.\n\n'
                        f'Contact support for more information.'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[w.user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

        self.message_user(
            request,
            f'{queryset.count()} withdrawal(s) rejected and funds refunded.'
        )
    mark_rejected.short_description = 'Mark selected as Rejected & Refund'