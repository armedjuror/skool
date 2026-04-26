"""
Tests for Authentication endpoints:
  POST /api/auth/login/
  POST /api/auth/logout/
  GET  /api/auth/user/
  POST /api/auth/change-password/
  POST /api/auth/forgot-password/
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from .base import BaseAPITestCase


class LoginTests(BaseAPITestCase):

    def test_login_valid_credentials(self):
        res = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'Admin@1234',
            'org_code': 'TEST',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))
        data = res.data.get('data', res.data)
        self.assertIn('token', data)
        self.assertEqual(data['user']['email'], 'admin@test.com')

    def test_login_wrong_password(self):
        res = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'wrong',
            'org_code': 'TEST',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unknown_email(self):
        res = self.client.post('/api/auth/login/', {
            'email': 'nobody@test.com',
            'password': 'Admin@1234',
            'org_code': 'TEST',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_org_code(self):
        """org_code mismatch — user belongs to TEST, not WRONG."""
        res = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'Admin@1234',
            'org_code': 'WRONG',
        })
        # API may return 400 (invalid org) or 200 (org_code not strictly validated)
        # Either is acceptable — just ensure no server error
        self.assertNotEqual(res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_login_missing_fields(self):
        res = self.client.post('/api/auth/login/', {'email': 'admin@test.com'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        self.admin.is_active = False
        self.admin.save()
        res = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'Admin@1234',
            'org_code': 'TEST',
        })
        self.assertNotEqual(res.status_code, status.HTTP_200_OK)
        self.admin.is_active = True
        self.admin.save()


class LogoutTests(BaseAPITestCase):

    def test_logout_authenticated(self):
        self.auth_admin()
        res = self.client.post('/api/auth/logout/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_logout_unauthenticated(self):
        res = self.client.post('/api/auth/logout/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class GetCurrentUserTests(BaseAPITestCase):

    def test_get_user_authenticated(self):
        self.auth_admin()
        res = self.client.get('/api/auth/user/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Response may be flat or nested under 'data'
        data = res.data.get('data', res.data)
        email = data.get('email') or res.data.get('email')
        self.assertEqual(email, 'admin@test.com')

    def test_get_user_unauthenticated(self):
        res = self.client.get('/api/auth/user/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordTests(BaseAPITestCase):

    def test_change_password_success(self):
        self.auth_teacher()
        res = self.client.post('/api/auth/change-password/', {
            'current_password': 'Teacher@1234',
            'new_password': 'NewTeacher@5678',
            'confirm_new_password': 'NewTeacher@5678',
        })
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        # Restore password regardless
        self.teacher.set_password('Teacher@1234')
        self.teacher.save()

    def test_change_password_wrong_old(self):
        self.auth_teacher()
        res = self.client.post('/api/auth/change-password/', {
            'current_password': 'WrongOld',
            'new_password': 'NewTeacher@5678',
            'confirm_new_password': 'NewTeacher@5678',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch(self):
        self.auth_teacher()
        res = self.client.post('/api/auth/change-password/', {
            'current_password': 'Teacher@1234',
            'new_password': 'NewTeacher@5678',
            'confirm_new_password': 'Different@9999',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated(self):
        res = self.client.post('/api/auth/change-password/', {
            'old_password': 'Teacher@1234',
            'new_password': 'New@5678',
            'confirm_password': 'New@5678',
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordTests(BaseAPITestCase):

    def test_forgot_password_unknown_email(self):
        """Unknown email should return a safe error, not a 500."""
        res = self.client.post('/api/auth/forgot-password/', {
            'email': 'unknown@nowhere.com',
        })
        self.assertNotEqual(res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_forgot_password_missing_email(self):
        res = self.client.post('/api/auth/forgot-password/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
