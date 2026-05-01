"""
Attendance tracking app.
"""

from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.attendance'
    verbose_name = 'Attendance'
    
    def ready(self):
        # Import signals
        import apps.attendance.signals
