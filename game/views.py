import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone

from .models import GameRound, GameEntry


def activated_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_activated:
            return redirect('payments:activate')
        return view_func(request, *args, **kwargs)
    return wrapper


@activated_required
def game_index(request):
    user = request.user

    # Get current open round
    current_round = GameRound.objects.filter(
        status='open'
    ).order_by('-created_at').first()

    # If no open round, get most recent
    if not current_round:
        current_round = GameRound.objects.order_by('-created_at').first()

    # Check if user already entered this round
    user_entry = None
    if current_round and current_round.status == 'open':
        user_entry = GameEntry.objects.filter(
            user=user,
            round=current_round
        ).first()

    # Past entries
    past_entries = GameEntry.objects.filter(
        user=user
    ).order_by('-created_at')[:10]

    # Recent winners
    recent_winners = GameRound.objects.filter(
        status='revealed',
        winner__isnull=False
    ).order_by('-revealed_at')[:5]

    context = {
        'current_round': current_round,
        'user_entry': user_entry,
        'past_entries': past_entries,
        'recent_winners': recent_winners,
    }
    return render(request, 'game/index.html', context)


@activated_required
def place_guess(request):
    if request.method != 'POST':
        return redirect('game:index')

    user = request.user
    guess = request.POST.get('guess', '').strip()

    current_round = GameRound.objects.filter(
        status='open'
    ).order_by('-created_at').first()

    if not current_round:
        messages.error(request, 'No active game round at the moment.')
        return redirect('game:index')

    if not guess.isdigit() or len(guess) != 4:
        messages.error(request, 'Please enter a valid 4-digit number.')
        return redirect('game:index')

    if GameEntry.objects.filter(user=user, round=current_round).exists():
        messages.error(request, 'You have already entered this round.')
        return redirect('game:index')

    entry_fee = current_round.entry_fee

    # Check wallet balance
    if user.wallet_balance < entry_fee:
        shortfall = entry_fee - user.wallet_balance
        messages.warning(
            request,
            f'Insufficient balance. You need Ksh {shortfall} more.'
        )
        return redirect('payments:topup')

    # Deduct from wallet
    user.wallet_balance -= entry_fee
    user.save()

    # Create entry
    GameEntry.objects.create(
        user=user,
        round=current_round,
        guess=guess,
        entry_fee=entry_fee,
        status='pending',
    )

    # Add to prize pool
    current_round.add_to_pool(entry_fee)

    messages.success(
        request,
        f'Your guess {guess} submitted for Round #{current_round.pk}! Good luck!'
    )
    return redirect('game:index')


@activated_required
def game_history(request):
    entries = GameEntry.objects.filter(
        user=request.user
    ).order_by('-created_at')
    return render(request, 'game/history.html', {'entries': entries})
