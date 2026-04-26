"""
Tests for public student registration and the approval workflow:
  POST /api/registration/student/submit/
  GET  /api/registration/student/verify/
  GET  /api/pending/students/
  GET  /api/pending/students/{id}/
  POST /api/pending/students/{id}/approve/
  POST /api/pending/students/{id}/reject/
  POST /api/pending/students/{id}/request-info/
"""
import json
import datetime
from rest_framework import status
from main.models import StudentRegistration, StudentProfile
from .base import BaseAPITestCase, make_image

SUBMIT_URL = '/api/registration/student/submit/'
VERIFY_URL = '/api/registration/student/verify/'
PENDING_LIST_URL = '/api/pending/students/'


def pending_detail_url(pk):
    return f'/api/pending/students/{pk}/'

def approve_url(pk):
    return f'/api/pending/students/{pk}/approve/'

def reject_url(pk):
    return f'/api/pending/students/{pk}/reject/'

def request_info_url(pk):
    return f'/api/pending/students/{pk}/request-info/'


class StudentRegistrationSubmitTests(BaseAPITestCase):
    """POST /api/registration/student/submit/"""

    def _payload(self, **overrides):
        data = {
            'org_code': 'TEST',
            'admission_type': 'NEW',
            'student_name': 'Ali Hassan',
            'gender': 'Male',
            'dob': '2015-03-20',
            'study_type': 'PERMANENT',
            'id_card_type': 'QID',
            'id_card_number': '29876543',
            'father_name': 'Hassan Ali',
            'parent_mobile': '55123456',
            'father_whatsapp': '55123456',
            'email': 'parent@example.com',
            'mother_name': 'Fatima Ali',
            'qatar_address': json.dumps({
                'place': 'Doha', 'landmark': 'Near Mall',
                'building_no': '10', 'street_no': '5', 'zone_no': '30',
            }),
            'india_address': json.dumps({
                'state': 'Kerala', 'district': 'Malappuram',
                'panchayath': 'Tirur', 'place': 'Tirur Town',
                'house_name': 'Al Noor House', 'contact_number': '9876543210',
            }),
            'class_to_admit': str(self.cls.id),
            'interested_branch': str(self.branch.id),
        }
        data.update(overrides)
        return data

    def test_submit_valid_registration(self):
        res = self.client.post(SUBMIT_URL, self._payload(), format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertIn('registration_id', res.data['data'])

    def test_creates_pending_record(self):
        self.client.post(SUBMIT_URL, self._payload(email='newparent@example.com'), format='multipart')
        exists = StudentRegistration.objects.filter(
            email='newparent@example.com', status='PENDING'
        ).exists()
        self.assertTrue(exists)

    def test_missing_required_fields(self):
        res = self.client.post(SUBMIT_URL, {'org_code': 'TEST'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_org_code(self):
        res = self.client.post(SUBMIT_URL, self._payload(org_code='NOPE'), format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_class_id(self):
        import uuid
        res = self.client.post(
            SUBMIT_URL,
            self._payload(class_to_admit=str(uuid.uuid4())),
            format='multipart'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_auth_required(self):
        """Public endpoint — unauthenticated requests must work."""
        self.no_auth()
        res = self.client.post(SUBMIT_URL, self._payload(email='pub@example.com'), format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


class StudentRegistrationVerifyTests(BaseAPITestCase):
    """GET /api/registration/student/verify/"""

    def setUp(self):
        self.reg = StudentRegistration.objects.create(
            organization=self.org,
            admission_type='NEW',
            student_name='Test Student',
            gender='Male',
            dob=datetime.date(2015, 1, 1),
            study_type='PERMANENT',
            id_card_type='QID',
            id_card_number='11111111',
            father_name='Father Name',
            parent_mobile='55000099',
            email='verify@example.com',
            mother_name='Mother Name',
            class_to_admit=self.cls,
            interested_branch=self.branch,
            status='PENDING',
        )

    def test_verify_by_registration_id(self):
        res = self.client.get(VERIFY_URL, {'registration_id': str(self.reg.id)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])

    def test_verify_by_email(self):
        res = self.client.get(VERIFY_URL, {'email': 'verify@example.com'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_verify_not_found(self):
        import uuid
        res = self.client.get(VERIFY_URL, {'registration_id': str(uuid.uuid4())})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_verify_missing_params(self):
        res = self.client.get(VERIFY_URL)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PendingStudentListTests(BaseAPITestCase):
    """GET /api/pending/students/"""

    def test_admin_can_list(self):
        self.auth_admin()
        res = self.client.get(PENDING_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_head_teacher_can_list(self):
        self.auth_head_teacher()
        res = self.client.get(PENDING_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        res = self.client.get(PENDING_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_teacher_denied(self):
        self.auth_teacher()
        res = self.client.get(PENDING_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class PendingStudentApproveTests(BaseAPITestCase):
    """POST /api/pending/students/{id}/approve/"""

    def setUp(self):
        self.reg = StudentRegistration.objects.create(
            organization=self.org,
            admission_type='NEW',
            student_name='Approve Student',
            gender='Female',
            dob=datetime.date(2014, 5, 10),
            study_type='PERMANENT',
            id_card_type='QID',
            id_card_number='22222222',
            father_name='Father',
            parent_mobile='55000010',
            email='approve@example.com',
            mother_name='Mother',
            class_to_admit=self.cls,
            interested_branch=self.branch,
            status='PENDING',
        )

    def _approval_payload(self):
        return {
            'branch_id': str(self.branch.id),
            'class_id': str(self.cls.id),
            'division_id': str(self.division.id),
            'category': 'PERMANENT',
        }

    def test_admin_can_approve(self):
        self.auth_admin()
        res = self.client.post(
            approve_url(self.reg.id),
            self._approval_payload(),
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.status, 'APPROVED')

    def test_approve_creates_student_profile(self):
        self.auth_admin()
        self.client.post(approve_url(self.reg.id), self._approval_payload(), format='json')
        self.assertTrue(StudentProfile.objects.filter(
            registration=self.reg
        ).exists())

    def test_approve_already_approved_fails(self):
        self.auth_admin()
        self.client.post(approve_url(self.reg.id), self._approval_payload(), format='json')
        res = self.client.post(approve_url(self.reg.id), self._approval_payload(), format='json')
        # Approved registrations are filtered out of the pending queue → 404 is also valid
        self.assertIn(res.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])

    def test_missing_branch_id_fails(self):
        self.auth_admin()
        payload = self._approval_payload()
        del payload['branch_id']
        res = self.client.post(approve_url(self.reg.id), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_cannot_approve(self):
        self.auth_teacher()
        res = self.client.post(approve_url(self.reg.id), self._approval_payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class PendingStudentRejectTests(BaseAPITestCase):
    """POST /api/pending/students/{id}/reject/"""

    def setUp(self):
        self.reg = StudentRegistration.objects.create(
            organization=self.org,
            admission_type='NEW',
            student_name='Reject Student',
            gender='Male',
            dob=datetime.date(2013, 8, 20),
            study_type='TEMPORARY',
            id_card_type='PASSPORT',
            id_card_number='PA123456',
            father_name='Father',
            parent_mobile='55000020',
            email='reject@example.com',
            mother_name='Mother',
            class_to_admit=self.cls,
            interested_branch=self.branch,
            status='PENDING',
        )

    def test_admin_can_reject(self):
        self.auth_admin()
        res = self.client.post(
            reject_url(self.reg.id),
            {'rejection_reason': 'Incomplete documents'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.status, 'REJECTED')

    def test_reject_requires_reason(self):
        self.auth_admin()
        res = self.client.post(reject_url(self.reg.id), {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PendingStudentRequestInfoTests(BaseAPITestCase):
    """POST /api/pending/students/{id}/request-info/"""

    def setUp(self):
        self.reg = StudentRegistration.objects.create(
            organization=self.org,
            admission_type='NEW',
            student_name='Info Student',
            gender='Male',
            dob=datetime.date(2016, 2, 14),
            study_type='PERMANENT',
            id_card_type='QID',
            id_card_number='33333333',
            father_name='Father',
            parent_mobile='55000030',
            email='info@example.com',
            mother_name='Mother',
            class_to_admit=self.cls,
            interested_branch=self.branch,
            status='PENDING',
        )

    def test_admin_can_request_info(self):
        self.auth_admin()
        res = self.client.post(
            request_info_url(self.reg.id),
            {'message': 'Please submit the original TC document.'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.status, 'INFO_REQUESTED')
