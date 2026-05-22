import hashlib
import random
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

ROUND_DURATION = 30
BETTING_DURATION = 10


def generate_crash_point():
    seed = random.randint(1, 10000000)
    h = hashlib.sha256(str(seed).encode()).hexdigest()
    val = int(h[:8], 16) / 0xFFFFFFFF
    crash = 1.0 / (1.0 - val * 0.99)
    crash = min(crash, 100.0)
    return round(crash, 2)


class AviatorRound(models.Model):
    STATUS_CHOICES = [
        ('betting', 'Betting'),
        ('flying', 'Flying'),
        ('crashed', 'Crashed'),
    ]

    crash_point = models.FloatField(default=generate_crash_point)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='betting')
    betting_ends_at = models.DateTimeField(null=True, blank=True)
    flying_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            now = timezone.now()
            self.betting_ends_at = now + timedelta(seconds=BETTING_DURATION)
            fly_time = min(self.crash_point * 2, ROUND_DURATION)
            self.flying_ends_at = self.betting_ends_at + timedelta(seconds=fly_time)
        super().save(*args, **kwargs)

    def current_multiplier(self):
        now = timezone.now()
        if self.status == 'betting':
            return 1.0
        if self.status == 'crashed':
            return self.crash_point
        if self.betting_ends_at and self.flying_ends_at:
            elapsed = (now - self.betting_ends_at).total_seconds()
            total = (self.flying_ends_at - self.betting_ends_at).total_seconds()
            if total > 0:
                progress = min(elapsed / total, 1.0)
                # FIX: exponential growth instead of linear
                mult = 1.0 * (self.crash_point ** progress)
                return round(min(mult, self.crash_point), 2)
        return 1.0

    def seconds_until_fly(self):
        if self.betting_ends_at:
            diff = (self.betting_ends_at - timezone.now()).total_seconds()
            return max(0, round(diff, 1))
        return 0

    def __str__(self):
        return f"Round #{self.pk} - {self.crash_point}x - {self.status}"


class AviatorBet(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='aviator_bets'
    )
    round = models.ForeignKey(
        AviatorRound,
        on_delete=models.CASCADE,
        related_name='bets'
    )
    bet_amount = models.DecimalField(max_digits=10, decimal_places=2)
    auto_cashout = models.FloatField(null=True, blank=True)
    cashout_multiplier = models.FloatField(null=True, blank=True)
    winnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    cashed_out_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Ksh{self.bet_amount} - {self.status}"