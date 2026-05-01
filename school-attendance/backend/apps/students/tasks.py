"""
Celery tasks for students app.
"""

from celery import shared_task
from django.core.files.base import ContentFile
import base64
import logging
import numpy as np

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def register_face_encodings(self, student_id):
    """
    Compute and store face encodings for a student's photo.
    
    Args:
        student_id: ID of the student
    """
    from apps.students.models import Student, FaceEncoding
    
    try:
        student = Student.objects.get(id=student_id)
        
        if not student.photo:
            logger.warning(f"No photo found for student {student_id}")
            return
        
        # Import face recognition libraries
        import face_recognition
        from PIL import Image
        import io
        
        # Load image
        img_bytes = student.photo.read()
        image = Image.open(io.BytesIO(img_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array for face_recognition
        img_array = np.array(image)
        
        # Detect faces and compute encodings
        face_locations = face_recognition.face_locations(img_array, model='cnn')
        
        if not face_locations:
            logger.warning(f"No faces detected in photo for student {student.student_id}")
            # Try with HOG model as fallback
            face_locations = face_recognition.face_locations(img_array, model='hog')
        
        if not face_locations:
            logger.error(f"Still no faces detected for student {student.student_id}")
            return
        
        # Compute encodings for each detected face
        face_encodings = face_recognition.face_encodings(img_array, face_locations)
        
        # Deactivate old encodings
        FaceEncoding.objects.filter(student=student).update(is_active=False)
        
        # Store new encodings
        for encoding in face_encodings:
            FaceEncoding.objects.create(
                student=student,
                encoding_vector=encoding.tolist(),
                is_active=True
            )
        
        logger.info(f"Stored {len(face_encodings)} face encoding(s) for student {student.student_id}")
        
        # Create IVFFlat index if this is the first encoding
        if FaceEncoding.objects.count() > 100:
            FaceEncoding.create_ivfflat_index(lists=100)
        
    except Student.DoesNotExist:
        logger.error(f"Student {student_id} does not exist")
    except Exception as exc:
        logger.error(f"Error processing face encodings for student {student_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_inactive_encodings():
    """
    Periodic task to clean up inactive face encodings.
    Run monthly.
    """
    from apps.students.models import FaceEncoding
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted_count, _ = FaceEncoding.objects.filter(
        is_active=False,
        created_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} inactive face encodings")
    
    return deleted_count
