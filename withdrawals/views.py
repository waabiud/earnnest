from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Withdrawal
from investments.models import Investment


def activated_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_activated:
            return redirect('payments:activate')
        return view_func(request, *args, **kwargs)
    return wrapper


@activated_required
def withdrawal_index(request):
    user = request.user

    # Only matured investments that haven't been withdrawn
    matured_investments = Investment.objects.filter(
        user=user,
        status='matured'
    )

    withdrawals = Withdrawal.objects.filter(
        user=user
    ).order_by('-created_at')

    # Total available to withdraw
    available = sum(i.total_return() for i in matured_investments)
    wallet = user.wallet_balance

    context = {
        'withdrawals': withdrawals,
        'matured_investments': matured_investments,
        'available': available,
        'wallet': wallet,
        'total_withdrawable': available + wallet,
    }
    return render(request, 'withdrawals/index.html', context)


@activated_required
def request_withdrawal(request):
    user = request.user

    if request.method == 'POST':
        amount = request.POST.get('amount')
        phone = request.POST.get('phone_number', user.phone_number)
        source = request.POST.get('source', 'wallet')  # 'wallet' or 'investment'

        try:
            amount = int(amount)
        except (ValueError, TypeError):
            messages.error(request, 'Enter a valid amount.')
            return redirect('withdrawals:index')

        if amount <= 0:
            messages.error(request, 'Amount must be greater than 0.')
            return redirect('withdrawals:index')

        # Check source
        if source == 'wallet':
            if amount > user.wallet_balance:
                messages.error(request, f'Insufficient wallet balance. Available: Ksh {user.wallet_balance}')
                return redirect('withdrawals:index')
            # Deduct from wallet
            user.wallet_balance -= amount
            user.save()

        elif source == 'investment':
            matured = Investment.objects.filter(
                user=user,
                status='matured'
            )
            total_matured = sum(i.total_return() for i in matured)

            if amount > total_matured:
                messages.error(request, f'Insufficient matured investment funds. Available: Ksh {total_matured}')
                return redirect('withdrawals:index')

            # Mark investments as withdrawn
            remaining = amount
            for inv in matured:
                if remaining <= 0:
                    break
                inv.status = 'withdrawn'
                inv.save()
                remaining -= inv.total_return()

        # Create withdrawal request
        Withdrawal.objects.create(
            user=user,
            amount=amount,
            phone_number=phone,
            status='pending',
        )

        messages.success(
            request,
            f'Withdrawal request of Ksh {amount} submitted. '
            f'You will receive funds on {phone} within 24 hours.'
        )
        return redirect('withdrawals:index')

    return redirect('withdrawals:index')


@activated_required
def withdrawal_history(request):
    withdrawals = Withdrawal.objects.filter(
        user=request.user
    ).order_by('-created_at')
    return render(request, 'withdrawals/history.html', {'withdrawals': withdrawals})
