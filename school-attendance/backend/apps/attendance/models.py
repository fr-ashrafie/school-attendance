"""
Attendance record models.
"""

from django.db import models
from django.conf import settings
from apps.students.models import Student


class AttendanceRecord(models.Model):
    """
    Daily attendance record for students.
    
    Status options:
    - present: Student attended on time
    - late: Student arrived late
    - absent: Student was absent
    """
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('late', 'Late'),
        ('absent', 'Absent'),
    ]
    
    MARKED_BY_CHOICES = [
        ('face', 'Face Recognition'),
        ('manual', 'Manual'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='present',
    )
    marked_by = models.CharField(
        max_length=10,
        choices=MARKED_BY_CHOICES,
        default='face',
    )
    recorded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_attendance',
    )
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'attendance_records'
        ordering = ['-timestamp']
        unique_together = ['student', 'date']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.student_id} - {self.date} ({self.status})"
    
    @classmethod
    def get_today_stats(cls):
        """Get today's attendance statistics."""
        from django.utils import timezone
        from django.core.cache import cache
        
        today = timezone.now().date()
        cache_key = f"attendance_stats_{today}"
        
        # Try to get from cache
        stats = cache.get(cache_key)
        if stats:
            return stats
        
        # Calculate stats
        today_records = cls.objects.filter(date=today)
        
        total_students = Student.objects.filter(is_active=True).count()
        present = today_records.filter(status='present').count()
        late = today_records.filter(status='late').count()
        absent_count = today_records.filter(status='absent').count()
        
        # Students without records are considered absent
        marked_count = today_records.values('student_id').distinct().count()
        unmarked = total_students - marked_count
        
        stats = {
            'date': str(today),
            'present': present,
            'late': late,
            'absent': absent_count + unmarked,
            'total': total_students,
            'marked': marked_count,
        }
        
        # Cache for 60 seconds
        cache.set(cache_key, stats, timeout=60)
        
        return stats
    
    @classmethod
    def get_seven_day_trend(cls):
        """Get attendance trend for the last 7 days."""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Q
        
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        
        records = cls.objects.filter(
            date__gte=seven_days_ago,
            date__lte=today
        ).values('date').annotate(
            present=Count('id', filter=Q(status='present')),
            late=Count('id', filter=Q(status='late')),
            absent=Count('id', filter=Q(status='absent')),
        ).order_by('date')
        
        return list(records)
