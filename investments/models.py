from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Investment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('matured', 'Matured'),
        ('withdrawn', 'Withdrawn'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='investments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    payment = models.OneToOneField(
        'payments.Payment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investment'
    )
    maturity_date = models.DateTimeField()
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            hours = settings.INVESTMENT_MATURITY_HOURS
            self.maturity_date = timezone.now() + timedelta(hours=hours)
            rate = settings.INVESTMENT_RETURN_PERCENT / 100
            self.profit = round(self.amount * rate, 2)
        super().save(*args, **kwargs)

    def is_matured(self):
        return timezone.now() >= self.maturity_date

    def total_return(self):
        return self.amount + self.profit

    def __str__(self):
        return f"{self.user.username} - Ksh{self.amount} ({self.status})"
