"""
Celery configuration for Face Recognition Attendance System.
"""

from celery import Celery
from celery.schedules import crontab

app = Celery('school_attendance')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'check-daily-absences': {
        'task': 'apps.attendance.tasks.check_daily_absences',
        'schedule': crontab(hour=10, minute=0),  # Daily at 10 AM
    },
    'generate-monthly-reports': {
        'task': 'apps.reports.tasks.generate_monthly_report',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # Monthly on 1st
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
