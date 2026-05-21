from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import random


def generate_secret_number():
    return str(random.randint(1000, 9999))


@shared_task
def create_new_game_round():
    """
    Creates a new game round automatically.
    Runs after each round is revealed.
    """
    from .models import GameRound

    # Don't create if there's already an open round
    if GameRound.objects.filter(status='open').exists():
        return 'Open round already exists.'

    round = GameRound.objects.create(
        secret_number=generate_secret_number(),
        entry_fee=50,
        prize_pool=100,
        status='open',
    )
    return f'New round #{round.pk} created with secret {round.secret_number}'


@shared_task
def auto_close_game_round():
    """
    Closes rounds that have been open for 24 hours.
    Runs every 30 minutes.
    """
    from .models import GameRound

    cutoff = timezone.now() - timedelta(hours=24)
    rounds = GameRound.objects.filter(
        status='open',
        created_at__lte=cutoff
    )

    count = 0
    for round in rounds:
        round.status = 'closed'
        round.save()
        count += 1

        # Immediately trigger reveal
        auto_reveal_game_winner.delay(round.pk)

    return f'Closed {count} rounds.'


@shared_task
def auto_reveal_game_winner(round_id=None):
    """
    Reveals winner for a specific round or all closed rounds.
    Runs every 30 minutes.
    """
    from .models import GameRound, GameEntry
    from notifications.models import Notification

    if round_id:
        rounds = GameRound.objects.filter(pk=round_id, status='closed')
    else:
        rounds = GameRound.objects.filter(status='closed')

    for round in rounds:
        # Find exact match
        winning_entry = round.entries.filter(
            guess=round.secret_number,
            status='pending'
        ).first()

        if winning_entry:
            # Mark winner
            winning_entry.status = 'won'
            winning_entry.save()

            round.winner = winning_entry.user
            round.status = 'revealed'
            round.revealed_at = timezone.now()
            round.save()

            # Credit prize pool to winner wallet
            winner = winning_entry.user
            winner.wallet_balance += round.prize_pool
            winner.save()

            # Mark all losers
            round.entries.exclude(pk=winning_entry.pk).update(status='lost')

            # Notify winner
            Notification.objects.create(
                user=winner,
                notification_type='general',
                title='🎉 You Won the Game!',
                message=(
                    f'Your guess {winning_entry.guess} matched the secret '
                    f'number {round.secret_number} in Round #{round.pk}! '
                    f'You won Ksh {round.prize_pool}! '
                    f'Funds have been credited to your wallet.'
                )
            )

            # Notify losers
            for entry in round.entries.filter(status='lost'):
                Notification.objects.create(
                    user=entry.user,
                    notification_type='general',
                    title=f'Round #{round.pk} Revealed',
                    message=(
                        f'Secret number was {round.secret_number}. '
                        f'Your guess was {entry.guess}. '
                        f'{winner.username} won Ksh {round.prize_pool}! '
                        f'Try again in the next round!'
                    )
                )

        else:
            # No winner
            round.status = 'revealed'
            round.revealed_at = timezone.now()
            round.save()
            round.entries.filter(status='pending').update(status='lost')

            # Notify all participants
            for entry in round.entries.all():
                Notification.objects.create(
                    user=entry.user,
                    notification_type='general',
                    title=f'No Winner - Round #{round.pk}',
                    message=(
                        f'Round #{round.pk} ended with no winner. '
                        f'Secret number was {round.secret_number}. '
                        f'Your guess was {entry.guess}. '
                        f'A new round has started — try again!'
                    )
                )

        # Start a new round immediately after reveal
        create_new_game_round.delay()

    return f'Revealed {rounds.count()} rounds.'


@shared_task
def ensure_open_round():
    """
    Makes sure there's always an open game round.
    Runs every 30 minutes.
    """
    from .models import GameRound

    if not GameRound.objects.filter(status='open').exists():
        create_new_game_round.delay()
        return 'Created new round — none was open.'

    return 'Open round exists.'
