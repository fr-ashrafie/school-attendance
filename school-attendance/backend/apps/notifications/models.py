"""
Notification models for absence alerts and system messages.
"""

from django.db import models
from apps.students.models import Student


class Notification(models.Model):
    """
    In-app and email notifications for absences, late arrivals, and reminders.
    """
    
    TYPE_CHOICES = [
        ('absence', 'Absence'),
        ('late', 'Late'),
        ('reminder', 'Reminder'),
        ('system', 'System'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('in_app', 'In-App'),
        ('both', 'Both'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )
    message = models.TextField()
    sent_to = models.EmailField(help_text="Recipient email address")
    channel = models.CharField(
        max_length=10,
        choices=CHANNEL_CHOICES,
        default='in_app',
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['is_read', '-sent_at']),
            models.Index(fields=['student', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.type} - {self.student.student_id if self.student else 'System'} ({self.sent_at})"
    
    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
    
    @classmethod
    def get_unread_count(cls):
        """Get total unread notification count."""
        return cls.objects.filter(is_read=False).count()
    
    @classmethod
    def get_user_notifications(cls, student_id=None, limit=50):
        """Get notifications for a specific student or all."""
        queryset = cls.objects.all()
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset[:limit]
