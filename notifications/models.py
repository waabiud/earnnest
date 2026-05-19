from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('investment_matured', 'Investment Matured'),
        ('withdrawal_approved', 'Withdrawal Approved'),
        ('withdrawal_rejected', 'Withdrawal Rejected'),
        ('referral_bonus', 'Referral Bonus'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
