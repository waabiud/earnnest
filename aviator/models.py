import random
import hashlib
import hmac
from django.db import models
from django.conf import settings
from django.utils import timezone


def generate_crash_point():
    """
    Provably fair crash point generation.
    Returns a float like 1.24, 3.50, 1.00 etc.
    """
    seed = random.randint(1, 1000000)
    hash_val = hashlib.sha256(str(seed).encode()).hexdigest()
    result = int(hash_val[:8], 16)
    crash_point = max(1.0, (result % 2000) / 100 + 1.0)
    return round(crash_point, 2)


class AviatorRound(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),    # waiting for bets
        ('flying', 'Flying'),      # plane is flying
        ('crashed', 'Crashed'),    # plane crashed
    ]

    crash_point = models.FloatField(default=generate_crash_point)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='waiting'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    crashed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Round #{self.pk} - Crashed at {self.crash_point}x"

    def duration_seconds(self):
        """How long the plane flies before crash."""
        if self.started_at and self.crashed_at:
            return (self.crashed_at - self.started_at).total_seconds()
        return 0


class AviatorBet(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),      # bet placed, not cashed out
        ('won', 'Won'),            # cashed out before crash
        ('lost', 'Lost'),          # plane crashed before cashout
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
    auto_cashout = models.FloatField(null=True, blank=True)  # auto cashout multiplier
    cashout_multiplier = models.FloatField(null=True, blank=True)  # actual cashout
    winnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    cashed_out_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f"{self.user.username} - Ksh{self.bet_amount} "
            f"- {self.status} - {self.cashout_multiplier}x"
        )

    def calculate_winnings(self, multiplier):
        return round(float(self.bet_amount) * multiplier, 2)
