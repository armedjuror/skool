"""
Tests for Dashboard endpoints:
  GET /api/dashboard/stats/
  GET /api/dashboard/recent-activity/
  GET /api/dashboard/notifications/
"""
from rest_framework import status
from .base import BaseAPITestCase


class DashboardStatsTests(BaseAPITestCase):

    def test_admin_can_get_stats(self):
        self.auth_admin()
        res = self.client.get('/api/dashboard/stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_teacher_can_get_stats(self):
        self.auth_teacher()
        res = self.client.get('/api/dashboard/stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        res = self.client.get('/api/dashboard/stats/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_stats_has_expected_keys(self):
        self.auth_admin()
        res = self.client.get('/api/dashboard/stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # At minimum one of these keys should be present
        data = res.data.get('data', res.data)
        possible_keys = [
            'total_students', 'total_staff', 'pending_registrations',
            'active_branches', 'students', 'staff',
        ]
        has_any = any(k in str(data) for k in possible_keys)
        self.assertTrue(has_any, f"Expected dashboard keys not found in: {data}")


class DashboardRecentActivityTests(BaseAPITestCase):

    def test_admin_can_get_activity(self):
        self.auth_admin()
        res = self.client.get('/api/dashboard/recent-activity/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        res = self.client.get('/api/dashboard/recent-activity/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class DashboardNotificationsTests(BaseAPITestCase):

    def test_admin_can_get_notifications(self):
        self.auth_admin()
        res = self.client.get('/api/dashboard/notifications/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        res = self.client.get('/api/dashboard/notifications/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
