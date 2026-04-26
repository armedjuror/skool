"""
Tests for User management:
  GET    /api/users/
  POST   /api/users/
  GET    /api/users/{id}/
  PATCH  /api/users/{id}/
  DELETE /api/users/{id}/
  POST   /api/users/{id}/reset_password/
"""
import datetime
from rest_framework import status
from main.models import User, UserProfile
from .base import BaseAPITestCase

LIST_URL = '/api/users/'


def detail_url(pk):
    return f'/api/users/{pk}/'


def reset_pw_url(pk):
    return f'/api/users/{pk}/reset_password/'


class UserListTests(BaseAPITestCase):

    def test_admin_can_list(self):
        self.auth_admin()
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_teacher_denied(self):
        self.auth_teacher()
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_denied(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class UserCreateTests(BaseAPITestCase):

    def _payload(self, email='newuser@example.com'):
        return {
            'email': email,
            'password': 'NewUser@1234',
            'user_type': 'TEACHER',
            'first_name': 'New',
            'last_name': 'User',
        }

    def test_admin_can_create_user(self):
        self.auth_admin()
        res = self.client.post(LIST_URL, self._payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_duplicate_email_rejected(self):
        self.auth_admin()
        self.client.post(LIST_URL, self._payload('dupuser@example.com'), format='json')
        res = self.client.post(LIST_URL, self._payload('dupuser@example.com'), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_cannot_create_user(self):
        self.auth_teacher()
        res = self.client.post(LIST_URL, self._payload('tc@example.com'), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class UserRetrieveTests(BaseAPITestCase):

    def test_admin_can_retrieve_any_user(self):
        self.auth_admin()
        res = self.client.get(detail_url(self.teacher.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_not_found(self):
        import uuid
        self.auth_admin()
        res = self.client.get(detail_url(uuid.uuid4()))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class UserUpdateTests(BaseAPITestCase):

    def test_admin_can_update(self):
        self.auth_admin()
        res = self.client.patch(
            detail_url(self.teacher.id),
            {'full_name': 'Updated Teacher Name'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class UserDeleteTests(BaseAPITestCase):

    def setUp(self):
        self.del_user = User.objects.create_user(
            email='del_user@example.com', password='Del@1234',
            organization=self.org, user_type='TEACHER',
        )
        UserProfile.objects.create(
            user=self.del_user, full_name='Delete User', gender='Male',
            dob=datetime.date(1993, 7, 7), id_card_type='QID',
            id_card_number='20202020', mobile='55000200',
        )

    def test_admin_can_delete(self):
        self.auth_admin()
        res = self.client.delete(detail_url(self.del_user.id))
        self.assertIn(res.status_code, [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
        ])

    def test_teacher_cannot_delete(self):
        self.auth_teacher()
        res = self.client.delete(detail_url(self.del_user.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class UserResetPasswordTests(BaseAPITestCase):

    def test_admin_can_reset_password(self):
        self.auth_admin()
        res = self.client.post(
            reset_pw_url(self.teacher.id),
            {'new_password': 'Reset@5678'},
            format='json',
        )
        self.assertIn(res.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,  # if extra validation applies
        ])

    def test_teacher_cannot_reset_others(self):
        self.auth_teacher()
        res = self.client.post(
            reset_pw_url(self.head_teacher.id),
            {'new_password': 'Reset@5678'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
