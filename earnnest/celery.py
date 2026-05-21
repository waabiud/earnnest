import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'earnnest.settings')

app = Celery('earnnest')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Check matured investments every 30 minutes
    'check-matured-investments': {
        'task': 'investments.tasks.check_matured_investments',
        'schedule': crontab(minute='*/30'),
    },
    # Auto close game rounds after 24 hours
    'auto-close-game-rounds': {
        'task': 'game.tasks.auto_close_game_round',
        'schedule': crontab(minute='*/30'),
    },
    # Auto reveal game winners
    'auto-reveal-game-winners': {
        'task': 'game.tasks.auto_reveal_game_winner',
        'schedule': crontab(minute='*/30'),
    },
    # Ensure open game round always exists
    'ensure-open-round': {
        'task': 'game.tasks.ensure_open_round',
        'schedule': crontab(minute='*/30'),
    },
    # Daily notifications at 8AM Nairobi
    'daily-notifications': {
        'task': 'notifications.tasks.send_daily_notifications',
        'schedule': crontab(hour=8, minute=0),
    },
    # Investment reminder at 12PM daily
    'investment-reminder': {
        'task': 'notifications.tasks.send_investment_reminder',
        'schedule': crontab(hour=12, minute=0),
    },
    # Referral reminder every 3 days at 10AM
    'referral-reminder': {
        'task': 'notifications.tasks.send_referral_reminder',
        'schedule': crontab(hour=10, minute=0, day_of_week='1,4'),
    },
}
