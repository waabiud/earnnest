import random
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def generate_secret_number():
    return str(random.randint(1000, 9999))


class GameRound(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('revealed', 'Revealed'),
    ]

    secret_number = models.CharField(max_length=4, default=generate_secret_number)
    prize_pool = models.DecimalField(max_digits=12, decimal_places=2, default=100.00)
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='won_rounds'
    )
    closes_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revealed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.closes_at:
            self.closes_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def time_remaining(self):
        if self.closes_at and self.status == 'open':
            remaining = self.closes_at - timezone.now()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return f'{hours}h {minutes}m'
        return '0h 0m'

    def __str__(self):
        return f"Round #{self.pk} - {self.status} - Prize: Ksh {self.prize_pool}"

    def add_to_pool(self, amount):
        self.prize_pool += amount
        self.save()


class GameEntry(models.Model):
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
        unique_together = ['user', 'round']

    def __str__(self):
        return f"{self.user.username} guessed {self.guess} - {self.status}"
