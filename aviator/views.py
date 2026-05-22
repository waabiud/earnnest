import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from .models import AviatorRound, AviatorBet, BETTING_DURATION


def activated_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_activated:
            return redirect('payments:activate')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_or_create_round():
    now = timezone.now()

    active_round = AviatorRound.objects.filter(
        status__in=['betting', 'flying']
    ).order_by('-created_at').first()

    if active_round:
        if active_round.status == 'betting' and now >= active_round.betting_ends_at:
            active_round.status = 'flying'
            active_round.save()
        elif active_round.status == 'flying' and now >= active_round.flying_ends_at:
            active_round.status = 'crashed'
            active_round.save()
            settle_lost_bets(active_round)
            active_round = AviatorRound.objects.create()
        return active_round

    return AviatorRound.objects.create()


def settle_lost_bets(active_round):
    AviatorBet.objects.filter(
        round=active_round,
        status='active'
    ).update(status='lost')


def process_auto_cashouts(active_round):
    if active_round.status != 'flying':
        return

    current_mult = active_round.current_multiplier()
    active_bets = AviatorBet.objects.filter(
        round=active_round,
        status='active',
        auto_cashout__isnull=False,
        auto_cashout__lte=current_mult
    ).select_related('user')

    for bet in active_bets:
        multiplier = bet.auto_cashout
        # FIX: 'active_round' does not shadow built-in round()
        winnings = Decimal(str(round(float(bet.bet_amount) * multiplier, 2)))

        user = bet.user
        user.wallet_balance += winnings
        user.save()

        bet.status = 'won'
        bet.cashout_multiplier = multiplier
        bet.winnings = winnings
        bet.cashed_out_at = timezone.now()
        bet.save()


@activated_required
def aviator_index(request):
    active_round = get_or_create_round()
    process_auto_cashouts(active_round)

    user_bet = AviatorBet.objects.filter(
        user=request.user,
        round=active_round
    ).first()

    recent_rounds = AviatorRound.objects.filter(
        status='crashed'
    ).order_by('-created_at')[:20]

    bet_history = AviatorBet.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]

    top_wins = AviatorBet.objects.filter(
        status='won'
    ).order_by('-winnings').select_related('user')[:5]

    context = {
        'current_round': active_round,
        'user_bet': user_bet,
        'recent_rounds': recent_rounds,
        'bet_history': bet_history,
        'top_wins': top_wins,
        'wallet': request.user.wallet_balance,
        'min_bet': 5,
    }
    return render(request, 'aviator/index.html', context)


@activated_required
def place_bet(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    user = request.user

    try:
        data = json.loads(request.body)
        bet_amount = Decimal(str(data.get('bet_amount', 0)))
        auto_cashout = data.get('auto_cashout')
        if auto_cashout:
            auto_cashout = float(auto_cashout)
            if auto_cashout < 1.01:
                auto_cashout = None
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid data.'})

    if bet_amount < 5:
        return JsonResponse({'success': False, 'error': 'Minimum bet is Ksh 5.'})

    if bet_amount > user.wallet_balance:
        return JsonResponse({
            'success': False,
            'error': f'Insufficient balance. Available: Ksh {user.wallet_balance}'
        })

    active_round = get_or_create_round()

    if active_round.status != 'betting':
        return JsonResponse({
            'success': False,
            'error': 'Betting is closed. Wait for next round.'
        })

    if AviatorBet.objects.filter(user=user, round=active_round).exists():
        return JsonResponse({
            'success': False,
            'error': 'You already placed a bet this round.'
        })

    user.wallet_balance -= bet_amount
    user.save()

    bet = AviatorBet.objects.create(
        user=user,
        round=active_round,
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
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    user = request.user

    # FIX: renamed to active_round so built-in round() is NOT shadowed
    active_round = AviatorRound.objects.filter(
        status='flying'
    ).order_by('-created_at').first()

    if not active_round:
        return JsonResponse({'success': False, 'error': 'No active round.'})

    bet = AviatorBet.objects.filter(
        user=user,
        round=active_round,
        status='active'
    ).first()

    if not bet:
        return JsonResponse({'success': False, 'error': 'No active bet.'})

    multiplier = active_round.current_multiplier()

    if multiplier >= active_round.crash_point:
        bet.status = 'lost'
        bet.save()
        return JsonResponse({'success': False, 'error': 'Too late! Plane crashed.'})

    # FIX: round() now correctly calls the built-in function
    winnings = Decimal(str(round(float(bet.bet_amount) * multiplier, 2)))

    user.wallet_balance += winnings
    user.save()

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
    active_round = get_or_create_round()
    if request.user.is_authenticated:
        process_auto_cashouts(active_round)

    current_mult = active_round.current_multiplier()

    data = {
        'round_id': active_round.pk,
        'status': active_round.status,
        'current_multiplier': current_mult,
        'crash_point': active_round.crash_point if active_round.status == 'crashed' else None,
        'seconds_until_fly': active_round.seconds_until_fly(),
    }

    if request.user.is_authenticated:
        bet = AviatorBet.objects.filter(
            user=request.user,
            round=active_round
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