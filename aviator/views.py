import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import AviatorRound, AviatorBet
from decimal import Decimal


def activated_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_activated:
            return redirect('payments:activate')
        return view_func(request, *args, **kwargs)
    return wrapper


@activated_required
def aviator_index(request):
    user = request.user

    # Get current round
    current_round = AviatorRound.objects.filter(
        status__in=['waiting', 'flying']
    ).order_by('-created_at').first()

    # If no round exists create one
    if not current_round:
        current_round = AviatorRound.objects.create(status='waiting')

    # User's bet in current round
    user_bet = AviatorBet.objects.filter(
        user=user,
        round=current_round
    ).first()

    # Recent rounds history
    recent_rounds = AviatorRound.objects.filter(
        status='crashed'
    ).order_by('-created_at')[:10]

    # User's bet history
    bet_history = AviatorBet.objects.filter(
        user=user
    ).order_by('-created_at')[:10]

    # Top wins
    top_wins = AviatorBet.objects.filter(
        status='won'
    ).order_by('-winnings')[:5]

    context = {
        'current_round': current_round,
        'user_bet': user_bet,
        'recent_rounds': recent_rounds,
        'bet_history': bet_history,
        'top_wins': top_wins,
        'wallet': user.wallet_balance,
        'min_bet': 5,
    }
    return render(request, 'aviator/index.html', context)


@activated_required
def place_bet(request):
    if request.method != 'POST':
        return redirect('aviator:index')

    user = request.user

    try:
        data = json.loads(request.body)
        bet_amount = Decimal(str(data.get('bet_amount', 0)))
        auto_cashout = data.get('auto_cashout')

        if auto_cashout:
            auto_cashout = float(auto_cashout)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid data.'})

    # Validate amount
    if bet_amount < 5:
        return JsonResponse({'success': False, 'error': 'Minimum bet is Ksh 5.'})

    if bet_amount > user.wallet_balance:
        return JsonResponse({
            'success': False,
            'error': f'Insufficient balance. Available: Ksh {user.wallet_balance}'
        })

    # Get current waiting round
    current_round = AviatorRound.objects.filter(
        status='waiting'
    ).order_by('-created_at').first()

    if not current_round:
        return JsonResponse({
            'success': False,
            'error': 'No active round. Please wait for next round.'
        })

    # Check if already bet
    if AviatorBet.objects.filter(user=user, round=current_round).exists():
        return JsonResponse({
            'success': False,
            'error': 'You have already placed a bet this round.'
        })

    # Deduct from wallet
    user.wallet_balance -= bet_amount
    user.save()

    # Create bet
    bet = AviatorBet.objects.create(
        user=user,
        round=current_round,
        bet_amount=bet_amount,
        auto_cashout=auto_cashout,
        status='active',
    )

    return JsonResponse({
        'success': True,
        'bet_id': bet.pk,
        'bet_amount': float(bet_amount),
        'auto_cashout': auto_cashout,
        'wallet_balance': float(user.wallet_balance),
    })


@activated_required
def cashout(request):
    if request.method != 'POST':
        return JsonResponse({'success': False})

    user = request.user

    try:
        data = json.loads(request.body)
        multiplier = float(data.get('multiplier', 1.0))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid data.'})

    # Get active bet
    current_round = AviatorRound.objects.filter(
        status='flying'
    ).order_by('-created_at').first()

    if not current_round:
        return JsonResponse({'success': False, 'error': 'No active round.'})

    bet = AviatorBet.objects.filter(
        user=user,
        round=current_round,
        status='active'
    ).first()

    if not bet:
        return JsonResponse({'success': False, 'error': 'No active bet found.'})

    # Validate multiplier hasn't exceeded crash point
    if multiplier > current_round.crash_point:
        multiplier = current_round.crash_point

    # Calculate winnings
    winnings = Decimal(str(bet.calculate_winnings(multiplier)))

    # Credit wallet
    user.wallet_balance += winnings
    user.save()

    # Update bet
    bet.status = 'won'
    bet.cashout_multiplier = multiplier
    bet.winnings = winnings
    bet.cashed_out_at = timezone.now()
    bet.save()

    return JsonResponse({
        'success': True,
        'multiplier': multiplier,
        'winnings': float(winnings),
        'wallet_balance': float(user.wallet_balance),
    })


def round_status(request):
    """AJAX endpoint — frontend polls this to get current round state."""
    current_round = AviatorRound.objects.filter(
        status__in=['waiting', 'flying', 'crashed']
    ).order_by('-created_at').first()

    if not current_round:
        return JsonResponse({'status': 'none'})

    data = {
        'round_id': current_round.pk,
        'status': current_round.status,
        'crash_point': current_round.crash_point if current_round.status == 'crashed' else None,
        'started_at': current_round.started_at.isoformat() if current_round.started_at else None,
    }

    # Include user's bet if logged in
    if request.user.is_authenticated:
        bet = AviatorBet.objects.filter(
            user=request.user,
            round=current_round
        ).first()
        if bet:
            data['user_bet'] = {
                'bet_id': bet.pk,
                'bet_amount': float(bet.bet_amount),
                'status': bet.status,
                'auto_cashout': bet.auto_cashout,
                'winnings': float(bet.winnings),
                'cashout_multiplier': bet.cashout_multiplier,
            }

    return JsonResponse(data)
