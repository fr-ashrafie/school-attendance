"""
Celery tasks for attendance app.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_daily_absences():
    """
    Check for students without attendance records and mark them as absent.
    Creates notifications for absent students.
    
    Scheduled to run at 10:00 AM daily.
    """
    from apps.students.models import Student
    from apps.attendance.models import AttendanceRecord
    from apps.notifications.models import Notification
    
    today = timezone.now().date()
    
    # Get all active students
    all_students = Student.objects.filter(is_active=True)
    
    # Get students who already have attendance records today
    marked_students = AttendanceRecord.objects.filter(
        date=today
    ).values_list('student_id', flat=True)
    
    # Find absent students
    absent_students = all_students.exclude(id__in=marked_students)
    
    absences_created = 0
    notifications_created = 0
    
    for student in absent_students:
        # Create absence record
        AttendanceRecord.objects.create(
            student=student,
            date=today,
            status='absent',
            marked_by='manual',
            notes='Marked absent by automated daily check',
        )
        absences_created += 1
        
        # Create notification
        Notification.objects.create(
            student=student,
            type='absence',
            message=f"{student.full_name} was marked absent on {today}",
            sent_to=student.parent_email,
            channel='email',
        )
        notifications_created += 1
        
        # TODO: Send email notification
        # send_absence_email.delay(student.id, today)
    
    logger.info(f"Marked {absences_created} students as absent, created {notifications_created} notifications")
    
    return {
        'absences_marked': absences_created,
        'notifications_created': notifications_created,
    }


@shared_task
def send_absence_email(student_id, date):
    """
    Send absence notification email to parent.
    """
    from apps.students.models import Student
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        student = Student.objects.get(id=student_id)
        
        subject = f"Absence Notification - {student.full_name}"
        message = f"""
Dear Parent/Guardian,

This is to inform you that {student.full_name} (Student ID: {student.student_id}) 
was marked absent on {date}.

If you believe this is an error, please contact the school administration.

Best regards,
School Administration
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [student.parent_email],
            fail_silently=False,
        )
        
        logger.info(f"Sent absence email for {student.student_id}")
        
    except Exception as e:
        logger.error(f"Error sending absence email: {e}")


@shared_task
def cleanup_old_attendance_records(days=365):
    """
    Archive or cleanup old attendance records.
    Run monthly.
    """
    from .models import AttendanceRecord
    from django.utils import timezone
    
    cutoff_date = timezone.now().date() - timedelta(days=days)
    
    # Just log count, don't delete by default
    old_count = AttendanceRecord.objects.filter(date__lt=cutoff_date).count()
    
    logger.info(f"Found {old_count} attendance records older than {cutoff_date}")
    
    # Uncomment to actually delete
    # deleted, _ = AttendanceRecord.objects.filter(date__lt=cutoff_date).delete()
    # logger.info(f"Deleted {deleted} old attendance records")
    
    return old_count
