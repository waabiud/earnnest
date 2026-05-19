from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Referral


def activated_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_activated:
            return redirect('payments:activate')
        return view_func(request, *args, **kwargs)
    return wrapper


@activated_required
def referral_dashboard(request):
    user = request.user

    referrals = Referral.objects.filter(
        referrer=user
    ).select_related('referred_user').order_by('-created_at')

    total_earned = sum(r.bonus_amount for r in referrals if r.bonus_paid)
    total_referrals = referrals.count()
    paid_referrals = referrals.filter(bonus_paid=True).count()

    referral_link = f"{request.scheme}://{request.get_host()}/accounts/register/?ref={user.referral_code}"

    context = {
        'referrals': referrals,
        'referral_link': referral_link,
        'referral_code': user.referral_code,
        'total_earned': total_earned,
        'total_referrals': total_referrals,
        'paid_referrals': paid_referrals,
    }
    return render(request, 'referrals/dashboard.html', context)
