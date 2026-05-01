"""
Student and face encoding models.
"""

from django.db import models
from pgvector.django import VectorField


class Student(models.Model):
    """
    Student model with personal information and photo.
    """
    
    student_id = models.CharField(max_length=20, unique=True, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    grade = models.CharField(max_length=20, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    parent_email = models.EmailField()
    photo_url = models.URLField(blank=True, null=True)
    photo = models.ImageField(upload_to='students/photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    enrolled_since = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['grade', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class FaceEncoding(models.Model):
    """
    Face encoding vectors for facial recognition.
    Uses pgvector for efficient similarity search.
    """
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='face_encodings',
    )
    encoding_vector = VectorField(dimensions=128)  # face_recognition uses 128-d embeddings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'face_encodings'
        indexes = [
            models.Index(fields=['student', 'is_active']),
        ]
    
    def __str__(self):
        return f"Encoding for {self.student.student_id} ({self.created_at})"
    
    @classmethod
    def create_ivfflat_index(cls, lists=100):
        """
        Create IVFFlat index for faster similarity search.
        Should be called after populating encodings.
        """
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS face_encodings_ivfflat_idx
                ON face_encodings
                USING ivfflat (encoding_vector vector_cosine_ops)
                WITH (lists = {lists});
            """)
