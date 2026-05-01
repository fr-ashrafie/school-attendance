"""
Serializers for attendance management.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import AttendanceRecord
from apps.students.serializers import StudentListSerializer


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for attendance record."""
    
    student_info = StudentListSerializer(source='student', read_only=True)
    recorded_by_user_name = serializers.CharField(
        source='recorded_by_user.full_name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'student', 'student_info', 'timestamp', 'date',
            'status', 'marked_by', 'recorded_by_user', 'recorded_by_user_name', 'notes'
        ]
        read_only_fields = ['id', 'timestamp']


class FaceCaptureRequestSerializer(serializers.Serializer):
    """Serializer for face capture request."""
    
    image = serializers.CharField(
        required=True,
        help_text="Base64 encoded image data"
    )
    
    def validate_image(self, value):
        """Validate base64 image data."""
        import base64
        from django.conf import settings
        
        # Check if it's a valid base64 string
        try:
            if ',' in value:
                # Remove data URL prefix if present
                value = value.split(',')[1]
            
            # Decode to check validity
            decoded = base64.b64decode(value)
            
            # Check size limit
            max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
            if len(decoded) > max_size:
                raise serializers.ValidationError(
                    f"Image size exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit"
                )
            
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Invalid image data: {str(e)}")


class ManualAttendanceSerializer(serializers.Serializer):
    """Serializer for manual attendance marking."""
    
    student_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['present', 'late', 'absent'])
    date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_date(self, value):
        """Ensure date is not in the future."""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Date cannot be in the future")
        return value or timezone.now().date()
    
    def validate_student_id(self, value):
        """Ensure student exists."""
        from apps.students.models import Student
        try:
            Student.objects.get(id=value)
        except Student.DoesNotExist:
            raise serializers.ValidationError("Student does not exist")
        return value


class AttendanceStatsSerializer(serializers.Serializer):
    """Serializer for attendance statistics."""
    
    date = serializers.DateField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    total = serializers.IntegerField()
    marked = serializers.IntegerField()


class AttendanceTrendSerializer(serializers.Serializer):
    """Serializer for attendance trend data."""
    
    date = serializers.DateField()
    present = serializers.IntegerField()
    late = serializers.IntegerField()
    absent = serializers.IntegerField()
