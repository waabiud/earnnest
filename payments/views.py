import uuid
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings

from .models import Payment
from .mpesa import send_stk_push, verify_callback_signature
from referrals.models import Referral


# ─── ACTIVATION ───────────────────────────────────────────────────────────────

@login_required
def activate_account(request):
    if request.user.is_activated:
        messages.info(request, 'Your account is already activated.')
        return redirect('dashboard:home')

    pending = Payment.objects.filter(
        user=request.user,
        payment_type='activation',
        status='pending'
    ).first()

    if request.method == 'POST':
        phone = request.POST.get('phone_number', request.user.phone_number)
        reference = f"ACT-{uuid.uuid4().hex[:10].upper()}"

        payment = Payment.objects.create(
            user=request.user,
            payment_type='activation',
            amount=settings.ACTIVATION_FEE,
            phone_number=phone,
            reference=reference,
            description='Earnnest Account Activation',
        )

        success, response = send_stk_push(
            phone_number=phone,
            amount=settings.ACTIVATION_FEE,
            reference=reference,
            description='Earnnest Account Activation'
        )

        if success:
            payment.checkout_request_id = response.get('checkout_request_id', '')
            payment.save()
            messages.success(
                request,
                f'STK Push sent to {phone}. Enter your M-Pesa PIN to complete payment.'
            )
            return redirect('payments:activation_pending')
        else:
            payment.status = 'failed'
            payment.description = response.get('message', 'STK push failed')
            payment.save()
            messages.error(
                request,
                f"Payment failed: {response.get('message', 'Try again.')}"
            )

    context = {
        'fee': settings.ACTIVATION_FEE,
        'phone': request.user.phone_number,
        'pending': pending,
    }
    return render(request, 'payments/activate.html', context)


@login_required
def activation_pending(request):
    payment = Payment.objects.filter(
        user=request.user,
        payment_type='activation'
    ).order_by('-created_at').first()
    return render(request, 'payments/activation_pending.html', {'payment': payment})


@login_required
def check_activation_status(request):
    payment = Payment.objects.filter(
        user=request.user,
        payment_type='activation'
    ).order_by('-created_at').first()

    if not payment:
        return JsonResponse({'status': 'not_found'})

    return JsonResponse({
        'status': payment.status,
        'is_activated': request.user.is_activated,
    })


# ─── TOP UP ───────────────────────────────────────────────────────────────────

@login_required
def topup_wallet(request):
    if not request.user.is_activated:
        return redirect('payments:activate')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        phone = request.POST.get('phone_number', request.user.phone_number)

        try:
            amount = int(amount)
        except (ValueError, TypeError):
            messages.error(request, 'Enter a valid amount.')
            return redirect('payments:topup')

        if amount < 10:
            messages.error(request, 'Minimum top up is Ksh 10.')
            return redirect('payments:topup')

        reference = f"TOP-{uuid.uuid4().hex[:10].upper()}"
        payment = Payment.objects.create(
            user=request.user,
            payment_type='topup',
            amount=amount,
            phone_number=phone,
            reference=reference,
            description=f'Earnnest Wallet Top Up - Ksh {amount}',
        )

        success, response = send_stk_push(
            phone_number=phone,
            amount=amount,
            reference=reference,
            description=f'Earnnest Wallet Top Up Ksh {amount}'
        )

        if success:
            payment.checkout_request_id = response.get('checkout_request_id', '')
            payment.save()
            messages.success(
                request,
                f'STK Push sent to {phone}. Enter M-Pesa PIN to top up Ksh {amount}.'
            )
            return redirect('payments:topup_pending')
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(
                request,
                f"Top up failed: {response.get('message', 'Try again.')}"
            )

    suggested_amount = request.GET.get('amount', '')
    invest_amount = request.GET.get('invest_amount', '')

    context = {
        'wallet': request.user.wallet_balance,
        'phone': request.user.phone_number,
        'suggested_amount': suggested_amount,
        'invest_amount': invest_amount,
    }
    return render(request, 'payments/topup.html', context)


@login_required
def topup_pending(request):
    payment = Payment.objects.filter(
        user=request.user,
        payment_type='topup',
        status='pending'
    ).order_by('-created_at').first()
    return render(request, 'payments/topup_pending.html', {'payment': payment})


@login_required
def check_topup_status(request):
    payment = Payment.objects.filter(
        user=request.user,
        payment_type='topup'
    ).order_by('-created_at').first()

    if not payment:
        return JsonResponse({'status': 'not_found'})

    # Refresh user from DB to get latest balance
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(pk=request.user.pk)

    return JsonResponse({
        'status': payment.status,
        'wallet_balance': str(user.wallet_balance),
    })


# ─── MPESA CALLBACK ───────────────────────────────────────────────────────────

@csrf_exempt
def mpesa_callback(request):
    if request.method != 'POST':
        return JsonResponse({'result': 'method not allowed'}, status=405)

    try:
        raw_body = request.body.decode('utf-8')

        received_signature = request.headers.get('X-Signature', '')
        if not verify_callback_signature(raw_body, received_signature):
            return JsonResponse({'result': 'invalid signature'}, status=403)

        data = json.loads(raw_body)

        reference = data.get('reference')
        status = data.get('status')
        transaction_id = data.get('mpesa_receipt_number', '')

        try:
            payment = Payment.objects.get(reference=reference)
        except Payment.DoesNotExist:
            return JsonResponse({'result': 'payment not found'}, status=404)

        payment.transaction_id = transaction_id

        if status == 'success':
            payment.status = 'success'
            payment.save()

            user = payment.user

            # --- ACTIVATION ---
            if payment.payment_type == 'activation':
                if not user.is_activated:
                    user.is_activated = True
                    user.save()

                    from notifications.models import Notification

                    # Notify new user
                    Notification.objects.create(
                        user=user,
                        notification_type='general',
                        title='Account Activated!',
                        message=(
                            'Your account has been activated successfully. '
                            'You can now invest, refer friends and play games. '
                            'Happy earning!'
                        )
                    )

                    # Credit referrer Ksh 50
                    if user.referred_by:
                        referrer = user.referred_by
                        referrer.wallet_balance += settings.REFERRAL_BONUS
                        referrer.save()

                        # Notify referrer
                        Notification.objects.create(
                            user=referrer,
                            notification_type='referral_bonus',
                            title='Referral Bonus Received!',
                            message=(
                                f'{user.username} just activated their account '
                                f'using your referral link. '
                                f'Ksh {settings.REFERRAL_BONUS} has been '
                                f'credited to your wallet!'
                            )
                        )

                        Referral.objects.get_or_create(
                            referrer=referrer,
                            referred_user=user,
                            defaults={
                                'bonus_amount': settings.REFERRAL_BONUS,
                                'bonus_paid': True,
                            }
                        )

            # --- TOPUP ---
            elif payment.payment_type == 'topup':
                user.wallet_balance += payment.amount
                user.save()

                from notifications.models import Notification
                Notification.objects.create(
                    user=user,
                    notification_type='general',
                    title='Wallet Topped Up!',
                    message=(
                        f'Your wallet has been topped up with Ksh {payment.amount}. '
                        f'New balance: Ksh {user.wallet_balance}.'
                    )
                )

            # --- INVESTMENT ---
            elif payment.payment_type == 'investment':
                from investments.models import Investment
                Investment.objects.get_or_create(
                    payment=payment,
                    defaults={
                        'user': user,
                        'amount': payment.amount,
                    }
                )

            # --- GAME ---
            elif payment.payment_type == 'game':
                from game.models import GameEntry
                entry = GameEntry.objects.filter(payment=payment).first()
                if entry:
                    entry.status = 'pending'
                    entry.save()
                    entry.round.add_to_pool(payment.amount)

        else:
            payment.status = 'failed'
            payment.save()

        return JsonResponse({'result': 'ok'})

    except Exception as e:
        return JsonResponse({'result': str(e)}, status=500)
