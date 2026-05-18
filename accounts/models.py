import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


def generate_referral_code():
    return uuid.uuid4().hex[:8].upper()


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    referral_code = models.CharField(
        max_length=10, unique=True, default=generate_referral_code
    )
    referred_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='referrals'
    )
    is_activated = models.BooleanField(default=False)
    wallet_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone_number']

    def __str__(self):
        return f"{self.username} ({self.phone_number})"

    def get_total_referrals(self):
        return self.referrals.filter(is_activated=True).count()
