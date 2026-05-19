from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        print(f"[REGISTER] Form submitted")
        print(f"[REGISTER] Form valid: {form.is_valid()}")
        print(f"[REGISTER] Form errors: {form.errors}")

        if form.is_valid():
            user = form.save(commit=False)
            print(f"[REGISTER] User created: {user.username}")

            referral_code = form.cleaned_data.get('referral_code', '').strip().upper()
            print(f"[REGISTER] Referral code: {referral_code}")

            if referral_code:
                try:
                    referrer = User.objects.get(referral_code=referral_code)
                    user.referred_by = referrer
                    print(f"[REGISTER] Referrer found: {referrer.username}")
                except User.DoesNotExist:
                    print(f"[REGISTER] Referrer not found")

            user.save()
            login(request, user)
            print(f"[REGISTER] Redirecting to activate")
            messages.success(
                request,
                f'Welcome {user.username}! Pay Ksh 200 to activate.'
            )
            return redirect('payments:activate')

        print(f"[REGISTER] Form invalid - re-rendering")
        return render(request, 'accounts/register.html', {'form': form})

    else:
        ref_code = request.GET.get('ref', '').strip().upper()
        form = RegisterForm(initial={'referral_code': ref_code})

    return render(request, 'accounts/register.html', {'form': form})
def login_view(request):
    if request.user.is_authenticated:
        if not request.user.is_activated:
            return redirect('payments:activate')
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                if not user.is_activated:
                    messages.warning(
                        request,
                        'Account not activated. Pay Ksh 200 to continue.'
                    )
                    return redirect('payments:activate')
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard:home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        phone = request.POST.get('phone_number', '').strip()
        if phone and phone != user.phone_number:
            if not phone.startswith('254') or len(phone) != 12:
                messages.error(
                    request,
                    'Enter a valid phone number e.g. 254712345678'
                )
            elif User.objects.filter(phone_number=phone).exclude(pk=user.pk).exists():
                messages.error(request, 'That phone number is already in use.')
            else:
                user.phone_number = phone
                user.save()
                messages.success(request, 'Phone number updated successfully.')
        return redirect('accounts:profile')

    from payments.models import Payment
    from investments.models import Investment
    from referrals.models import Referral

    recent_payments = Payment.objects.filter(
        user=user
    ).order_by('-created_at')[:5]

    total_investments = Investment.objects.filter(user=user).count()
    total_referrals = Referral.objects.filter(referrer=user).count()

    context = {
        'user': user,
        'recent_payments': recent_payments,
        'total_investments': total_investments,
        'total_referrals': total_referrals,
    }
    return render(request, 'accounts/profile.html', context)