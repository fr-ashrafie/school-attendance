"""
Views for student management.
"""

from rest_framework import generics, filters, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.core.cache import cache
from .models import Student, FaceEncoding
from .serializers import (
    StudentSerializer,
    StudentListSerializer,
    StudentCreateUpdateSerializer,
)


class IsTeacherOrAdmin(permissions.BasePermission):
    """Permission class for teachers and admins."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role in ['admin', 'teacher']
        )


class StudentListView(generics.ListAPIView):
    """
    List and search students with filtering.
    Supports search by name or student_id, and grade filtering.
    """
    
    queryset = Student.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['grade', 'is_active']
    search_fields = ['first_name', 'last_name', 'student_id']
    ordering_fields = ['last_name', 'first_name', 'created_at', 'student_id']
    ordering = ['last_name', 'first_name']
    permission_classes = [IsTeacherOrAdmin]
    
    def get_serializer_class(self):
        return StudentListSerializer
    
    def list(self, request, *args, **kwargs):
        # Check cache for search results
        cache_key = f"students_list_{request.query_params.urlencode()}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        response = super().list(request, *args, **kwargs)
        
        # Cache for 5 minutes
        cache.set(cache_key, response.data, timeout=300)
        
        return response


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update, or delete a specific student.
    Includes attendance summary.
    """
    
    queryset = Student.objects.all()
    permission_classes = [IsTeacherOrAdmin]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StudentCreateUpdateSerializer
        return StudentSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Add attendance summary
        from apps.attendance.models import AttendanceRecord
        from django.utils import timezone
        
        today = timezone.now().date()
        
        # This month's stats
        this_month = today.replace(day=1)
        monthly_attendance = AttendanceRecord.objects.filter(
            student=instance,
            date__gte=this_month
        )
        
        summary = {
            'total_days': monthly_attendance.count(),
            'present': monthly_attendance.filter(status='present').count(),
            'absent': monthly_attendance.filter(status='absent').count(),
            'late': monthly_attendance.filter(status='late').count(),
        }
        
        # Calculate percentage
        if summary['total_days'] > 0:
            summary['attendance_percentage'] = round(
                (summary['present'] / summary['total_days']) * 100, 2
            )
        else:
            summary['attendance_percentage'] = 0.0
        
        data = serializer.data
        data['attendance_summary'] = summary
        
        return Response(data)


class StudentCreateView(generics.CreateAPIView):
    """Create a new student."""
    
    queryset = Student.objects.all()
    serializer_class = StudentCreateUpdateSerializer
    permission_classes = [IsTeacherOrAdmin]


class StudentProfileView(APIView):
    """
    Get detailed student profile with complete attendance history.
    """
    
    permission_classes = [IsTeacherOrAdmin]
    
    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StudentSerializer(student)
        
        # Get face encoding status
        has_encodings = FaceEncoding.objects.filter(
            student=student,
            is_active=True
        ).exists()
        
        data = serializer.data
        data['has_face_encodings'] = has_encodings
        
        return Response(data)
