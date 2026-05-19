from django.db import models
from django.conf import settings


class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('activation', 'Account Activation'),
        ('topup', 'Wallet Top Up'),
        ('investment', 'Investment'),
        ('game', 'Game Entry'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    reference = models.CharField(max_length=100, unique=True)     # our internal ref
    transaction_id = models.CharField(max_length=100, blank=True) # mpesa transaction id
    checkout_request_id = models.CharField(max_length=100, blank=True) # codian/mpesa id
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.payment_type} - {self.status} - Ksh{self.amount}"
