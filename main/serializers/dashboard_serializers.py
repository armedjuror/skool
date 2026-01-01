"""
Dashboard Serializers

This module contains serializers for dashboard-related data:
- Dashboard statistics
- Recent activity feed
- Notifications
"""

from rest_framework import serializers


class DashboardStatsSerializer(serializers.Serializer):
    """
    Serializer for dashboard statistics response.
    """
    students = serializers.DictField()
    staff = serializers.DictField()
    registrations = serializers.DictField()
    fees = serializers.DictField()
    attendance = serializers.DictField()


class RecentActivitySerializer(serializers.Serializer):
    """
    Serializer for recent activity items.
    """
    id = serializers.UUIDField()
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    timestamp = serializers.DateTimeField()
    user = serializers.CharField()
    icon = serializers.CharField()
    color = serializers.CharField()


class NotificationSerializer(serializers.Serializer):
    """
    Serializer for user notifications.
    """
    id = serializers.UUIDField()
    type = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    created_at = serializers.DateTimeField()
    is_read = serializers.BooleanField()
    action_url = serializers.CharField(allow_null=True, required=False)
