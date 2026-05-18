from django.db import models
from django.conf import settings


class Referral(models.Model):
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_records'
    )
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_record'
    )
    bonus_paid = models.BooleanField(default=False)
    bonus_amount = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referrer.username} → {self.referred_user.username} (Ksh {self.bonus_amount})"
