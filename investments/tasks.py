from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def check_matured_investments():
    """
    Runs every 30 minutes.
    Finds active investments that have matured,
    credits wallet, sends email + in-app notification.
    """
    from .models import Investment
    from notifications.models import Notification

    now = timezone.now()
    matured = Investment.objects.filter(
        status='active',
        maturity_date__lte=now,
        notified=False
    )

    for investment in matured:
        user = investment.user

        # Update investment status
        investment.status = 'matured'
        investment.notified = True
        investment.save()

        # Credit wallet with profit + principal
        user.wallet_balance += investment.total_return()
        user.save()

        # Create in-app notification
        Notification.objects.create(
            user=user,
            notification_type='investment_matured',
            title='Investment Matured!',
            message=(
                f'Your investment of Ksh {investment.amount} has matured. '
                f'You earned Ksh {investment.profit} profit. '
                f'Total Ksh {investment.total_return()} has been credited to your wallet.'
            )
        )

        # Send email notification
        try:
            send_mail(
                subject='🎉 Your Earnnest Investment Has Matured!',
                message=(
                    f'Hi {user.username},\n\n'
                    f'Great news! Your investment has matured.\n\n'
                    f'Investment Amount: Ksh {investment.amount}\n'
                    f'Profit Earned:     Ksh {investment.profit}\n'
                    f'Total Credited:    Ksh {investment.total_return()}\n\n'
                    f'Log in to withdraw your funds:\n'
                    f'http://yourdomain.com/withdrawals/\n\n'
                    f'Thank you for using Earnnest!\n'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

    return f'Processed {matured.count()} matured investments.'
