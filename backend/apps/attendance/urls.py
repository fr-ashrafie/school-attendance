"""
URL patterns for attendance app.
"""

from django.urls import path
from .views import (
    FaceCaptureView,
    TodayAttendanceStatsView,
    AttendanceTrendView,
    StudentAttendanceHistoryView,
    ManualAttendanceView,
    RecentAttendanceView,
)

urlpatterns = [
    path('capture/', FaceCaptureView.as_view(), name='attendance-capture'),
    path('today/', TodayAttendanceStatsView.as_view(), name='attendance-today'),
    path('trend/', AttendanceTrendView.as_view(), name='attendance-trend'),
    path('student/<int:student_id>/', StudentAttendanceHistoryView.as_view(), name='student-attendance-history'),
    path('manual/', ManualAttendanceView.as_view(), name='attendance-manual'),
    path('recent/', RecentAttendanceView.as_view(), name='attendance-recent'),
]
