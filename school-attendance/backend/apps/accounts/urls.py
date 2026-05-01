"""
URL patterns for accounts app.
"""

from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    UserListCreateView,
    UserDetailView,
    CurrentUserView,
)

urlpatterns = [
    # Authentication is handled in main urls.py
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
]
