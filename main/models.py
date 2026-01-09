"""
Kerala Islamic Centre - Madrassa Management System
Django Models - FINAL VERSION (CORRECTED)

This module contains all database models for the system with:
- Unified User model (staff + students)
- SEPARATE Class and Division models
- StudentEnrollment for year-over-year tracking
- Enhanced fee management with auto-creation
- Teacher assignment history tracking
- Complete audit trail

Author: Backend Team
Date: December 31, 2024
Version: 2.0 Final (Corrected)
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from datetime import timedelta
import uuid


# ============================================================================
# BASE MODEL
# ============================================================================

class BaseModel(models.Model):
    """
    Abstract base model that provides common fields for all models
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ============================================================================
# CORE ORGANIZATION MODELS
# ============================================================================

class Organization(BaseModel):
    """
    Root entity for multi-tenancy. Each Islamic centre is an organization.
    All data is isolated at the organization level.
    """
    name = models.CharField(max_length=200)
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Unique organization code (e.g., KIC)"
    )
    logo = models.ImageField(upload_to='organizations/logos/', null=True, blank=True)

    # Contact Information
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.JSONField(default=dict, blank=True)

    # Settings stored as JSON for flexibility
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Organization-specific configuration"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Branch(BaseModel):
    """
    Physical branches/locations within an organization.
    Each branch operates semi-independently under the organization.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='branches'
    )
    name = models.CharField(max_length=200)
    code = models.CharField(
        max_length=10,
        help_text="4-letter code used for admission numbers (e.g., WAKR)"
    )

    # Address stored as JSON for flexibility
    address = models.JSONField(default=dict, blank=True)

    # Contact Information
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    # Head Teacher (assigned from User model)
    head_teacher = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_branches',
        limit_choices_to={'user_type__in': ['HEAD_TEACHER', 'CHIEF_HEAD_TEACHER']}
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'branches'
        verbose_name_plural = 'Branches'
        ordering = ['organization', 'name']
        unique_together = [('organization', 'code')]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class AcademicYear(BaseModel):
    """
    Academic year configuration. Only one can be active per organization.
    Controls which year's data is displayed and managed.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='academic_years'
    )
    name = models.CharField(
        max_length=50,
        help_text="e.g., 2024-2025"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(
        default=False,
        help_text="Only one academic year can be active at a time per organization"
    )

    class Meta:
        db_table = 'academic_years'
        ordering = ['-start_date']
        unique_together = [('organization', 'name')]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

    def save(self, *args, **kwargs):
        """Ensure only one active academic year per organization"""
        if self.is_active:
            AcademicYear.objects.filter(
                organization=self.organization,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class Class(BaseModel):
    """
    Grade/Class levels (I to XII).
    Reusable across branches within an organization.
    Admin creates: Class I, Class II, ..., Class XII (12 records total)
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='classes'
    )
    name = models.CharField(
        max_length=50,
        help_text="e.g., Class I, Class II, etc."
    )
    level = models.IntegerField(
        help_text="Arabic numeral: 1, 2,...., 11, 12"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'classes'
        verbose_name_plural = 'Classes'
        ordering = ['organization', 'level', 'name']
        unique_together = [('organization', 'name')]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return f"{self.name}"


class Division(BaseModel):
    """
    Class sections/divisions (A to J).
    Reusable across classes and branches.
    Admin creates: Division A, Division B, ..., Division J (10 records total)
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='divisions'
    )
    name = models.CharField(
        max_length=10,
        help_text="e.g., A, B, C, ..., J"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'divisions'
        ordering = ['organization', 'name']
        unique_together = [('organization', 'name')]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
        ]

    def __str__(self):
        return f"Division {self.name}"


# ============================================================================
# UNIFIED USER MANAGEMENT MODELS
# ============================================================================

class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # For superuser, we need an organization
        # Get or create a default organization for superusers
        org = extra_fields.get('organization')
        if not org:
            org, _ = Organization.objects.get_or_create(
                code='ADMIN',
                defaults={'name': 'Admin Organization', 'is_active': True}
            )
            extra_fields['organization'] = org

        # Set default user_type for superuser
        extra_fields.setdefault('user_type', 'ADMIN')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Unified user model for ALL users in the system:
    - Staff (Admin, Head Teachers, Teachers, Accountants, Office Staff)
    - Students
    - Parents (future)

    This replaces the default Django User model.
    """
    # Remove username, use email as unique identifier
    username = None
    email = models.EmailField(unique=True)
    # Override groups and user_permissions to avoid reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='main_user_set',
        related_query_name='main_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='main_user_set',
        related_query_name='main_user',
    )

    # Multi-tenancy
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='users'
    )

    # User Type
    USER_TYPE_CHOICES = [
        # Staff Types
        ('ADMIN', 'Admin'),
        ('CHIEF_HEAD_TEACHER', 'Chief Head Teacher'),
        ('HEAD_TEACHER', 'Head Teacher'),
        ('TEACHER', 'Teacher'),
        ('ACCOUNTANT', 'Accountant'),
        ('OFFICE_STAFF', 'Office Staff'),
        # Non-Staff Types
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),  # Future use
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)

    # Email is the login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email and password are required by default

    objects = UserManager()

    class Meta:
        db_table = 'users'
        ordering = ['organization', 'user_type', 'email']
        indexes = [
            models.Index(fields=['organization', 'user_type']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        profile_name = getattr(self, 'userprofile', None)
        if profile_name and hasattr(profile_name, 'full_name'):
            return f"{profile_name.full_name} ({self.get_user_type_display()})"
        return f"{self.email} ({self.get_user_type_display()})"

    @property
    def is_staff_user(self):
        """Check if user is a staff member"""
        return self.user_type in [
            'ADMIN', 'CHIEF_HEAD_TEACHER', 'HEAD_TEACHER',
            'TEACHER', 'ACCOUNTANT', 'OFFICE_STAFF'
        ]

    @property
    def is_student(self):
        """Check if user is a student"""
        return self.user_type == 'STUDENT'

    @property
    def role(self):
        """Return user_type as lowercase role for API compatibility"""
        return self.user_type.lower() if self.user_type else None


class UserProfile(BaseModel):
    """
    Extended profile information for ALL users (staff and students).
    Contains personal information common to everyone.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='userprofile'
    )

    # Personal Information
    full_name = models.CharField(max_length=200)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female')]
    )
    dob = models.DateField(verbose_name="Date of Birth")
    age = models.IntegerField(
        null=True,
        blank=True,
        help_text="Auto-calculated from DOB"
    )

    # ID Information
    ID_CARD_CHOICES = [
        ('QID', 'Qatar ID'),
        ('PASSPORT', 'Passport'),
    ]
    id_card_type = models.CharField(max_length=10, choices=ID_CARD_CHOICES)
    id_card_number = models.CharField(max_length=50)

    # Contact Information
    mobile = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'"
            )
        ]
    )
    whatsapp = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'"
            )
        ]
    )

    # Photo
    photo = models.ImageField(
        upload_to='users/photos/%Y/%m/',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['mobile']),
            models.Index(fields=['id_card_number']),
        ]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        """Auto-calculate age from DOB"""
        if self.dob:
            today = timezone.now().date()
            self.age = today.year - self.dob.year - (
                    (today.month, today.day) < (self.dob.month, self.dob.day)
            )
        super().save(*args, **kwargs)


class UserAddress(BaseModel):
    """
    Address information for users (staff and students).
    Supports multiple addresses per user (Qatar and India).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )

    ADDRESS_TYPE_CHOICES = [
        ('QATAR', 'Qatar Address'),
        ('INDIA', 'India Address'),
    ]
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES)

    # Qatar Address Fields
    qatar_place = models.CharField(max_length=200, null=True, blank=True)
    qatar_landmark = models.CharField(max_length=200, null=True, blank=True)
    qatar_building_no = models.CharField(max_length=50, null=True, blank=True)
    qatar_street_no = models.CharField(max_length=50, null=True, blank=True)
    qatar_zone_no = models.CharField(max_length=50, null=True, blank=True)

    # India Address Fields
    india_state = models.CharField(max_length=100, null=True, blank=True)
    india_district = models.CharField(max_length=100, null=True, blank=True)
    india_panchayath = models.CharField(max_length=100, null=True, blank=True)
    india_place = models.CharField(max_length=100, null=True, blank=True)
    india_house_name = models.CharField(max_length=200, null=True, blank=True)
    india_contact = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'user_addresses'
        verbose_name_plural = 'User Addresses'
        indexes = [
            models.Index(fields=['user', 'address_type']),
        ]

    def __str__(self):
        return f"{self.user.userprofile.full_name} - {self.get_address_type_display()}"


class StaffProfile(BaseModel):
    """
    Staff-specific information. Only for staff members.
    Linked to User with user_type in staff types.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staffprofile',
        limit_choices_to={'user_type__in': [
            'ADMIN', 'CHIEF_HEAD_TEACHER', 'HEAD_TEACHER',
            'TEACHER', 'ACCOUNTANT', 'OFFICE_STAFF'
        ]}
    )

    # Staff Number (auto-generated: KIC001, KIC002, etc.)
    staff_number = models.CharField(max_length=20, unique=True)

    # Staff Category
    CATEGORY_CHOICES = [
        ('PERMANENT', 'Permanent'),
        ('TEMPORARY', 'Temporary'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    # Status
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INACTIVE')

    # Assignment
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members'
    )
    assigned_head_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_staff',
        limit_choices_to={'user_type__in': ['HEAD_TEACHER', 'CHIEF_HEAD_TEACHER']}
    )

    # Compensation
    monthly_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    other_allowances = models.JSONField(
        default=dict,
        blank=True,
        help_text="Store transport, food, mobile allowances as JSON"
    )

    # Academic Credentials
    religious_academic_details = models.TextField(null=True, blank=True)
    academic_details = models.TextField(null=True, blank=True)
    previous_madrasa = models.CharField(max_length=200, null=True, blank=True)
    msr_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="MSR Number"
    )
    aadhar_number = models.CharField(max_length=12, null=True, blank=True)

    # Admin Notes
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'staff_profiles'
        indexes = [
            models.Index(fields=['staff_number']),
            models.Index(fields=['status']),
            models.Index(fields=['branch']),
        ]

    def __str__(self):
        return f"{self.staff_number} - {self.user.userprofile.full_name}"

    def save(self, *args, **kwargs):
        """Auto-generate staff number if not set"""
        if not self.staff_number:
            org_code = self.user.organization.code[:3].upper()
            last_staff = StaffProfile.objects.filter(
                user__organization=self.user.organization,
                staff_number__startswith=org_code
            ).order_by('-staff_number').first()

            if last_staff:
                last_num = int(last_staff.staff_number[3:])
                new_num = last_num + 1
            else:
                new_num = 1

            self.staff_number = f"{org_code}{new_num:03d}"

        super().save(*args, **kwargs)


class TeacherAssignment(BaseModel):
    """
    Tracks teacher assignments to class-divisions over time.
    Maintains complete history of who taught what and when.
    Multiple assignments can exist for same class+division over different time periods.
    """
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
        limit_choices_to={'user_type': 'TEACHER'}
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )

    # What they're teaching
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    division_assigned = models.ForeignKey(
        Division,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )

    # Time period tracking
    start_date = models.DateField(
        help_text="When this assignment started"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="When this assignment ended (null = ongoing)"
    )

    # Assignment type
    ASSIGNMENT_TYPE_CHOICES = [
        ('PRIMARY', 'Primary Class Teacher'),
        ('SUBSTITUTE', 'Substitute Teacher'),
        ('ASSISTANT', 'Assistant Teacher'),
        ('TEMPORARY', 'Temporary Assignment'),
    ]
    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPE_CHOICES,
        default='PRIMARY'
    )

    # Why assignment changed
    CHANGE_REASON_CHOICES = [
        ('NEW_YEAR', 'New Academic Year'),
        ('LEAVE', 'Teacher on Leave'),
        ('TRANSFER', 'Teacher Transferred'),
        ('REPLACEMENT', 'Permanent Replacement'),
        ('RESIGNATION', 'Teacher Resigned'),
        ('PROMOTION', 'Teacher Promoted'),
        ('OTHER', 'Other'),
    ]
    change_reason = models.CharField(
        max_length=20,
        choices=CHANGE_REASON_CHOICES,
        null=True,
        blank=True
    )

    # Links to other assignments
    replaced_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replaces'
    )

    is_primary = models.BooleanField(
        default=True,
        help_text="Is this the primary teacher for this class?"
    )
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'teacher_assignments'
        unique_together = [
            ('teacher', 'branch', 'academic_year', 'class_assigned', 'division_assigned')
        ]
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['teacher', 'academic_year', 'is_active']),
            models.Index(fields=['branch', 'class_assigned', 'division_assigned']),
            models.Index(fields=['is_active', 'end_date']),
        ]

    def __str__(self):
        return (f"{self.teacher.userprofile.full_name} → "
                f"{self.class_assigned.name} {self.division_assigned.name} "
                f"({self.start_date} to {self.end_date or 'Present'})")

    def save(self, *args, **kwargs):
        """
        When creating new active assignment, end previous assignment
        """
        if self.is_active and not self.end_date:
            # End any other active assignments for this class+division
            TeacherAssignment.objects.filter(
                branch=self.branch,
                class_assigned=self.class_assigned,
                division_assigned=self.division_assigned,
                academic_year=self.academic_year,
                is_active=True,
                end_date__isnull=True
            ).exclude(id=self.id).update(
                end_date=self.start_date,
                is_active=False
            )

        super().save(*args, **kwargs)


# ============================================================================
# STUDENT LIFECYCLE MODELS
# ============================================================================

class StudentRegistration(BaseModel):
    """
    Stores online student registration form submissions.
    These are temporary records that get converted to Student upon approval.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='student_registrations'
    )

    submission_date = models.DateTimeField(auto_now_add=True)

    # Admission Type
    ADMISSION_TYPE_CHOICES = [
        ('NEW', 'New Admission'),
        ('EXISTING_UPDATE', 'Existing Student Update'),
    ]
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPE_CHOICES)

    # Personal Details
    student_name = models.CharField(max_length=200)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female')]
    )
    dob = models.DateField(verbose_name="Date of Birth")

    # Study Type
    STUDY_TYPE_CHOICES = [
        ('PERMANENT', 'Permanent'),
        ('TEMPORARY', 'Temporary'),
    ]
    study_type = models.CharField(max_length=20, choices=STUDY_TYPE_CHOICES)

    # ID Information
    id_card_type = models.CharField(
        max_length=10,
        choices=[('QID', 'Qatar ID'), ('PASSPORT', 'Passport')]
    )
    id_card_number = models.CharField(max_length=50)

    # Photo
    photo = models.ImageField(
        upload_to='registrations/photos/%Y/%m/',
        null=True,
        blank=True
    )

    # Family Details
    father_name = models.CharField(max_length=200)
    parent_mobile = models.CharField(max_length=20)
    father_whatsapp = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField()
    mother_name = models.CharField(max_length=200)
    siblings_details = models.TextField(null=True, blank=True)

    # Addresses stored as JSON for temporary storage
    qatar_address = models.JSONField(default=dict, blank=True)
    india_address = models.JSONField(default=dict, blank=True)

    # Academic Details - Just preference at registration
    class_to_admit = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registration_applications',
        help_text="Which class the parent wants to enroll in"
    )
    interested_branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registration_applications'
    )
    completed_classes = models.CharField(max_length=100, null=True, blank=True)
    previous_madrasa = models.CharField(max_length=200, null=True, blank=True)
    tc_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Transfer Certificate Number"
    )
    aadhar_number = models.CharField(max_length=12, null=True, blank=True)

    # Status Tracking
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('INFO_REQUESTED', 'Information Requested'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    rejection_reason = models.TextField(null=True, blank=True)
    info_request_message = models.TextField(null=True, blank=True)

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_registrations'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'student_registrations'
        ordering = ['-submission_date']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['submission_date']),
            models.Index(fields=['interested_branch']),
        ]

    def __str__(self):
        return f"{self.student_name} - {self.get_status_display()}"


class StudentProfile(BaseModel):
    """
    Student master record - contains basic info that doesn't change.
    Year-specific data (class, teacher, etc.) is in StudentEnrollment.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='studentprofile',
        limit_choices_to={'user_type': 'STUDENT'}
    )

    # Link to original registration (optional)
    registration = models.OneToOneField(
        StudentRegistration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student'
    )

    # Admission Number (auto-generated: WAKR0001, NABI0001, etc.)
    admission_number = models.CharField(max_length=20, unique=True)

    # Student Category
    CATEGORY_CHOICES = [
        ('PERMANENT', 'Permanent'),
        ('TEMPORARY', 'Temporary'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    # Overall Status (across all years)
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('GRADUATED', 'Graduated'),
        ('TRANSFERRED', 'Transferred'),
        ('DROPPED', 'Dropped Out'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='INACTIVE'
    )

    # Home Branch (primary branch, doesn't change frequently)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        related_name='students'
    )

    # Additional Info
    has_siblings = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)

    # Activation Tracking
    activated_at = models.DateTimeField(null=True, blank=True)
    activated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activated_students'
    )

    class Meta:
        db_table = 'student_profiles'
        indexes = [
            models.Index(fields=['admission_number']),
            models.Index(fields=['status']),
            models.Index(fields=['branch']),
        ]

    def __str__(self):
        return f"{self.admission_number} - {self.user.userprofile.full_name}"

    def save(self, *args, **kwargs):
        """Auto-generate admission number if not set"""
        if not self.admission_number and self.branch:
            branch_code = self.branch.code[:4].upper()

            last_student = StudentProfile.objects.filter(
                user__organization=self.user.organization,
                branch=self.branch,
                admission_number__startswith=branch_code
            ).order_by('-admission_number').first()

            if last_student:
                last_num = int(last_student.admission_number[4:])
                new_num = last_num + 1
            else:
                new_num = 1

            self.admission_number = f"{branch_code}{new_num:04d}"

        super().save(*args, **kwargs)

    @property
    def current_enrollment(self):
        """Get student's current enrollment"""
        return self.enrollments.filter(
            academic_year__is_active=True,
            enrollment_status='ENROLLED'
        ).first()


class StudentEnrollment(BaseModel):
    """
    Enrollment record for each academic year.
    This is where class+division assignment happens - separate record for each year!
    Enables year-over-year tracking and easy promotion/demotion.

    CRITICAL: This preserves complete academic history.
    Never delete or overwrite - always create new records.
    """
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='student_enrollments'
    )

    # Class and Division assignment for THIS year
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name='enrolled_students',
        help_text="Student's class for this academic year"
    )
    division_assigned = models.ForeignKey(
        Division,
        on_delete=models.PROTECT,
        related_name='enrolled_students',
        help_text="Student's division for this academic year"
    )

    # Enrollment status for THIS year
    ENROLLMENT_STATUS_CHOICES = [
        ('ENROLLED', 'Enrolled'),
        ('PROMOTED', 'Promoted'),
        ('DETAINED', 'Detained/Repeat'),
        ('TRANSFERRED', 'Transferred Out'),
        ('DROPPED', 'Dropped Out'),
        ('COMPLETED', 'Completed'),
    ]
    enrollment_status = models.CharField(
        max_length=20,
        choices=ENROLLMENT_STATUS_CHOICES,
        default='ENROLLED'
    )

    # Dates
    enrollment_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)

    # Promotion/Detention tracking
    promoted_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promoted_from',
        help_text="Link to next year's enrollment if promoted"
    )

    # Performance tracking (optional)
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    final_result = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Pass/Fail or grade"
    )

    remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'student_enrollments'
        unique_together = [('student', 'academic_year')]
        ordering = ['-academic_year__start_date']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['class_assigned', 'division_assigned', 'enrollment_status']),
            models.Index(fields=['enrollment_status']),
        ]

    def __str__(self):
        return (f"{self.student.user.userprofile.full_name} - "
                f"{self.academic_year.name} - "
                f"{self.class_assigned.name} {self.division_assigned.name}")

    @property
    def current_teacher(self):
        """Get the current teacher for this enrollment"""
        assignment = TeacherAssignment.objects.filter(
            class_assigned=self.class_assigned,
            division_assigned=self.division_assigned,
            academic_year=self.academic_year,
            is_active=True,
            start_date__lte=timezone.now().date()
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now().date())
        ).first()

        return assignment.teacher if assignment else None

    def get_teacher_on_date(self, date):
        """Get the teacher on a specific date"""
        assignment = TeacherAssignment.objects.filter(
            class_assigned=self.class_assigned,
            division_assigned=self.division_assigned,
            academic_year=self.academic_year,
            start_date__lte=date
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=date)
        ).first()

        return assignment.teacher if assignment else None


class StudentFamily(BaseModel):
    """
    Family information for students.
    Separated for normalization and privacy.
    """
    student = models.OneToOneField(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='family'
    )

    # Father Details
    father_name = models.CharField(max_length=200)
    parent_mobile = models.CharField(max_length=20)
    father_whatsapp = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField()

    # Mother Details
    mother_name = models.CharField(max_length=200)

    # Siblings
    siblings_details = models.TextField(
        null=True,
        blank=True,
        help_text="Information about siblings studying in the madrassa"
    )

    class Meta:
        db_table = 'student_families'
        verbose_name_plural = 'Student Families'

    def __str__(self):
        return f"Family of {self.student.user.userprofile.full_name}"


class StudentAcademicHistory(BaseModel):
    """
    Historical academic records for students.
    Tracks previous education before joining this madrassa.
    """
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='academic_history'
    )

    # Previous Education
    previous_class = models.CharField(max_length=100, null=True, blank=True)
    previous_madrasa = models.CharField(max_length=200, null=True, blank=True)
    tc_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Transfer Certificate Number"
    )
    completed_classes = models.CharField(max_length=100, null=True, blank=True)

    year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Year of completion"
    )

    # Notes
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'student_academic_histories'
        verbose_name_plural = 'Student Academic Histories'
        ordering = ['-year']
        indexes = [
            models.Index(fields=['student', 'year']),
        ]

    def __str__(self):
        return f"{self.student.user.userprofile.full_name} - {self.previous_madrasa}"


# ============================================================================
# FEE MANAGEMENT MODELS
# (Enhanced with auto-creation triggers)
# ============================================================================

class FeeType(BaseModel):
    """
    Defines types of fees (Monthly, Exam, Festival, etc.)
    Reusable across the organization.
    Enhanced with auto-creation triggers.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='fee_types'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    CATEGORY_CHOICES = [
        ('MONTHLY', 'Monthly Fee'),
        ('ADMISSION', 'Admission Fee'),
        ('EXAM', 'Exam Fee'),
        ('FESTIVAL', 'Festival Fee'),
        ('SPORTS', 'Sports Fee'),
        ('BOOKS', 'Books Fee'),
        ('UNIFORM', 'Uniform Fee'),
        ('TRANSPORT', 'Transport Fee'),
        ('OTHER', 'Other'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    # When to charge this fee
    CHARGE_TRIGGER_CHOICES = [
        ('ON_ADMISSION', 'On Student Admission'),
        ('ON_ENROLLMENT', 'On Academic Year Enrollment'),
        ('MONTHLY', 'Monthly Recurring'),
        ('ANNUAL', 'Once Per Year'),
        ('MANUAL', 'Manual Entry Only'),
    ]
    charge_trigger = models.CharField(
        max_length=20,
        choices=CHARGE_TRIGGER_CHOICES,
        default='MANUAL',
        help_text="When to automatically create due records"
    )

    # For monthly/annual fees
    charge_month = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Which month to charge (1-12) for annual fees"
    )

    is_recurring = models.BooleanField(
        default=False,
        help_text="Does this fee recur monthly?"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'fee_types'
        unique_together = [('organization', 'name')]
        ordering = ['organization', 'category', 'name']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['category']),
            models.Index(fields=['charge_trigger']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class FeeStructure(BaseModel):
    """
    Default fee configuration by branch/class/category.
    Defines the base fees before student-specific overrides.
    Enhanced with auto-creation settings.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )

    # Optional filters (null = applies to all)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fee_structures',
        help_text="Null = applies to all branches"
    )
    class_level = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fee_structures',
        help_text="Null = applies to all classes"
    )

    fee_type = models.ForeignKey(
        FeeType,
        on_delete=models.CASCADE,
        related_name='structures'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    APPLICABLE_TO_CHOICES = [
        ('ALL', 'All Students'),
        ('PERMANENT', 'Permanent Students Only'),
        ('TEMPORARY', 'Temporary Students Only'),
    ]
    applicable_to = models.CharField(
        max_length=20,
        choices=APPLICABLE_TO_CHOICES,
        default='ALL'
    )

    # Validity Period
    effective_from = models.DateField()
    effective_to = models.DateField()

    # Auto-creation settings
    auto_create_due = models.BooleanField(
        default=True,
        help_text="Automatically create due records for this fee"
    )

    due_days_after_trigger = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Days after trigger event before fee is due"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'fee_structures'
        ordering = ['organization', 'academic_year', 'branch', 'class_level']
        indexes = [
            models.Index(fields=['organization', 'academic_year', 'is_active']),
            models.Index(fields=['branch', 'class_level']),
            models.Index(fields=['effective_from', 'effective_to']),
            models.Index(fields=['fee_type', 'is_active']),
        ]

    def __str__(self):
        branch_str = self.branch.name if self.branch else "All Branches"
        class_str = self.class_level.name if self.class_level else "All Classes"
        return f"{self.fee_type.name} - {branch_str} - {class_str} - {self.amount}"


class StudentFeeConfiguration(BaseModel):
    """
    Student-specific fee overrides.
    Allows customization of fees for individual students.
    """
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='fee_configurations'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='student_fee_configs'
    )
    fee_type = models.ForeignKey(
        FeeType,
        on_delete=models.CASCADE,
        related_name='student_configs'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    override_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for custom fee amount (scholarship, sibling discount, etc.)"
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='fee_config_updates'
    )

    class Meta:
        db_table = 'student_fee_configurations'
        unique_together = [('student', 'academic_year', 'fee_type')]
        ordering = ['student', 'academic_year']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['fee_type']),
        ]

    def __str__(self):
        return (f"{self.student.user.userprofile.full_name} - "
                f"{self.fee_type.name} - {self.amount}")


class FeeCollection(BaseModel):
    """
    Records of fee payments.
    Main transaction record for fee collections.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='fee_collections'
    )

    # Auto-generated receipt number: KIC-2024-12-0001
    receipt_number = models.CharField(max_length=50, unique=True)

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='fee_payments'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='fee_collections'
    )

    # Link to enrollment (optional but recommended)
    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_payments',
        help_text="Link to specific enrollment period"
    )

    # Payment Details
    collection_date = models.DateField()
    collected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='collected_fees'
    )

    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('OTHER', 'Other'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    reference_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Cheque number, transaction ID, etc."
    )

    remarks = models.TextField(null=True, blank=True)

    # Approval Workflow
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_fees'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'fee_collections'
        ordering = ['-collection_date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['collection_date']),
            models.Index(fields=['receipt_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.receipt_number} - {self.student.user.userprofile.full_name} - {self.total_amount}"

    def save(self, *args, **kwargs):
        """Auto-generate receipt number if not set"""
        if not self.receipt_number:
            org_code = self.organization.code
            year = self.collection_date.year
            month = self.collection_date.month
            prefix = f"{org_code}-{year}-{month:02d}"

            last_receipt = FeeCollection.objects.filter(
                organization=self.organization,
                receipt_number__startswith=prefix
            ).order_by('-receipt_number').first()

            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.receipt_number = f"{prefix}-{new_num:04d}"

        super().save(*args, **kwargs)


class FeeCollectionItem(BaseModel):
    """
    Line items for fee collections.
    Supports partial payments and multiple fee types in one receipt.
    """
    fee_collection = models.ForeignKey(
        FeeCollection,
        on_delete=models.CASCADE,
        related_name='items'
    )
    fee_type = models.ForeignKey(
        FeeType,
        on_delete=models.CASCADE,
        related_name='collection_items'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # For monthly fees
    month = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month number (1-12) for monthly fees"
    )
    year = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'fee_collection_items'
        ordering = ['fee_collection', 'fee_type']
        indexes = [
            models.Index(fields=['fee_collection']),
            models.Index(fields=['fee_type']),
            models.Index(fields=['month', 'year']),
        ]

    def __str__(self):
        month_str = f" - {self.get_month_name()} {self.year}" if self.month else ""
        return f"{self.fee_type.name}{month_str} - {self.amount}"

    def get_month_name(self):
        """Get month name from month number"""
        if self.month:
            import calendar
            return calendar.month_name[self.month]
        return ""


class StudentFeeDue(BaseModel):
    """
    Computed/cached dues for students.
    Created automatically by signals/Celery or manually.
    Updated when fees are configured or collected.
    """
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='fee_dues'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='student_dues'
    )
    fee_type = models.ForeignKey(
        FeeType,
        on_delete=models.CASCADE,
        related_name='student_dues'
    )

    # Link to enrollment that triggered this due
    triggered_by_enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_dues'
    )

    # For monthly fees
    month = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    # Amounts
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    due_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    # Due date
    due_date = models.DateField(
        help_text="When this fee is due"
    )

    # Track creation source
    CREATION_SOURCE_CHOICES = [
        ('AUTO_ADMISSION', 'Auto-created on admission'),
        ('AUTO_ENROLLMENT', 'Auto-created on enrollment'),
        ('AUTO_MONTHLY', 'Auto-created monthly'),
        ('AUTO_ANNUAL', 'Auto-created annually'),
        ('MANUAL', 'Manually created'),
        ('ADMIN_OVERRIDE', 'Admin override'),
    ]
    creation_source = models.CharField(
        max_length=20,
        choices=CREATION_SOURCE_CHOICES,
        default='MANUAL'
    )

    last_payment_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'student_fee_dues'
        unique_together = [('student', 'academic_year', 'fee_type', 'month')]
        ordering = ['student', 'academic_year', 'fee_type', 'month']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['due_amount']),
            models.Index(fields=['due_date']),
            models.Index(fields=['creation_source']),
        ]

    def __str__(self):
        month_str = f" - Month {self.month}" if self.month else ""
        return (f"{self.student.user.userprofile.full_name} - "
                f"{self.fee_type.name}{month_str} - Due: {self.due_amount}")

    def save(self, *args, **kwargs):
        """Auto-calculate due amount"""
        self.due_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)


# ============================================================================
# ATTENDANCE MANAGEMENT MODELS
# ============================================================================

class AttendanceCalendar(BaseModel):
    """
    Defines working days for each branch.
    Used to identify valid attendance days.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='attendance_calendars'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='attendance_calendars'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='attendance_calendars'
    )

    date = models.DateField()
    is_working_day = models.BooleanField(default=True)
    holiday_reason = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Reason if not a working day"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_calendars'
    )

    class Meta:
        db_table = 'attendance_calendars'
        unique_together = [('organization', 'academic_year', 'branch', 'date')]
        ordering = ['branch', 'date']
        indexes = [
            models.Index(fields=['organization', 'academic_year', 'branch']),
            models.Index(fields=['date', 'is_working_day']),
        ]

    def __str__(self):
        status = "Working" if self.is_working_day else "Holiday"
        return f"{self.branch.name} - {self.date} ({status})"


class StudentAttendance(BaseModel):
    """
    Daily attendance records for students.
    Linked to enrollment for year-specific tracking.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='student_attendances'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Which enrollment/year this attendance is for"
    )

    date = models.DateField()

    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='marked_student_attendance'
    )

    remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'student_attendances'
        unique_together = [('student', 'date')]
        ordering = ['-date', 'student']
        indexes = [
            models.Index(fields=['organization', 'date']),
            models.Index(fields=['enrollment', 'date']),
            models.Index(fields=['student', 'date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return (f"{self.student.user.userprofile.full_name} - "
                f"{self.date} - {self.get_status_display()}")


class StaffAttendance(BaseModel):
    """
    Daily attendance records for staff members.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='staff_attendances'
    )
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        limit_choices_to={'user_type__in': [
            'ADMIN', 'CHIEF_HEAD_TEACHER', 'HEAD_TEACHER',
            'TEACHER', 'ACCOUNTANT', 'OFFICE_STAFF'
        ]}
    )

    date = models.DateField()

    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'On Leave'),
        ('LATE', 'Late'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='marked_staff_attendance'
    )

    remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'staff_attendances'
        unique_together = [('staff', 'date')]
        ordering = ['-date', 'staff']
        indexes = [
            models.Index(fields=['organization', 'date']),
            models.Index(fields=['staff', 'date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return (f"{self.staff.userprofile.full_name} - "
                f"{self.date} - {self.get_status_display()}")


class LeaveRequest(BaseModel):
    """
    Staff leave request and approval tracking.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        limit_choices_to={'user_type__in': [
            'ADMIN', 'CHIEF_HEAD_TEACHER', 'HEAD_TEACHER',
            'TEACHER', 'ACCOUNTANT', 'OFFICE_STAFF'
        ]}
    )

    LEAVE_TYPE_CHOICES = [
        ('SICK', 'Sick Leave'),
        ('CASUAL', 'Casual Leave'),
        ('EMERGENCY', 'Emergency Leave'),
        ('ANNUAL', 'Annual Leave'),
        ('OTHER', 'Other'),
    ]
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)

    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_leaves'
    )
    review_remarks = models.TextField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'leave_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['requested_by', 'from_date', 'to_date']),
        ]

    def __str__(self):
        return (f"{self.requested_by.userprofile.full_name} - "
                f"{self.get_leave_type_display()} - "
                f"{self.from_date} to {self.to_date}")

    @property
    def total_days(self):
        """Calculate total leave days"""
        return (self.to_date - self.from_date).days + 1


# ============================================================================
# SUPPORTING MODELS
# ============================================================================

class SystemSetting(BaseModel):
    """
    Flexible system-wide configuration storage.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='system_settings'
    )

    key = models.CharField(max_length=100)
    value = models.JSONField()
    description = models.TextField(null=True, blank=True)
    category = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Group settings by category"
    )

    class Meta:
        db_table = 'system_settings'
        unique_together = [('organization', 'key')]
        ordering = ['category', 'key']
        indexes = [
            models.Index(fields=['organization', 'category']),
        ]

    def __str__(self):
        return f"{self.key} = {self.value}"


class AuditLog(BaseModel):
    """
    Comprehensive audit trail for all data changes.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    # What was changed
    entity_type = models.CharField(
        max_length=100,
        help_text="Model name (e.g., Student, FeeCollection)"
    )
    entity_id = models.UUIDField()

    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
    ]
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)

    # Change details
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['organization', 'entity_type', 'entity_id']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        user_str = self.user.userprofile.full_name if self.user else "System"
        return f"{user_str} {self.get_action_display()} {self.entity_type} at {self.timestamp}"


class EmailNotification(BaseModel):
    """
    Email queue and delivery tracking.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='email_notifications'
    )

    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()

    # Template support
    template_name = models.CharField(max_length=100, null=True, blank=True)
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Template context variables"
    )

    # Status tracking
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'email_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['recipient_email']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.subject} to {self.recipient_email} - {self.get_status_display()}"


class DocumentUpload(BaseModel):
    """
    Generic document storage linked to any entity.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )

    # Link to any entity
    entity_type = models.CharField(
        max_length=100,
        help_text="Model name this document belongs to"
    )
    entity_id = models.UUIDField()

    # File details
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField(help_text="Size in bytes")

    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'document_uploads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'entity_type', 'entity_id']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.entity_type})"