import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json

from .models import Payment
from .mpesa import send_stk_push
from referrals.models import Referral


def generate_reference():
    return f"ACT-{uuid.uuid4().hex[:10].upper()}"


@login_required
def activate_account(request):
    """Show activation page and trigger STK push."""

    # Already activated
    if request.user.is_activated:
        messages.info(request, 'Your account is already activated.')
        return redirect('dashboard:home')

    # Check if there's a pending payment already
    pending = Payment.objects.filter(
        user=request.user,
        payment_type='activation',
        status='pending'
    ).first()

    if request.method == 'POST':
        phone = request.POST.get('phone_number', request.user.phone_number)

        # Create payment record
        reference = generate_reference()
        payment = Payment.objects.create(
            user=request.user,
            payment_type='activation',
            amount=settings.ACTIVATION_FEE,
            phone_number=phone,
            reference=reference,
            description='Earnnest Account Activation',
        )

        # Send STK Push
        success, response = send_stk_push(
            phone_number=phone,
            amount=settings.ACTIVATION_FEE,
            reference=reference,
            description='Earnnest Account Activation'
        )

        if success:
            # Save checkout request id from codian response
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
            messages.error(request, f"Payment failed: {response.get('message', 'Try again.')}")

    context = {
        'fee': settings.ACTIVATION_FEE,
        'phone': request.user.phone_number,
        'pending': pending,
    }
    return render(request, 'payments/activate.html', context)


@login_required
def activation_pending(request):
    """Page shown after STK push, user waits for confirmation."""
    payment = Payment.objects.filter(
        user=request.user,
        payment_type='activation'
    ).order_by('-created_at').first()

    return render(request, 'payments/activation_pending.html', {'payment': payment})


@login_required
def check_activation_status(request):
    """AJAX endpoint — frontend polls this to check if payment came through."""
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


@csrf_exempt
def mpesa_callback(request):
    """
    Codian/Mpesa sends payment result here.
    Update payment status and activate user if successful.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Codian sends back reference and status
            reference = data.get('reference')
            status = data.get('status')           # 'success' or 'failed'
            transaction_id = data.get('mpesa_receipt_number', '')

            payment = Payment.objects.get(reference=reference)
            payment.transaction_id = transaction_id

            if status == 'success':
                payment.status = 'success'
                payment.save()

                # Activate user
                user = payment.user
                if payment.payment_type == 'activation' and not user.is_activated:
                    user.is_activated = True
                    user.save()

                    # Credit referrer bonus if any
                    if user.referred_by:
                        referrer = user.referred_by
                        referrer.wallet_balance += settings.REFERRAL_BONUS
                        referrer.save()

                        # Record referral
                        Referral.objects.get_or_create(
                            referrer=referrer,
                            referred_user=user,
                            defaults={
                                'bonus_amount': settings.REFERRAL_BONUS,
                                'bonus_paid': True,
                            }
                        )

            else:
                payment.status = 'failed'
                payment.save()

            return JsonResponse({'result': 'ok'})

        except Payment.DoesNotExist:
            return JsonResponse({'result': 'payment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'result': str(e)}, status=500)

    return JsonResponse({'result': 'method not allowed'}, status=405)
