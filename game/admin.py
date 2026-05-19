from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline
from .models import GameRound, GameEntry
from notifications.models import Notification


class GameEntryInline(TabularInline):
    model = GameEntry
    extra = 0
    readonly_fields = ['user', 'guess', 'entry_fee', 'status', 'created_at']


@admin.register(GameRound)
class GameRoundAdmin(ModelAdmin):
    list_display = [
        'id', 'secret_number', 'prize_pool',
        'entry_fee', 'status', 'winner', 'created_at'
    ]
    list_filter = ['status']
    inlines = [GameEntryInline]
    actions = ['reveal_winner', 'close_round']

    def reveal_winner(self, request, queryset):
        for round in queryset.filter(status='closed'):
            winning_entry = round.entries.filter(
                guess=round.secret_number,
                status='pending'
            ).first()

            if winning_entry:
                winning_entry.status = 'won'
                winning_entry.save()
                round.winner = winning_entry.user
                round.status = 'revealed'
                round.revealed_at = timezone.now()
                round.save()

                winner = winning_entry.user
                winner.wallet_balance += round.prize_pool
                winner.save()

                round.entries.exclude(pk=winning_entry.pk).update(status='lost')

                Notification.objects.create(
                    user=winner,
                    notification_type='general',
                    title='🎉 You Won the Game!',
                    message=(
                        f'Your guess {winning_entry.guess} matched! '
                        f'You won Ksh {round.prize_pool}!'
                    )
                )
            else:
                round.status = 'revealed'
                round.revealed_at = timezone.now()
                round.save()
                round.entries.filter(status='pending').update(status='lost')

        self.message_user(request, 'Round(s) revealed successfully.')
    reveal_winner.short_description = 'Reveal winner'

    def close_round(self, request, queryset):
        queryset.filter(status='open').update(status='closed')
        self.message_user(request, 'Round(s) closed.')
    close_round.short_description = 'Close round'


@admin.register(GameEntry)
class GameEntryAdmin(ModelAdmin):
    list_display = [
        'user', 'round', 'guess',
        'entry_fee', 'status', 'created_at'
    ]
    list_filter = ['status']
    search_fields = ['user__username', 'guess']
