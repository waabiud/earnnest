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
        if form.is_valid():
            user = form.save(commit=False)

            # Link referrer
            referral_code = form.cleaned_data.get('referral_code')
            if referral_code:
                try:
                    referrer = User.objects.get(referral_code=referral_code)
                    user.referred_by = referrer
                except User.DoesNotExist:
                    pass

            user.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Please pay Ksh 200 to activate your account.')
            return redirect('payments:activate')
    else:
        # Pre-fill referral code from URL ?ref=CODE
        ref_code = request.GET.get('ref', '')
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
                    messages.warning(request, 'Account not activated. Pay Ksh 200 to continue.')
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
    return render(request, 'accounts/profile.html', {'user': request.user})
