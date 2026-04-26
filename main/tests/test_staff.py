"""
Tests for Staff management:
  GET    /api/staffs/
  POST   /api/staffs/
  GET    /api/staffs/{id}/
  PATCH  /api/staffs/{id}/
  DELETE /api/staffs/{id}/
  POST   /api/staffs/{id}/reset-password/
"""
import datetime
from rest_framework import status
from main.models import StaffProfile, User, UserProfile
from .base import BaseAPITestCase

LIST_URL = '/api/staffs/'


def detail_url(pk):
    return f'/api/staffs/{pk}/'


def reset_pw_url(pk):
    return f'/api/staffs/{pk}/reset-password/'


class StaffListTests(BaseAPITestCase):

    def test_admin_can_list(self):
        self.auth_admin()
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_head_teacher_can_list(self):
        self.auth_head_teacher()
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class StaffCreateTests(BaseAPITestCase):

    def _payload(self, email='newstaff@example.com'):
        return {
            'email': email,
            'name': 'New Staff',
            'gender': 'Male',
            'dob': '1988-07-15',
            'id_card_type': 'QID',
            'id_card_number': '77777777',
            'mobile': '55000070',
            'user_type': 'TEACHER',
            'branch_ids': [str(self.branch.id)],
            'category': 'PERMANENT',
            'status': 'ACTIVE',
            'monthly_salary': '3000.00',
            'qatar_place': 'Doha',
            'qatar_landmark': 'Near Park',
            'qatar_building_no': '5',
            'qatar_street_no': '10',
            'qatar_zone_no': '20',
            'india_state': 'Kerala',
            'india_district': 'Thrissur',
            'india_place': 'Thrissur Town',
            'india_house_name': 'Staff House',
            'india_contact': '9876540000',
        }

    def test_admin_can_create_staff(self):
        self.auth_admin()
        res = self.client.post(LIST_URL, self._payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_duplicate_email_rejected(self):
        self.auth_admin()
        self.client.post(LIST_URL, self._payload('dup_staff@example.com'), format='json')
        res = self.client.post(LIST_URL, self._payload('dup_staff@example.com'), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_cannot_create_staff(self):
        self.auth_teacher()
        res = self.client.post(LIST_URL, self._payload('tc@example.com'), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_required_fields(self):
        self.auth_admin()
        res = self.client.post(LIST_URL, {'email': 'incomplete@example.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class StaffRetrieveTests(BaseAPITestCase):

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email='staff_ret@example.com', password='St@1234',
            organization=self.org, user_type='TEACHER',
        )
        UserProfile.objects.create(
            user=self.staff_user, full_name='Retrieve Staff', gender='Female',
            dob=datetime.date(1992, 9, 25), id_card_type='PASSPORT',
            id_card_number='PA999888', mobile='55000080',
        )
        self.staff = StaffProfile.objects.create(
            user=self.staff_user, category='PERMANENT',
            status='ACTIVE', monthly_salary='2500.00',
        )

    def test_admin_can_retrieve(self):
        self.auth_admin()
        res = self.client.get(detail_url(self.staff.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_not_found(self):
        import uuid
        self.auth_admin()
        res = self.client.get(detail_url(uuid.uuid4()))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class StaffUpdateTests(BaseAPITestCase):

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email='staff_upd@example.com', password='St@1234',
            organization=self.org, user_type='TEACHER',
        )
        UserProfile.objects.create(
            user=self.staff_user, full_name='Update Staff', gender='Male',
            dob=datetime.date(1985, 11, 11), id_card_type='QID',
            id_card_number='88888888', mobile='55000090',
        )
        self.staff = StaffProfile.objects.create(
            user=self.staff_user, category='PERMANENT',
            status='ACTIVE', monthly_salary='2800.00',
        )

    def test_admin_can_update(self):
        self.auth_admin()
        res = self.client.patch(
            detail_url(self.staff.id),
            {'category': 'TEMPORARY'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_teacher_cannot_update_others(self):
        self.auth_teacher()
        res = self.client.patch(
            detail_url(self.staff.id),
            {'category': 'TEMPORARY'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class StaffDeleteTests(BaseAPITestCase):

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email='staff_del@example.com', password='St@1234',
            organization=self.org, user_type='TEACHER',
        )
        UserProfile.objects.create(
            user=self.staff_user, full_name='Delete Staff', gender='Male',
            dob=datetime.date(1991, 3, 3), id_card_type='QID',
            id_card_number='99999999', mobile='55000091',
        )
        self.staff = StaffProfile.objects.create(
            user=self.staff_user, category='PERMANENT',
            status='ACTIVE', monthly_salary='2000.00',
        )

    def test_admin_can_delete(self):
        self.auth_admin()
        res = self.client.delete(detail_url(self.staff.id))
        self.assertIn(res.status_code, [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
        ])

    def test_teacher_cannot_delete(self):
        self.auth_teacher()
        res = self.client.delete(detail_url(self.staff.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class StaffFilterTests(BaseAPITestCase):

    def test_filter_by_status(self):
        self.auth_admin()
        res = self.client.get(LIST_URL + '?status=ACTIVE')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_filter_by_user_type(self):
        self.auth_admin()
        res = self.client.get(LIST_URL + '?user_type=TEACHER')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_filter_by_branch(self):
        self.auth_admin()
        res = self.client.get(LIST_URL + f'?branch={self.branch.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_search(self):
        self.auth_admin()
        res = self.client.get(LIST_URL + '?search=Teacher')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
