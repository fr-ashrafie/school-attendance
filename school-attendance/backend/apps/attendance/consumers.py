"""
WebSocket consumers for real-time updates.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class AttendanceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time attendance updates.
    
    Authentication via JWT token in query parameter.
    Joins 'attendance' group to receive broadcasts.
    """
    
    async def connect(self):
        """Authenticate and accept connection."""
        try:
            # Get token from query params
            token = self.scope['query_string'].decode()
            token = token.replace('token=', '')
            
            if not token:
                await self.close()
                return
            
            # Validate token
            user = await self.get_user_from_token(token)
            if not user:
                await self.close()
                return
            
            self.user = user
            
            # Join attendance group
            self.group_name = 'attendance'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send welcome message with unread notification count
            unread_count = await self.get_unread_notifications()
            await self.send(json.dumps({
                'type': 'connected',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                },
                'unread_notifications': unread_count,
            }))
            
            logger.info(f"WebSocket connected for user {user.email}")
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Leave attendance group."""
        try:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for user {self.user.email}")
        except Exception as e:
            logger.error(f"WebSocket disconnection error: {e}")
    
    async def new_attendance(self, event):
        """Handle new attendance broadcast."""
        await self.send(json.dumps({
            'type': 'new_attendance',
            **event['data']
        }))
    
    async def notification(self, event):
        """Handle notification broadcast."""
        await self.send(json.dumps({
            'type': 'notification',
            **event['data']
        }))
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """Get user from JWT token."""
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id, is_active=True)
        except Exception:
            return None
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """Get count of unread notifications for user."""
        from apps.notifications.models import Notification
        
        # For admin/teacher, show all unread notifications
        if self.user.role == 'admin':
            return Notification.objects.filter(is_read=False).count()
        
        return 0
