"""
Tests for Student management (admin CRUD):
  GET    /api/students/
  POST   /api/students/
  GET    /api/students/{id}/
  PATCH  /api/students/{id}/
  DELETE /api/students/{id}/
  GET    /api/students/search/
"""
import datetime
from rest_framework import status
from main.models import StudentProfile, StudentEnrollment, StudentRegistration, User, UserProfile
from .base import BaseAPITestCase

LIST_URL = '/api/students/'


def detail_url(pk):
    return f'/api/students/{pk}/'


class StudentListTests(BaseAPITestCase):

    def test_admin_can_list(self):
        self.auth_admin()
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_head_teacher_can_list(self):
        self.auth_head_teacher()
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_teacher_can_list(self):
        self.auth_teacher()
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_pagination_present(self):
        self.auth_admin()
        res = self.client.get(LIST_URL)
        self.assertIn('count', res.data)


class StudentCreateTests(BaseAPITestCase):

    def _payload(self, email='student1@example.com'):
        return {
            'email': email,
            'name': 'Test Student',
            'gender': 'Male',
            'dob': '2014-04-01',
            'id_card_type': 'QID',
            'id_card_number': '44444444',
            'mobile': '55000040',
            'branch_id': str(self.branch.id),
            'class_id': str(self.cls.id),
            'division_id': str(self.division.id),
            'category': 'PERMANENT',
            'father_name': 'Student Father',
            'mother_name': 'Student Mother',
            'parent_mobile': '55000041',
            'qatar_place': 'Doha',
            'qatar_landmark': 'Mall',
            'qatar_building_no': '1',
            'qatar_street_no': '2',
            'qatar_zone_no': '3',
            'india_state': 'Kerala',
            'india_district': 'Kozhikode',
            'india_place': 'Calicut',
            'india_house_name': 'Test House',
            'india_contact': '9876543210',
        }

    def test_admin_can_create(self):
        self.auth_admin()
        res = self.client.post(LIST_URL, self._payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_duplicate_email_rejected(self):
        self.auth_admin()
        self.client.post(LIST_URL, self._payload('dup@example.com'), format='json')
        res = self.client.post(LIST_URL, self._payload('dup@example.com'), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_cannot_create(self):
        self.auth_teacher()
        res = self.client.post(LIST_URL, self._payload('t@example.com'), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_denied(self):
        res = self.client.post(LIST_URL, self._payload('u@example.com'), format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class StudentRetrieveTests(BaseAPITestCase):

    def setUp(self):
        # Create a student directly
        self.student_user = User.objects.create_user(
            email='s_retrieve@example.com', password='S@1234',
            organization=self.org, user_type='STUDENT',
        )
        UserProfile.objects.create(
            user=self.student_user, full_name='Retrieve Student', gender='Male',
            dob=datetime.date(2014, 1, 1), id_card_type='QID',
            id_card_number='55555555', mobile='55000050',
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user, branch=self.branch,
            category='PERMANENT', status='ACTIVE',
        )
        StudentEnrollment.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            class_assigned=self.cls,
            division_assigned=self.division,
            enrollment_status='ENROLLED',
            enrollment_date=datetime.date.today(),
        )

    def test_admin_can_retrieve(self):
        self.auth_admin()
        res = self.client.get(detail_url(self.student.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_returns_student_name(self):
        self.auth_admin()
        res = self.client.get(detail_url(self.student.id))
        self.assertIn('Retrieve Student', str(res.data))

    def test_not_found(self):
        import uuid
        self.auth_admin()
        res = self.client.get(detail_url(uuid.uuid4()))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class StudentUpdateTests(BaseAPITestCase):

    def setUp(self):
        self.student_user = User.objects.create_user(
            email='s_update@example.com', password='S@1234',
            organization=self.org, user_type='STUDENT',
        )
        UserProfile.objects.create(
            user=self.student_user, full_name='Update Student', gender='Male',
            dob=datetime.date(2013, 6, 15), id_card_type='QID',
            id_card_number='66666666', mobile='55000060',
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user, branch=self.branch,
            category='PERMANENT', status='ACTIVE',
        )

    def test_admin_can_update(self):
        self.auth_admin()
        res = self.client.patch(
            detail_url(self.student.id),
            {'category': 'TEMPORARY'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_teacher_cannot_update(self):
        self.auth_teacher()
        res = self.client.patch(
            detail_url(self.student.id),
            {'category': 'TEMPORARY'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class StudentSearchTests(BaseAPITestCase):

    def test_search_endpoint_accessible(self):
        self.auth_admin()
        res = self.client.get('/api/students/search/', {'q': 'Ali'})
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_search_requires_auth(self):
        res = self.client.get('/api/students/search/', {'q': 'Ali'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
