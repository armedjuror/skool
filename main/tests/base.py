"""
Base test case with shared fixtures for all test modules.
Creates a complete org → users → academic structure in setUp.
"""
import datetime
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.core.files.uploadedfile import SimpleUploadedFile

from main.models import (
    Organization, Branch, AcademicYear, Class, Division,
    User, UserProfile,
)


def make_image():
    """Return a minimal valid JPEG SimpleUploadedFile."""
    # 1×1 white JPEG
    jpeg_bytes = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e'
        b'=\x00\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
        b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08'
        b'\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03'
        b'\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12'
        b'!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1'
        b'\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJ'
        b'STUVWXYZ\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xf5\x0e\xd4P'
        b'\x00\x00\x00\x1f\xff\xd9'
    )
    return SimpleUploadedFile('test.jpg', jpeg_bytes, content_type='image/jpeg')


class BaseAPITestCase(APITestCase):
    """
    Creates the full fixture hierarchy once per test class.

    Attributes available in every test:
        self.org           – Organization
        self.branch        – Branch
        self.academic_year – AcademicYear (active)
        self.cls           – Class
        self.division      – Division

        self.admin         – User (ADMIN) + self.admin_token
        self.head_teacher  – User (HEAD_TEACHER) + self.head_teacher_token
        self.teacher       – User (TEACHER) + self.teacher_token
    """

    @classmethod
    def setUpTestData(cls):
        # Organisation
        cls.org = Organization.objects.create(name='Test Org', code='TEST', is_active=True)

        # Academic structure
        cls.branch = Branch.objects.create(
            organization=cls.org, name='Main Branch', code='MAIN', is_active=True
        )
        cls.academic_year = AcademicYear.objects.create(
            organization=cls.org,
            name='2024-2025',
            start_date=datetime.date(2024, 6, 1),
            end_date=datetime.date(2025, 5, 31),
            is_active=True,
        )
        cls.cls = Class.objects.create(
            organization=cls.org, name='Class I', level=1, is_active=True
        )
        cls.division = Division.objects.create(
            organization=cls.org,
            name='A',
            is_active=True,
        )

        # Admin user
        cls.admin = User.objects.create_user(
            email='admin@test.com', password='Admin@1234',
            organization=cls.org, user_type='ADMIN',
        )
        UserProfile.objects.create(
            user=cls.admin, full_name='Test Admin', gender='Male',
            dob=datetime.date(1985, 1, 1), id_card_type='QID',
            id_card_number='12345678', mobile='55000001',
        )
        cls.admin_token = Token.objects.create(user=cls.admin)

        # Head teacher user
        cls.head_teacher = User.objects.create_user(
            email='headteacher@test.com', password='Head@1234',
            organization=cls.org, user_type='HEAD_TEACHER',
        )
        UserProfile.objects.create(
            user=cls.head_teacher, full_name='Head Teacher', gender='Male',
            dob=datetime.date(1980, 3, 15), id_card_type='QID',
            id_card_number='87654321', mobile='55000002',
        )
        cls.head_teacher_token = Token.objects.create(user=cls.head_teacher)

        # Teacher user
        cls.teacher = User.objects.create_user(
            email='teacher@test.com', password='Teacher@1234',
            organization=cls.org, user_type='TEACHER',
        )
        UserProfile.objects.create(
            user=cls.teacher, full_name='Test Teacher', gender='Female',
            dob=datetime.date(1990, 6, 10), id_card_type='PASSPORT',
            id_card_number='AB123456', mobile='55000003',
        )
        cls.teacher_token = Token.objects.create(user=cls.teacher)

    def auth(self, token):
        """Helper: set Authorization header."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def auth_admin(self):
        self.auth(self.admin_token)

    def auth_head_teacher(self):
        self.auth(self.head_teacher_token)

    def auth_teacher(self):
        self.auth(self.teacher_token)

    def no_auth(self):
        self.client.credentials()
