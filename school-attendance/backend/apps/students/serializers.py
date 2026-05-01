"""
Serializers for student management.
"""

from rest_framework import serializers
from .models import Student, FaceEncoding


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for student model."""
    
    full_name = serializers.ReadOnlyField()
    today_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'first_name', 'last_name', 'full_name',
            'grade', 'date_of_birth', 'parent_email', 'photo_url', 'photo',
            'is_active', 'enrolled_since', 'created_at', 'updated_at', 'today_status'
        ]
        read_only_fields = ['id', 'enrolled_since', 'created_at', 'updated_at']
    
    def get_today_status(self, obj):
        """Get today's attendance status for the student."""
        from django.utils import timezone
        from apps.attendance.models import AttendanceRecord
        
        today = timezone.now().date()
        attendance = AttendanceRecord.objects.filter(
            student=obj,
            date=today
        ).first()
        
        if attendance:
            return {
                'status': attendance.status,
                'marked_by': attendance.marked_by,
                'timestamp': attendance.timestamp
            }
        return None
    
    def validate_student_id(self, value):
        """Ensure student_id is unique."""
        if self.instance:
            if Student.objects.filter(student_id=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("Student ID already exists")
        else:
            if Student.objects.filter(student_id=value).exists():
                raise serializers.ValidationError("Student ID already exists")
        return value


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for student list view."""
    
    full_name = serializers.ReadOnlyField()
    photo_thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'first_name', 'last_name', 'full_name',
            'grade', 'photo_thumbnail', 'is_active'
        ]
    
    def get_photo_thumbnail(self, obj):
        if obj.photo:
            return obj.photo.url
        return obj.photo_url or None


class FaceEncodingSerializer(serializers.ModelSerializer):
    """Serializer for face encoding model."""
    
    class Meta:
        model = FaceEncoding
        fields = ['id', 'student', 'encoding_vector', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class StudentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating students with optional photo."""
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'first_name', 'last_name', 'grade',
            'date_of_birth', 'parent_email', 'photo', 'is_active'
        ]
    
    def create(self, validated_data):
        """Create student and trigger face encoding task if photo provided."""
        student = super().create(validated_data)
        
        # If photo was uploaded, schedule face encoding task
        if student.photo:
            from apps.students.tasks import register_face_encodings
            register_face_encodings.delay(student.id)
        
        return student
    
    def update(self, instance, validated_data):
        """Update student and re-trigger face encoding if new photo provided."""
        photo_changed = 'photo' in validated_data and validated_data['photo']
        student = super().update(instance, validated_data)
        
        if photo_changed:
            from apps.students.tasks import register_face_encodings
            register_face_encodings.delay(student.id)
        
        return student
