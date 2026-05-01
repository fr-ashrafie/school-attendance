"""
Signals for attendance app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import AttendanceRecord


@receiver(post_save, sender=AttendanceRecord)
def invalidate_attendance_cache(sender, instance, **kwargs):
    """Invalidate attendance stats cache when record is saved."""
    cache.delete(f"attendance_stats_{instance.date}")
