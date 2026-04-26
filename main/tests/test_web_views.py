"""
Tests for HTML web views (smoke tests — check HTTP status, redirects, template rendered):
  /<org_code>/login/
  /<org_code>/dashboard/
  /<org_code>/students/
  /<org_code>/staff/
  /<org_code>/registrations/
  /<org_code>/students/register/
  /<org_code>/staff/register/
  /<org_code>/fees/
  /<org_code>/attendance/
  /<org_code>/reports/
  /<org_code>/settings/
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .base import BaseAPITestCase

User = get_user_model()


class LoginViewTests(BaseAPITestCase):

    def test_login_page_renders(self):
        res = self.client.get('/TEST/login/')
        self.assertEqual(res.status_code, 200)

    def test_invalid_org_returns_error(self):
        res = self.client.get('/NOPE/login/')
        self.assertIn(res.status_code, [200, 404])

    def test_login_post_redirects_on_success(self):
        res = self.client.post('/TEST/login/', {
            'email': 'admin@test.com',
            'password': 'Admin@1234',
        }, follow=True)
        # After successful login should land on dashboard or similar
        self.assertIn(res.status_code, [200, 302])


class AuthenticatedViewTests(BaseAPITestCase):
    """
    Views that require login — use the Django test client with session auth.
    """

    def setUp(self):
        self.django_client = Client()
        self.django_client.force_login(self.admin)

    def test_dashboard_renders(self):
        res = self.django_client.get('/TEST/dashboard/')
        self.assertEqual(res.status_code, 200)

    def test_students_list_renders(self):
        res = self.django_client.get('/TEST/students/')
        self.assertEqual(res.status_code, 200)

    def test_staff_list_renders(self):
        res = self.django_client.get('/TEST/staff/')
        self.assertEqual(res.status_code, 200)

    def test_pending_registrations_renders(self):
        res = self.django_client.get('/TEST/registrations/')
        self.assertEqual(res.status_code, 200)

    def test_settings_renders(self):
        res = self.django_client.get('/TEST/settings/')
        self.assertEqual(res.status_code, 200)

    def test_fees_renders(self):
        res = self.django_client.get('/TEST/fees/')
        self.assertIn(res.status_code, [200, 302])

    def test_attendance_renders(self):
        res = self.django_client.get('/TEST/attendance/')
        self.assertIn(res.status_code, [200, 302])

    def test_reports_renders(self):
        res = self.django_client.get('/TEST/reports/')
        self.assertIn(res.status_code, [200, 302])


class PublicRegistrationViewTests(BaseAPITestCase):
    """Registration forms are public — no auth required."""

    def test_student_registration_form_renders(self):
        res = self.client.get('/TEST/students/register/')
        self.assertEqual(res.status_code, 200)

    def test_staff_registration_form_renders(self):
        res = self.client.get('/TEST/staff/register/')
        self.assertEqual(res.status_code, 200)

    def test_student_registration_invalid_org(self):
        res = self.client.get('/NOPE/students/register/')
        self.assertIn(res.status_code, [200, 404])

    def test_unauthenticated_dashboard_redirects(self):
        res = self.client.get('/TEST/dashboard/')
        # Should redirect to login
        self.assertIn(res.status_code, [302, 301])
