import random
from django.db import models
from django.conf import settings


def generate_secret_number():
    """Generate a random 4-digit number as string e.g. '4729'"""
    return str(random.randint(1000, 9999))


class GameRound(models.Model):
    """Each game round has a secret number. Admin controls when it's active."""
    STATUS_CHOICES = [
        ('open', 'Open'),       # accepting entries
        ('closed', 'Closed'),   # no more entries
        ('revealed', 'Revealed'), # winner announced
    ]

    secret_number = models.CharField(max_length=4, default=generate_secret_number)
    prize_pool = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='won_rounds'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    revealed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Round #{self.pk} - {self.status} - Prize: Ksh {self.prize_pool}"

    def add_to_pool(self, amount):
        self.prize_pool += amount
        self.save()


class GameEntry(models.Model):
    """A user's guess in a game round."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_entries'
    )
    round = models.ForeignKey(
        GameRound,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    guess = models.CharField(max_length=4)
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment = models.OneToOneField(
        'payments.Payment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='game_entry'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # One guess per user per round
        unique_together = ['user', 'round']

    def __str__(self):
        return f"{self.user.username} guessed {self.guess} in Round #{self.round.pk} - {self.status}"
