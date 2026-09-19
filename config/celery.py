"""
Celery configuration for Smart Task Manager.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('smart_task_manager')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'send-task-deadline-reminders-hourly': {
        'task': 'apps.tasks.tasks.send_task_deadline_reminders',
        'schedule': crontab(minute=0),  # runs every hour at :00
    },
}
