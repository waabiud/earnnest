from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import time


@shared_task
def run_aviator_round():
    """
    Manages the aviator game loop:
    1. Wait 10 seconds for bets
    2. Fly for crash_point duration
    3. Crash and settle bets
    4. Create new round
    """
    from .models import AviatorRound, AviatorBet
    from accounts.models import User
    from decimal import Decimal

    # Get or create waiting round
    round = AviatorRound.objects.filter(status='waiting').order_by('-created_at').first()
    if not round:
        round = AviatorRound.objects.create(status='waiting')

    # Wait 10 seconds for bets (betting phase)
    time.sleep(10)

    # Start flying
    round.status = 'flying'
    round.started_at = timezone.now()
    round.save()

    # Fly until crash
    # crash_point determines how long it flies
    # 1.00x = crashes immediately, 2.00x = flies ~2 seconds, etc
    fly_duration = min(round.crash_point * 1.5, 30)  # max 30 seconds

    # Check for auto cashouts during flight
    elapsed = 0
    interval = 0.5  # check every 0.5 seconds

    while elapsed < fly_duration:
        time.sleep(interval)
        elapsed += interval

        # Calculate current multiplier
        current_multiplier = 1.0 + (elapsed / fly_duration) * (round.crash_point - 1.0)
        current_multiplier = min(current_multiplier, round.crash_point)

        # Process auto cashouts
        active_bets = AviatorBet.objects.filter(
            round=round,
            status='active',
            auto_cashout__isnull=False,
            auto_cashout__lte=current_multiplier
        )

        for bet in active_bets:
            multiplier = bet.auto_cashout
            winnings = Decimal(str(bet.calculate_winnings(multiplier)))

            # Credit wallet
            user = bet.user
            user.wallet_balance += winnings
            user.save()

            bet.status = 'won'
            bet.cashout_multiplier = multiplier
            bet.winnings = winnings
            bet.cashed_out_at = timezone.now()
            bet.save()

    # Plane crashed!
    round.status = 'crashed'
    round.crashed_at = timezone.now()
    round.save()

    # Mark all remaining active bets as lost
    lost_bets = AviatorBet.objects.filter(round=round, status='active')
    lost_bets.update(status='lost')

    # Create next round after 5 seconds
    time.sleep(5)
    AviatorRound.objects.create(status='waiting')

    # Trigger next round
    run_aviator_round.delay()

    return f'Round #{round.pk} crashed at {round.crash_point}x'


@shared_task
def ensure_aviator_running():
    """
    Makes sure aviator game is always running.
    Runs every 5 minutes.
    """
    from .models import AviatorRound

    # Check if there's an active round
    active = AviatorRound.objects.filter(
        status__in=['waiting', 'flying']
    ).exists()

    if not active:
        run_aviator_round.delay()
        return 'Started new aviator round.'

    return 'Aviator is running.'
