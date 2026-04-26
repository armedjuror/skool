"""
Tests for public staff registration:
  POST /api/registration/staff/submit/
  GET  /api/registration/staff/verify/
"""
from rest_framework import status
from main.models import StaffRegistration
from .base import BaseAPITestCase

SUBMIT_URL = '/api/registration/staff/submit/'
VERIFY_URL = '/api/registration/staff/verify/'


class StaffRegistrationSubmitTests(BaseAPITestCase):

    def _payload(self, **overrides):
        import json
        data = {
            'org_code': 'TEST',
            'full_name': 'Ahmed Khalid',
            'gender': 'Male',
            'dob': '1990-04-15',
            'id_card_type': 'QID',
            'id_card_number': '12300099',
            'mobile': '55001234',
            'email': 'staffapply@example.com',
            'qatar_address': json.dumps({
                'place': 'Al Wakra', 'landmark': 'Near School',
                'building_no': '2', 'street_no': '8', 'zone_no': '10',
            }),
            'india_address': json.dumps({
                'state': 'Kerala', 'district': 'Kannur',
                'panchayath': 'Thalassery', 'place': 'Thalassery',
                'house_name': 'Green House', 'contact_number': '9876501234',
            }),
        }
        data.update(overrides)
        return data

    def test_submit_valid(self):
        res = self.client.post(SUBMIT_URL, self._payload(), format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertIn('registration_id', res.data['data'])

    def test_creates_pending_record(self):
        self.client.post(SUBMIT_URL, self._payload(email='newstaff2@example.com'), format='multipart')
        self.assertTrue(
            StaffRegistration.objects.filter(
                email='newstaff2@example.com', status='PENDING'
            ).exists()
        )

    def test_no_auth_required(self):
        self.no_auth()
        res = self.client.post(SUBMIT_URL, self._payload(email='pub_staff@example.com'), format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_missing_required_fields(self):
        res = self.client.post(SUBMIT_URL, {'org_code': 'TEST'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_org_code(self):
        res = self.client.post(SUBMIT_URL, self._payload(org_code='NOPE'), format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email(self):
        res = self.client.post(SUBMIT_URL, self._payload(email='not-an-email'), format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class StaffRegistrationVerifyTests(BaseAPITestCase):

    def setUp(self):
        self.reg = StaffRegistration.objects.create(
            organization=self.org,
            full_name='Verify Staff',
            gender='Female',
            dob='1988-01-01',
            id_card_type='PASSPORT',
            id_card_number='PB456789',
            mobile='55009999',
            email='staffverify@example.com',
            status='PENDING',
        )

    def test_verify_by_id(self):
        res = self.client.get(VERIFY_URL, {'registration_id': str(self.reg.id)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])

    def test_verify_by_email(self):
        res = self.client.get(VERIFY_URL, {'email': 'staffverify@example.com'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_verify_not_found(self):
        import uuid
        res = self.client.get(VERIFY_URL, {'registration_id': str(uuid.uuid4())})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_params(self):
        res = self.client.get(VERIFY_URL)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
