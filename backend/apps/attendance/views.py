"""
Views for attendance management.
"""

import base64
import io
import logging
import numpy as np
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import AttendanceRecord
from .serializers import (
    AttendanceRecordSerializer,
    FaceCaptureRequestSerializer,
    ManualAttendanceSerializer,
    AttendanceStatsSerializer,
)
from apps.students.models import Student, FaceEncoding

logger = logging.getLogger(__name__)


class IsTeacherOrAdmin(permissions.BasePermission):
    """Permission class for teachers and admins."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role in ['admin', 'teacher']
        )


class FaceCaptureView(views.APIView):
    """
    Capture face and mark attendance using facial recognition.
    
    Accepts base64 encoded image, detects face, matches against stored
    encodings using pgvector cosine similarity, and creates attendance record.
    """
    
    permission_classes = [IsTeacherOrAdmin]
    
    def post(self, request):
        serializer = FaceCaptureRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Decode image
            image_data = serializer.validated_data['image']
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            img_bytes = base64.b64decode(image_data)
            
            # Import face recognition
            import face_recognition
            from PIL import Image
            
            # Load image
            image = Image.open(io.BytesIO(img_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            img_array = np.array(image)
            
            # Detect faces
            face_locations = face_recognition.face_locations(img_array, model='hog')
            
            if not face_locations:
                return Response(
                    {'error': 'No face detected in the image'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(img_array, face_locations)
            
            if not face_encodings:
                return Response(
                    {'error': 'Could not compute face encoding'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            query_encoding = face_encodings[0]
            
            # Search for matching encodings using pgvector
            # Using cosine distance (<=>) with threshold of 0.5
            from django.db.models import F
            from pgvector.django import CosineDistance
            
            tolerance = 0.5  # Lower is stricter matching
            
            matches = FaceEncoding.objects.filter(
                is_active=True
            ).annotate(
                distance=CosineDistance('encoding_vector', query_encoding.tolist())
            ).filter(
                distance__lt=tolerance
            ).select_related('student').order_by('distance')[:3]
            
            if not matches:
                return Response(
                    {
                        'success': False,
                        'error': 'No matching student found',
                        'confidence': 0.0
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get best match
            best_match = matches.first()
            confidence = 1.0 - best_match.distance
            
            student = best_match.student
            
            # Check if already marked today
            today = timezone.now().date()
            existing_record = AttendanceRecord.objects.filter(
                student=student,
                date=today
            ).first()
            
            if existing_record:
                return Response({
                    'success': True,
                    'message': 'Attendance already marked today',
                    'student': {
                        'id': student.id,
                        'student_id': student.student_id,
                        'first_name': student.first_name,
                        'last_name': student.last_name,
                        'grade': student.grade,
                    },
                    'attendance': AttendanceRecordSerializer(existing_record).data,
                    'confidence': float(confidence),
                    'already_marked': True
                })
            
            # Determine status based on time (late if after 9:00 AM)
            current_hour = timezone.now().hour
            status_value = 'late' if current_hour >= 9 else 'present'
            
            # Create attendance record
            record = AttendanceRecord.objects.create(
                student=student,
                date=today,
                status=status_value,
                marked_by='face',
            )
            
            # Invalidate cache
            cache.delete(f"attendance_stats_{today}")
            
            # Broadcast via WebSocket
            self.broadcast_attendance_update(student, record)
            
            return Response({
                'success': True,
                'student': {
                    'id': student.id,
                    'student_id': student.student_id,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'grade': student.grade,
                },
                'attendance': AttendanceRecordSerializer(record).data,
                'confidence': float(confidence),
                'already_marked': False
            })
            
        except Exception as e:
            logger.error(f"Error processing face capture: {e}")
            return Response(
                {'error': 'Failed to process image'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def broadcast_attendance_update(self, student, record):
        """Broadcast attendance update via WebSocket."""
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'attendance',
                {
                    'type': 'new_attendance',
                    'data': {
                        'student': {
                            'id': student.id,
                            'student_id': student.student_id,
                            'full_name': student.full_name,
                            'grade': student.grade,
                        },
                        'attendance': {
                            'id': record.id,
                            'status': record.status,
                            'timestamp': record.timestamp.isoformat(),
                        },
                        'dashboard_stats': AttendanceRecord.get_today_stats()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting attendance update: {e}")


class TodayAttendanceStatsView(views.APIView):
    """Get today's attendance statistics."""
    
    permission_classes = [IsTeacherOrAdmin]
    
    def get(self, request):
        stats = AttendanceRecord.get_today_stats()
        serializer = AttendanceStatsSerializer(stats)
        return Response(serializer.data)


class AttendanceTrendView(views.APIView):
    """Get 7-day attendance trend."""
    
    permission_classes = [IsTeacherOrAdmin]
    
    def get(self, request):
        trend = AttendanceRecord.get_seven_day_trend()
        return Response(trend)


class StudentAttendanceHistoryView(generics.ListAPIView):
    """Get attendance history for a specific student."""
    
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsTeacherOrAdmin]
    
    def get_queryset(self):
        student_id = self.kwargs['student_id']
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        
        queryset = AttendanceRecord.objects.filter(
            student_id=student_id
        ).select_related('student', 'recorded_by_user').order_by('-date')
        
        if month and year:
            queryset = queryset.filter(
                date__month=month,
                date__year=year
            )
        
        return queryset


class ManualAttendanceView(views.APIView):
    """Manually mark attendance for a student."""
    
    permission_classes = [IsTeacherOrAdmin]
    
    def post(self, request):
        serializer = ManualAttendanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.students.models import Student
        
        student = Student.objects.get(id=serializer.validated_data['student_id'])
        date = serializer.validated_data['date']
        
        # Check if already marked
        existing = AttendanceRecord.objects.filter(
            student=student,
            date=date
        ).first()
        
        if existing:
            # Update existing record
            existing.status = serializer.validated_data['status']
            existing.marked_by = 'manual'
            existing.recorded_by_user = request.user
            existing.notes = serializer.validated_data.get('notes', '')
            existing.save()
            record = existing
        else:
            # Create new record
            record = AttendanceRecord.objects.create(
                student=student,
                date=date,
                status=serializer.validated_data['status'],
                marked_by='manual',
                recorded_by_user=request.user,
                notes=serializer.validated_data.get('notes', ''),
            )
        
        # Invalidate cache
        cache.delete(f"attendance_stats_{date}")
        
        # Broadcast update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'attendance',
            {
                'type': 'new_attendance',
                'data': {
                    'student': {
                        'id': student.id,
                        'student_id': student.student_id,
                        'full_name': student.full_name,
                    },
                    'dashboard_stats': AttendanceRecord.get_today_stats()
                }
            }
        )
        
        return Response({
            'success': True,
            'attendance': AttendanceRecordSerializer(record).data
        })


class RecentAttendanceView(generics.ListAPIView):
    """Get recent attendance records for dashboard."""
    
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsTeacherOrAdmin]
    
    def get_queryset(self):
        today = timezone.now().date()
        return AttendanceRecord.objects.filter(
            date=today
        ).select_related('student').order_by('-timestamp')[:20]
