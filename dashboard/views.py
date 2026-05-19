from django.shortcuts import render, redirect
from payments.models import Payment
from investments.models import Investment
from referrals.models import Referral
from withdrawals.models import Withdrawal


def activated_required(view_func):
    """Custom decorator - user must be activated to access dashboard."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_activated:
            return redirect('payments:activate')
        return view_func(request, *args, **kwargs)
    return wrapper


@activated_required
def home(request):
    user = request.user

    # Recent payments
    recent_payments = Payment.objects.filter(
        user=user
    ).order_by('-created_at')[:5]

    # Active investments
    active_investments = Investment.objects.filter(
        user=user,
        status='active'
    ).order_by('-created_at')[:5]

    # Referrals
    referrals = Referral.objects.filter(
        referrer=user
    ).order_by('-created_at')[:5]

    # Recent withdrawals
    recent_withdrawals = Withdrawal.objects.filter(
        user=user
    ).order_by('-created_at')[:3]

    # Stats
    total_invested = sum(
        i.amount for i in Investment.objects.filter(
            user=user,
            status__in=['active', 'matured']
        )
    )
    total_earned = sum(
        i.profit for i in Investment.objects.filter(
            user=user,
            status='matured'
        )
    )
    total_referral_earnings = sum(
        r.bonus_amount for r in Referral.objects.filter(
            referrer=user,
            bonus_paid=True
        )
    )

    # Build referral link safely
    scheme = request.scheme
    host = request.get_host()
    referral_link = f"{scheme}://{host}/accounts/register/?ref={user.referral_code}"

    context = {
        'user': user,
        'wallet_balance': user.wallet_balance,
        'total_invested': total_invested,
        'total_earned': total_earned,
        'total_referral_earnings': total_referral_earnings,
        'total_referrals': user.get_total_referrals(),
        'recent_payments': recent_payments,
        'active_investments': active_investments,
        'referrals': referrals,
        'recent_withdrawals': recent_withdrawals,
        'referral_link': referral_link,
    }
    return render(request, 'dashboard/home.html', context)