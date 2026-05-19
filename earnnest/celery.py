import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'earnnest.settings')

app = Celery('earnnest')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'check-matured-investments-every-30-min': {
        'task': 'investments.tasks.check_matured_investments',
        'schedule': crontab(minute='*/30'),
    },
}
