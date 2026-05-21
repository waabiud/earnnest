from celery import shared_task
from django.utils import timezone


@shared_task
def send_daily_notifications():
    """
    Sends daily notifications to all activated users.
    Runs every day at 8:00 AM Nairobi time.
    """
    from accounts.models import User
    from .models import Notification
    from investments.models import Investment

    users = User.objects.filter(is_activated=True)

    for user in users:
        # Check active investments
        active_investments = Investment.objects.filter(
            user=user,
            status='active'
        )

        # Check matured investments
        matured_investments = Investment.objects.filter(
            user=user,
            status='matured'
        )

        # Build personalized message
        parts = []

        if matured_investments.exists():
            total_matured = sum(i.total_return() for i in matured_investments)
            parts.append(
                f'💰 You have Ksh {total_matured} ready to withdraw '
                f'from {matured_investments.count()} matured investment(s)!'
            )

        if active_investments.exists():
            parts.append(
                f'📈 You have {active_investments.count()} active '
                f'investment(s) growing.'
            )

        if user.wallet_balance > 0:
            parts.append(
                f'👛 Wallet balance: Ksh {user.wallet_balance}.'
            )

        if not active_investments.exists() and user.wallet_balance >= 1000:
            parts.append(
                f'🚀 You have Ksh {user.wallet_balance} in your wallet. '
                f'Invest now and earn 5% in 48 hours!'
            )

        if not parts:
            parts.append(
                '💡 Top up your wallet and start investing to earn daily!'
            )

        # Referral reminder
        referral_count = user.get_total_referrals()
        parts.append(
            f'👥 You have {referral_count} referral(s). '
            f'Share your link to earn Ksh 50 per friend!'
        )

        # Create notification
        Notification.objects.create(
            user=user,
            notification_type='general',
            title=f'Good Morning {user.username}! 🌅',
            message=' '.join(parts)
        )

    return f'Sent daily notifications to {users.count()} users.'


@shared_task
def send_investment_reminder():
    """
    Reminds users with wallet balance >= 1000 to invest.
    Runs every day at 12:00 PM.
    """
    from accounts.models import User
    from .models import Notification
    from investments.models import Investment

    # Users with enough balance but no active investments
    users = User.objects.filter(
        is_activated=True,
        wallet_balance__gte=1000
    )

    count = 0
    for user in users:
        has_active = Investment.objects.filter(
            user=user,
            status='active'
        ).exists()

        if not has_active:
            Notification.objects.create(
                user=user,
                notification_type='general',
                title='💡 Invest Your Idle Funds!',
                message=(
                    f'Hi {user.username}, you have Ksh {user.wallet_balance} '
                    f'sitting idle in your wallet. '
                    f'Invest now and earn 5% in just 48 hours! '
                    f'Minimum investment is Ksh 1,000.'
                )
            )
            count += 1

    return f'Sent investment reminders to {count} users.'


@shared_task
def send_referral_reminder():
    """
    Reminds users to share their referral link.
    Runs every 3 days.
    """
    from accounts.models import User
    from .models import Notification

    # Users with no referrals
    users = User.objects.filter(
        is_activated=True,
        referrals__isnull=True
    ).distinct()

    for user in users:
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='👥 Earn Ksh 50 Per Referral!',
            message=(
                f'Hi {user.username}, you haven\'t referred anyone yet. '
                f'Share your referral link and earn Ksh 50 '
                f'for every friend who activates their account. '
                f'No limit on referrals!'
            )
        )

    return f'Sent referral reminders to {users.count()} users.'
