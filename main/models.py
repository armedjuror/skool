from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, FileExtensionValidator
from django.utils import timezone
from django.db.models import Max


class Organization(models.Model):
    id = models.AutoField(editable=False, primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    contact_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name


class Branch(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='branches')
    code = models.CharField(max_length=4, primary_key=True, help_text="4-letter branch code (e.g., WAKR)")
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_next_admission_number(self):
        """Generate next admission number for this branch"""
        last_student = Student.objects.filter(branch=self).aggregate(Max('admission_number'))
        last_number = last_student['admission_number__max']
        
        if last_number:
            # Extract numeric part and increment
            try:
                numeric_part = int(last_number[4:])  # Skip branch code
                next_number = numeric_part + 1
            except:
                next_number = 1
        else:
            next_number = 1
        
        return f"{self.code}{next_number:04d}"


CLASS_CHOICES = [
    ('I', 'Class I'),
    ('II', 'Class II'),
    ('III', 'Class III'),
    ('IV', 'Class IV'),
    ('V', 'Class V'),
    ('VI', 'Class VI'),
    ('VII', 'Class VII'),
    ('VIII', 'Class VIII'),
    ('IX', 'Class IX'),
    ('X', 'Class X'),
    ('XI', 'Class XI'),
    ('XII', 'Class XII'),
]

class Class(models.Model):
    name = models.CharField(max_length=10, unique=True)
    level = models.CharField(max_length=10, choices=CLASS_CHOICES)
    division = models.CharField(max_length=10, blank=True)
    description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, help_text="e.g., 2024-2025")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False, help_text="Only one academic year can be active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'
    
    def save(self, *args, **kwargs):
        # Ensure only one academic year is active
        if self.is_active:
            AcademicYear.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class UserDetail(User):
    USER_TYPES = (
        ('ADMIN', 'Admin'),
        ('HEAD_TEACHER', 'Head Teacher'),
        ('ACCOUNTANT', 'Accountant'),
        ('OFFICE_STAFF', 'Office Staff'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    # photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)
    max_devices = models.IntegerField(default=-1, help_text="Maximum devices allowed")
    is_active_user = models.BooleanField(default=False, help_text="Whether user account is active")
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"


# class DeviceSession(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_sessions')
#     device_id = models.CharField(max_length=255, help_text="Unique device identifier")
#     device_name = models.CharField(max_length=100, blank=True)
#     ip_address = models.GenericIPAddressField(null=True, blank=True)
#     user_agent = models.TextField(blank=True)
#     last_activity = models.DateTimeField(auto_now=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_active = models.BooleanField(default=True)
#
#     class Meta:
#         unique_together = ('user', 'device_id')
#         ordering = ['-last_activity']
#
#     def __str__(self):
#         return f"{self.user.username} - {self.device_name or self.device_id}"
#
#
#
#
#
#
#
#     def __str__(self):
#         return self.get_name_display()

#
# class Student(models.Model):
#     """
#     Student profile with complete registration details
#     """
#     ADMISSION_TYPES = (
#         ('NEW', 'New Admission'),
#         ('EXISTING', 'Existing Update'),
#     )
#
#     GENDER_CHOICES = (
#         ('MALE', 'Male'),
#         ('FEMALE', 'Female'),
#     )
#
#     STUDY_TYPES = (
#         ('PERMANENT', 'Permanent'),
#         ('TEMPORARY', 'Temporary'),
#     )
#
#     ID_CARD_TYPES = (
#         ('QID', 'QID'),
#         ('PASSPORT', 'Passport'),
#     )
#
#     STATUS_CHOICES = (
#         ('PENDING', 'Pending Approval'),
#         ('APPROVED', 'Approved'),
#         ('REJECTED', 'Rejected'),
#         ('ACTIVE', 'Active'),
#         ('INACTIVE', 'Inactive'),
#     )
#
#     # User account link
#     user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='student_profile')
#
#     # Section 1: Personal Details
#     admission_type = models.CharField(max_length=10, choices=ADMISSION_TYPES, default='NEW')
#     student_name = models.CharField(max_length=200)
#     gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
#     date_of_birth = models.DateField()
#     age = models.IntegerField(editable=False, null=True)
#     study_type = models.CharField(max_length=10, choices=STUDY_TYPES)
#     id_card_type = models.CharField(max_length=10, choices=ID_CARD_TYPES)
#     id_number = models.CharField(max_length=50, verbose_name="QID/Passport Number")
#     # photo = models.ImageField(
#     #     upload_to='student_photos/',
#     #     validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
#     #     blank=True,
#     #     null=True
#     # )
#
#     # Section 2: Family Details
#     father_name = models.CharField(max_length=200)
#     parent_mobile = models.CharField(
#         max_length=15,
#         validators=[RegexValidator(regex=r'^\d+$', message='Enter digits only')]
#     )
#     father_whatsapp = models.CharField(
#         max_length=15,
#         validators=[RegexValidator(regex=r'^\d+$', message='Enter digits only')],
#         blank=True
#     )
#     email = models.EmailField()
#     mother_name = models.CharField(max_length=200)
#     siblings_details = models.TextField(blank=True)
#
#     # Section 3: Address in Qatar
#     place_qatar = models.CharField(max_length=200)
#     landmark_qatar = models.CharField(max_length=200, blank=True)
#     building_number = models.CharField(max_length=20)
#     street_number = models.CharField(max_length=20)
#     zone_number = models.CharField(max_length=20)
#
#     # Section 4: Address in India
#     STATE_CHOICES = [
#         ('KERALA', 'Kerala'),
#         ('TAMIL_NADU', 'Tamil Nadu'),
#         ('KARNATAKA', 'Karnataka'),
#         # Add more states as needed
#     ]
#     state_india = models.CharField(max_length=50, choices=STATE_CHOICES)
#     district_india = models.CharField(max_length=100)
#     panchayath = models.CharField(max_length=100, blank=True)
#     place_name_india = models.CharField(max_length=100)
#     house_name_india = models.CharField(max_length=100)
#     contact_number_india = models.CharField(
#         max_length=15,
#         validators=[RegexValidator(regex=r'^\d+$', message='Enter digits only')]
#     )
#
#     # Section 5: Academic Details
#     class_to_admit = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students_to_admit')
#     interested_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='interested_students')
#     completed_classes = models.CharField(max_length=10, blank=True)
#     previous_madrasa = models.CharField(max_length=200, blank=True)
#     tc_number = models.CharField(max_length=50, blank=True, verbose_name="TC Number")
#     aadhar_number = models.CharField(
#         max_length=12,
#         blank=True,
#         validators=[RegexValidator(regex=r'^\d{12}$', message='Enter 12 digits')]
#     )
#
#     # Admin Assignment Fields (Post-Approval)
#     student_category = models.CharField(max_length=10, choices=STUDY_TYPES, blank=True)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
#     branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
#     assigned_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_students')
#     division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
#     teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_students')
#
#     # Fee Details
#     monthly_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     other_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     has_siblings = models.BooleanField(default=False)
#
#     # Admission Number (generated after approval)
#     admission_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
#
#     # Metadata
#     notes = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     approved_at = models.DateTimeField(null=True, blank=True)
#     approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_students')
#
#     class Meta:
#         ordering = ['-created_at']
#         verbose_name = 'Student'
#         verbose_name_plural = 'Students'
#
#     def save(self, *args, **kwargs):
#         # Calculate age from date of birth
#         if self.date_of_birth:
#             today = timezone.now().date()
#             self.age = today.year - self.date_of_birth.year - (
#                 (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
#             )
#
#         # Generate admission number when status changes to ACTIVE
#         if self.status == 'ACTIVE' and not self.admission_number and self.branch:
#             self.admission_number = self.branch.get_next_admission_number()
#
#         super().save(*args, **kwargs)
#
#     def __str__(self):
#         return f"{self.student_name} ({self.admission_number or 'Pending'})"
#
#
# class Teacher(models.Model):
#     """
#     Teacher/Staff profile
#     """
#     STAFF_CATEGORY = (
#         ('PERMANENT', 'Permanent'),
#         ('TEMPORARY', 'Temporary'),
#     )
#
#     STAFF_ROLE = (
#         ('STAFF', 'Staff'),
#         ('HEAD_TEACHER', 'Head Teacher'),
#         ('TEACHER', 'Teacher'),
#     )
#
#     STATUS_CHOICES = (
#         ('PENDING', 'Pending Approval'),
#         ('APPROVED', 'Approved'),
#         ('REJECTED', 'Rejected'),
#         ('ACTIVE', 'Active'),
#         ('INACTIVE', 'Inactive'),
#     )
#
#     # User account link
#     user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='teacher_profile')
#
#     # Personal Details
#     name = models.CharField(max_length=200, verbose_name="Name (As per QID/Passport)")
#     gender = models.CharField(max_length=10, choices=Student.GENDER_CHOICES)
#     date_of_birth = models.DateField()
#     age = models.IntegerField(editable=False, null=True)
#     id_card_type = models.CharField(max_length=10, choices=Student.ID_CARD_TYPES)
#     id_number = models.CharField(max_length=50)
#     mobile_number = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\d+$')])
#     whatsapp_number = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\d+$')], blank=True)
#     email = models.EmailField()
#     # photo = models.ImageField(upload_to='teacher_photos/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])], blank=True, null=True)
#
#     # Address in Qatar
#     place_qatar = models.CharField(max_length=200)
#     landmark = models.CharField(max_length=200, blank=True)
#     building_number = models.CharField(max_length=20)
#     street_number = models.CharField(max_length=20)
#     zone_number = models.CharField(max_length=20)
#
#     # Address in India
#     state_india = models.CharField(max_length=50, choices=Student.STATE_CHOICES)
#     district_india = models.CharField(max_length=100)
#     panchayath = models.CharField(max_length=100, blank=True)
#     place_name_india = models.CharField(max_length=100)
#     house_name_india = models.CharField(max_length=100)
#     contact_number_india = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\d+$')])
#
#     # Academic Details
#     religious_academic_details = models.TextField()
#     academic_details = models.TextField()
#     interested_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='interested_teachers')
#     previous_madrasa = models.CharField(max_length=200, blank=True)
#     msr_number = models.CharField(max_length=50, blank=True, verbose_name="MSR Number")
#     aadhar_number = models.CharField(max_length=12, blank=True, validators=[RegexValidator(regex=r'^\d{12}$')])
#
#     # Admin Assignment Fields
#     staff_category = models.CharField(max_length=10, choices=STAFF_CATEGORY, blank=True)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
#     staff_role = models.CharField(max_length=20, choices=STAFF_ROLE, blank=True)
#     branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='teachers')
#     assigned_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True)
#     division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
#     head_teacher = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_teachers')
#
#     # Salary Details
#     monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     other_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Overtime, Transport, Food, Mobile Allowance")
#
#     # Staff Number
#     staff_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
#
#     # Metadata
#     notes = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     approved_at = models.DateTimeField(null=True, blank=True)
#     approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_teachers')
#
#     class Meta:
#         ordering = ['-created_at']
#         verbose_name = 'Teacher/Staff'
#         verbose_name_plural = 'Teachers/Staff'
#
#     def save(self, *args, **kwargs):
#         # Calculate age
#         if self.date_of_birth:
#             today = timezone.now().date()
#             self.age = today.year - self.date_of_birth.year - (
#                 (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
#             )
#
#         # Generate staff number when status changes to ACTIVE
#         if self.status == 'ACTIVE' and not self.staff_number:
#             last_staff = Teacher.objects.filter(staff_number__isnull=False).aggregate(Max('staff_number'))
#             last_number = last_staff['staff_number__max']
#
#             if last_number:
#                 try:
#                     numeric_part = int(last_number[3:])
#                     next_number = numeric_part + 1
#                 except:
#                     next_number = 1
#             else:
#                 next_number = 1
#
#             self.staff_number = f"KIC{next_number:03d}"
#
#         super().save(*args, **kwargs)
#
#     def __str__(self):
#         return f"{self.name} ({self.staff_number or 'Pending'})"
#
#
# class AuditLog(models.Model):
#     """
#     Track all changes to critical data
#     """
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
#     action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE, LOGIN, etc.
#     model_name = models.CharField(max_length=50)
#     object_id = models.IntegerField(null=True, blank=True)
#     changes = models.JSONField(default=dict, blank=True)
#     ip_address = models.GenericIPAddressField(null=True, blank=True)
#     timestamp = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         ordering = ['-timestamp']
#         verbose_name = 'Audit Log'
#         verbose_name_plural = 'Audit Logs'
#
#     def __str__(self):
#         return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"