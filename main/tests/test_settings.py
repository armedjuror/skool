"""
Tests for Settings endpoints:
  Academic Years  – /api/academic-years/
  Branches        – /api/branches/
  Classes         – /api/classes/
  Divisions       – /api/divisions/
  Utilities       – /api/utilities/branches|classes|divisions/
"""
import datetime
from rest_framework import status
from .base import BaseAPITestCase


# ─────────────────────────────────────────────
# ACADEMIC YEARS
# ─────────────────────────────────────────────

class AcademicYearListTests(BaseAPITestCase):

    def test_admin_can_list(self):
        self.auth_admin()
        res = self.client.get('/api/academic-years/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        res = self.client.get('/api/academic-years/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AcademicYearCreateTests(BaseAPITestCase):

    def test_admin_can_create(self):
        self.auth_admin()
        res = self.client.post('/api/academic-years/', {
            'name': '2025-2026',
            'start_date': '2025-06-01',
            'end_date': '2026-05-31',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['name'], '2025-2026')

    def test_duplicate_name_rejected(self):
        self.auth_admin()
        self.client.post('/api/academic-years/', {
            'name': '2026-2027', 'start_date': '2026-06-01', 'end_date': '2027-05-31',
        })
        res = self.client.post('/api/academic-years/', {
            'name': '2026-2027', 'start_date': '2026-06-01', 'end_date': '2027-05-31',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_cannot_create(self):
        self.auth_teacher()
        res = self.client.post('/api/academic-years/', {
            'name': '2030-2031', 'start_date': '2030-06-01', 'end_date': '2031-05-31',
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AcademicYearActivateTests(BaseAPITestCase):

    def test_activate_sets_active(self):
        self.auth_admin()
        # Create an inactive year
        res = self.client.post('/api/academic-years/', {
            'name': '2027-2028', 'start_date': '2027-06-01', 'end_date': '2028-05-31',
        })
        year_id = res.data['data']['id']
        res2 = self.client.post(f'/api/academic-years/{year_id}/activate/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# BRANCHES
# ─────────────────────────────────────────────

class BranchTests(BaseAPITestCase):

    def test_list_branches(self):
        self.auth_admin()
        res = self.client.get('/api/branches/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data['results'] if 'results' in res.data else res.data), 1)

    def test_create_branch(self):
        self.auth_admin()
        res = self.client.post('/api/branches/', {
            'name': 'New Branch', 'code': 'NEWB',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_duplicate_code_rejected(self):
        self.auth_admin()
        self.client.post('/api/branches/', {'name': 'Dup Branch', 'code': 'DUPB'})
        res = self.client.post('/api/branches/', {'name': 'Another', 'code': 'DUPB'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_branch(self):
        self.auth_admin()
        res = self.client.get(f'/api/branches/{self.branch.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['name'], 'Main Branch')

    def test_update_branch(self):
        self.auth_admin()
        res = self.client.patch(f'/api/branches/{self.branch.id}/', {'name': 'Updated Branch'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['name'], 'Updated Branch')
        # Restore
        self.client.patch(f'/api/branches/{self.branch.id}/', {'name': 'Main Branch'})

    def test_teacher_cannot_create_branch(self):
        self.auth_teacher()
        res = self.client.post('/api/branches/', {'name': 'Nope', 'code': 'NOPE'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


# ─────────────────────────────────────────────
# CLASSES
# ─────────────────────────────────────────────

class ClassTests(BaseAPITestCase):

    def test_list_classes(self):
        self.auth_admin()
        res = self.client.get('/api/classes/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_class(self):
        self.auth_admin()
        res = self.client.post('/api/classes/', {'name': 'Class II', 'level': 2})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_retrieve_class(self):
        self.auth_admin()
        res = self.client.get(f'/api/classes/{self.cls.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_teacher_cannot_create_class(self):
        self.auth_teacher()
        res = self.client.post('/api/classes/', {'name': 'Class X', 'level': 10})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


# ─────────────────────────────────────────────
# DIVISIONS
# ─────────────────────────────────────────────

class DivisionTests(BaseAPITestCase):

    def test_list_divisions(self):
        self.auth_admin()
        res = self.client.get('/api/divisions/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_division(self):
        self.auth_admin()
        res = self.client.post('/api/divisions/', {
            'name': 'B',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_retrieve_division(self):
        self.auth_admin()
        res = self.client.get(f'/api/divisions/{self.division.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# UTILITIES (public dropdowns)
# ─────────────────────────────────────────────

class UtilitiesTests(BaseAPITestCase):

    def test_utilities_branches_no_auth(self):
        res = self.client.get(f'/api/utilities/branches/?org_code=TEST')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_utilities_classes_no_auth(self):
        res = self.client.get(f'/api/utilities/classes/?org_code=TEST')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_utilities_divisions_no_auth(self):
        res = self.client.get(f'/api/utilities/divisions/?org_code=TEST')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
