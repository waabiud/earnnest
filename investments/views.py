from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone

from .models import Investment
from payments.models import Payment
from payments.mpesa import send_stk_push
import uuid


def activated_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_activated:
            return redirect('payments:activate')
        return view_func(request, *args, **kwargs)
    return wrapper


def generate_reference():
    return f"INV-{uuid.uuid4().hex[:10].upper()}"


@activated_required
def investment_list(request):
    investments = Investment.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Separate by status
    active = investments.filter(status='active')
    matured = investments.filter(status='matured')
    withdrawn = investments.filter(status='withdrawn')

    total_invested = sum(i.amount for i in investments)
    total_profit = sum(i.profit for i in matured)

    context = {
        'investments': investments,
        'active': active,
        'matured': matured,
        'withdrawn': withdrawn,
        'total_invested': total_invested,
        'total_profit': total_profit,
        'min_investment': settings.MIN_INVESTMENT,
        'return_percent': settings.INVESTMENT_RETURN_PERCENT,
        'maturity_hours': settings.INVESTMENT_MATURITY_HOURS,
    }
    return render(request, 'investments/list.html', context)


@activated_required
def create_investment(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')

        try:
            amount = int(amount)
        except (ValueError, TypeError):
            messages.error(request, 'Enter a valid amount.')
            return redirect('investments:create')

        if amount < settings.MIN_INVESTMENT:
            messages.error(
                request,
                f'Minimum investment is Ksh {settings.MIN_INVESTMENT}.'
            )
            return redirect('investments:create')

        user = request.user

        # Check wallet balance
        if user.wallet_balance < amount:
            shortfall = amount - user.wallet_balance
            messages.warning(
                request,
                f'Insufficient balance. You need Ksh {shortfall} more to invest Ksh {amount}.'
            )
            return redirect(f'/payments/topup/?amount={shortfall}&next=invest&invest_amount={amount}')

        # Deduct from wallet
        user.wallet_balance -= amount
        user.save()

        # Create investment directly
        from .models import Investment
        Investment.objects.create(
            user=user,
            amount=amount,
        )

        messages.success(
            request,
            f'Investment of Ksh {amount} placed successfully! '
            f'Matures in {settings.INVESTMENT_MATURITY_HOURS} hours.'
        )
        return redirect('investments:list')

    context = {
        'min_investment': settings.MIN_INVESTMENT,
        'return_percent': settings.INVESTMENT_RETURN_PERCENT,
        'maturity_hours': settings.INVESTMENT_MATURITY_HOURS,
        'wallet': request.user.wallet_balance,
    }
    return render(request, 'investments/create.html', context)

@activated_required
def investment_pending(request):
    payment = Payment.objects.filter(
        user=request.user,
        payment_type='investment',
        status='pending'
    ).order_by('-created_at').first()

    return render(request, 'investments/pending.html', {'payment': payment})
