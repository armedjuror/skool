"""
Student Management Serializers

This module contains all serializers for student-related operations:
- Student listing and details
- Student CRUD operations
- Public registration form submission
- Pending registration management
"""

from rest_framework import serializers
from django.utils import timezone
from django.db import transaction

from main.models import (
    StudentProfile,
    StudentRegistration,
    StudentEnrollment,
    StudentFamily,
    StudentAcademicHistory,
    UserProfile,
    UserAddress,
    User,
    Branch,
    Class,
    Division,
    AcademicYear,
)


# =============================================================================
# NESTED SERIALIZERS (for read operations)
# =============================================================================

class BranchMinimalSerializer(serializers.ModelSerializer):
    """Minimal branch information for nested display"""
    class Meta:
        model = Branch
        fields = ['id', 'name', 'code']


class ClassMinimalSerializer(serializers.ModelSerializer):
    """Minimal class information for nested display"""
    class Meta:
        model = Class
        fields = ['id', 'name', 'level']


class DivisionMinimalSerializer(serializers.ModelSerializer):
    """Minimal division information for nested display"""
    class Meta:
        model = Division
        fields = ['id', 'name']


# =============================================================================
# STUDENT LIST SERIALIZER
# =============================================================================

class StudentListSerializer(serializers.ModelSerializer):
    """
    Serializer for student list view with essential information.
    Used for DataTable display with pagination.
    """
    name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    division_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    parent_mobile = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'admission_number',
            'name',
            'photo_url',
            'gender',
            'age',
            'class_name',
            'division_name',
            'branch_name',
            'parent_mobile',
            'status',
            'category',
            'created_at',
        ]

    def get_name(self, obj):
        try:
            return obj.user.userprofile.full_name
        except (AttributeError, UserProfile.DoesNotExist):
            return obj.user.email

    def get_photo_url(self, obj):
        try:
            if obj.user.userprofile.photo:
                return obj.user.userprofile.photo.url
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return None

    def get_gender(self, obj):
        try:
            return obj.user.userprofile.gender
        except (AttributeError, UserProfile.DoesNotExist):
            return None

    def get_age(self, obj):
        try:
            return obj.user.userprofile.age
        except (AttributeError, UserProfile.DoesNotExist):
            return None

    def get_class_name(self, obj):
        enrollment = obj.current_enrollment
        if enrollment:
            return enrollment.class_assigned.name
        return None

    def get_division_name(self, obj):
        enrollment = obj.current_enrollment
        if enrollment:
            return enrollment.division_assigned.name
        return None

    def get_branch_name(self, obj):
        if obj.branch:
            return obj.branch.name
        return None

    def get_parent_mobile(self, obj):
        try:
            return obj.family.parent_mobile
        except (AttributeError, StudentFamily.DoesNotExist):
            return None


# =============================================================================
# STUDENT DETAIL SERIALIZER
# =============================================================================

class StudentDetailSerializer(serializers.ModelSerializer):
    """
    Complete student information for detail view.
    Includes personal info, academic info, family, and addresses.
    """
    personal_info = serializers.SerializerMethodField()
    academic_info = serializers.SerializerMethodField()
    family_info = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()
    admission_info = serializers.SerializerMethodField()
    enrollment_history = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'admission_number',
            'category',
            'status',
            'has_siblings',
            'notes',
            'personal_info',
            'academic_info',
            'family_info',
            'addresses',
            'admission_info',
            'enrollment_history',
            'created_at',
            'updated_at',
        ]

    def get_personal_info(self, obj):
        try:
            profile = obj.user.userprofile
            return {
                'name': profile.full_name,
                'gender': profile.gender,
                'dob': profile.dob,
                'age': profile.age,
                'id_type': profile.id_card_type,
                'id_number': profile.id_card_number,
                'mobile': profile.mobile,
                'whatsapp': profile.whatsapp,
                'photo_url': profile.photo.url if profile.photo else None,
            }
        except (AttributeError, UserProfile.DoesNotExist):
            return None

    def get_academic_info(self, obj):
        enrollment = obj.current_enrollment
        if enrollment:
            teacher = enrollment.current_teacher
            return {
                'branch': BranchMinimalSerializer(obj.branch).data if obj.branch else None,
                'class': ClassMinimalSerializer(enrollment.class_assigned).data,
                'division': DivisionMinimalSerializer(enrollment.division_assigned).data,
                'academic_year': enrollment.academic_year.name,
                'enrollment_status': enrollment.enrollment_status,
                'enrollment_date': enrollment.enrollment_date,
                'teacher': {
                    'id': str(teacher.id),
                    'name': teacher.userprofile.full_name if hasattr(teacher, 'userprofile') else teacher.email
                } if teacher else None,
            }
        return None

    def get_family_info(self, obj):
        try:
            family = obj.family
            return {
                'father_name': family.father_name,
                'mother_name': family.mother_name,
                'parent_mobile': family.parent_mobile,
                'whatsapp': family.father_whatsapp,
                'email': family.email,
                'siblings_details': family.siblings_details,
                'has_siblings': obj.has_siblings,
            }
        except (AttributeError, StudentFamily.DoesNotExist):
            return None

    def get_addresses(self, obj):
        addresses = obj.user.addresses.all()
        result = {'qatar': None, 'india': None}

        for addr in addresses:
            if addr.address_type == 'QATAR':
                result['qatar'] = {
                    'place': addr.qatar_place,
                    'landmark': addr.qatar_landmark,
                    'building_no': addr.qatar_building_no,
                    'street_no': addr.qatar_street_no,
                    'zone_no': addr.qatar_zone_no,
                }
            elif addr.address_type == 'INDIA':
                result['india'] = {
                    'state': addr.india_state,
                    'district': addr.india_district,
                    'panchayath': addr.india_panchayath,
                    'place': addr.india_place,
                    'house_name': addr.india_house_name,
                    'contact_number': addr.india_contact,
                }

        return result

    def get_admission_info(self, obj):
        result = {
            'admission_date': obj.activated_at.date() if obj.activated_at else obj.created_at.date(),
        }

        # Get academic history
        history = obj.academic_history.first()
        if history:
            result.update({
                'previous_madrasa': history.previous_madrasa,
                'completed_classes': history.completed_classes,
                'tc_number': history.tc_number,
            })

        return result

    def get_enrollment_history(self, obj):
        enrollments = obj.enrollments.select_related(
            'academic_year', 'class_assigned', 'division_assigned'
        ).order_by('-academic_year__start_date')

        return [{
            'academic_year': e.academic_year.name,
            'class': e.class_assigned.name,
            'division': e.division_assigned.name,
            'enrollment_status': e.enrollment_status,
            'enrollment_date': e.enrollment_date,
            'attendance_percentage': e.attendance_percentage,
            'final_result': e.final_result,
        } for e in enrollments]


# =============================================================================
# STUDENT CREATE SERIALIZER
# =============================================================================

class StudentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new student (direct admission by admin).
    Creates User, UserProfile, StudentProfile, StudentEnrollment, and StudentFamily.
    """
    # Personal Information
    name = serializers.CharField(max_length=200)
    gender = serializers.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')])
    dob = serializers.DateField()
    id_card_type = serializers.ChoiceField(choices=[('QID', 'Qatar ID'), ('PASSPORT', 'Passport')])
    id_card_number = serializers.CharField(max_length=50)
    mobile = serializers.CharField(max_length=20, required=False, allow_blank=True)
    whatsapp = serializers.CharField(max_length=20, required=False, allow_blank=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    # Family Information
    father_name = serializers.CharField(max_length=200)
    mother_name = serializers.CharField(max_length=200)
    parent_mobile = serializers.CharField(max_length=20)
    father_whatsapp = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField()
    siblings_details = serializers.CharField(required=False, allow_blank=True)

    # Qatar Address
    qatar_place = serializers.CharField(max_length=200, required=False, allow_blank=True)
    qatar_landmark = serializers.CharField(max_length=200, required=False, allow_blank=True)
    qatar_building_no = serializers.CharField(max_length=50, required=False, allow_blank=True)
    qatar_street_no = serializers.CharField(max_length=50, required=False, allow_blank=True)
    qatar_zone_no = serializers.CharField(max_length=50, required=False, allow_blank=True)

    # India Address
    india_state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    india_district = serializers.CharField(max_length=100, required=False, allow_blank=True)
    india_panchayath = serializers.CharField(max_length=100, required=False, allow_blank=True)
    india_place = serializers.CharField(max_length=100, required=False, allow_blank=True)
    india_house_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    india_contact = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Academic Information
    branch_id = serializers.UUIDField()
    class_id = serializers.UUIDField()
    division_id = serializers.UUIDField()
    category = serializers.ChoiceField(choices=[('PERMANENT', 'Permanent'), ('TEMPORARY', 'Temporary')])

    # Optional Academic History
    previous_madrasa = serializers.CharField(max_length=200, required=False, allow_blank=True)
    completed_classes = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tc_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    aadhar_number = serializers.CharField(max_length=12, required=False, allow_blank=True)

    def validate_email(self, value):
        """Check if email is already in use"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_branch_id(self, value):
        """Validate branch exists and belongs to organization"""
        request = self.context.get('request')
        try:
            branch = Branch.objects.get(id=value, organization=request.user.organization, is_active=True)
            return branch
        except Branch.DoesNotExist:
            raise serializers.ValidationError("Invalid branch.")

    def validate_class_id(self, value):
        """Validate class exists and belongs to organization"""
        request = self.context.get('request')
        try:
            class_obj = Class.objects.get(id=value, organization=request.user.organization, is_active=True)
            return class_obj
        except Class.DoesNotExist:
            raise serializers.ValidationError("Invalid class.")

    def validate_division_id(self, value):
        """Validate division exists and belongs to organization"""
        request = self.context.get('request')
        try:
            division = Division.objects.get(id=value, organization=request.user.organization, is_active=True)
            return division
        except Division.DoesNotExist:
            raise serializers.ValidationError("Invalid division.")

    @transaction.atomic
    def create(self, validated_data):
        """Create student with all related records"""
        request = self.context.get('request')
        organization = request.user.organization

        # Get active academic year
        academic_year = AcademicYear.objects.filter(
            organization=organization,
            is_active=True
        ).first()

        if not academic_year:
            raise serializers.ValidationError({"academic_year": "No active academic year found."})

        # Extract nested data
        branch = validated_data.pop('branch_id')
        class_obj = validated_data.pop('class_id')
        division = validated_data.pop('division_id')

        # Create User
        user = User.objects.create_user(
            email=validated_data['email'],
            password=User.objects.make_random_password(),
            organization=organization,
            user_type='STUDENT',
            is_active=True
        )

        # Create UserProfile
        UserProfile.objects.create(
            user=user,
            full_name=validated_data['name'],
            gender=validated_data['gender'],
            dob=validated_data['dob'],
            id_card_type=validated_data['id_card_type'],
            id_card_number=validated_data['id_card_number'],
            mobile=validated_data.get('mobile') or validated_data['parent_mobile'],
            whatsapp=validated_data.get('whatsapp'),
            photo=validated_data.get('photo'),
        )

        # Create StudentProfile (admission_number auto-generated)
        student = StudentProfile.objects.create(
            user=user,
            branch=branch,
            category=validated_data['category'],
            status='ACTIVE',
            has_siblings=bool(validated_data.get('siblings_details')),
            activated_at=timezone.now(),
            activated_by=request.user,
        )

        # Create StudentEnrollment
        StudentEnrollment.objects.create(
            student=student,
            academic_year=academic_year,
            class_assigned=class_obj,
            division_assigned=division,
            enrollment_status='ENROLLED',
            enrollment_date=timezone.now().date(),
        )

        # Create StudentFamily
        StudentFamily.objects.create(
            student=student,
            father_name=validated_data['father_name'],
            mother_name=validated_data['mother_name'],
            parent_mobile=validated_data['parent_mobile'],
            father_whatsapp=validated_data.get('father_whatsapp'),
            email=validated_data['email'],
            siblings_details=validated_data.get('siblings_details'),
        )

        # Create Qatar Address
        if any([validated_data.get('qatar_place'), validated_data.get('qatar_zone_no')]):
            UserAddress.objects.create(
                user=user,
                address_type='QATAR',
                qatar_place=validated_data.get('qatar_place'),
                qatar_landmark=validated_data.get('qatar_landmark'),
                qatar_building_no=validated_data.get('qatar_building_no'),
                qatar_street_no=validated_data.get('qatar_street_no'),
                qatar_zone_no=validated_data.get('qatar_zone_no'),
            )

        # Create India Address
        if any([validated_data.get('india_state'), validated_data.get('india_place')]):
            UserAddress.objects.create(
                user=user,
                address_type='INDIA',
                india_state=validated_data.get('india_state'),
                india_district=validated_data.get('india_district'),
                india_panchayath=validated_data.get('india_panchayath'),
                india_place=validated_data.get('india_place'),
                india_house_name=validated_data.get('india_house_name'),
                india_contact=validated_data.get('india_contact'),
            )

        # Create Academic History if provided
        if any([validated_data.get('previous_madrasa'), validated_data.get('completed_classes')]):
            StudentAcademicHistory.objects.create(
                student=student,
                previous_madrasa=validated_data.get('previous_madrasa'),
                completed_classes=validated_data.get('completed_classes'),
                tc_number=validated_data.get('tc_number'),
            )

        return student


# =============================================================================
# STUDENT UPDATE SERIALIZER
# =============================================================================

class StudentUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating student information.
    Supports partial updates.
    """
    # Personal Information (optional for updates)
    name = serializers.CharField(max_length=200, required=False)
    gender = serializers.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')], required=False)
    dob = serializers.DateField(required=False)
    id_card_type = serializers.ChoiceField(
        choices=[('QID', 'Qatar ID'), ('PASSPORT', 'Passport')],
        required=False
    )
    id_card_number = serializers.CharField(max_length=50, required=False)
    mobile = serializers.CharField(max_length=20, required=False, allow_blank=True)
    whatsapp = serializers.CharField(max_length=20, required=False, allow_blank=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    # Family Information
    father_name = serializers.CharField(max_length=200, required=False)
    mother_name = serializers.CharField(max_length=200, required=False)
    parent_mobile = serializers.CharField(max_length=20, required=False)
    father_whatsapp = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    siblings_details = serializers.CharField(required=False, allow_blank=True)

    # Student Profile
    category = serializers.ChoiceField(
        choices=[('PERMANENT', 'Permanent'), ('TEMPORARY', 'Temporary')],
        required=False
    )
    status = serializers.ChoiceField(
        choices=[
            ('ACTIVE', 'Active'),
            ('INACTIVE', 'Inactive'),
            ('GRADUATED', 'Graduated'),
            ('TRANSFERRED', 'Transferred'),
            ('DROPPED', 'Dropped Out'),
        ],
        required=False
    )
    has_siblings = serializers.BooleanField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    # Academic (for changing class/division)
    branch_id = serializers.UUIDField(required=False)
    class_id = serializers.UUIDField(required=False)
    division_id = serializers.UUIDField(required=False)

    # Addresses
    qatar_place = serializers.CharField(max_length=200, required=False, allow_blank=True)
    qatar_landmark = serializers.CharField(max_length=200, required=False, allow_blank=True)
    qatar_building_no = serializers.CharField(max_length=50, required=False, allow_blank=True)
    qatar_street_no = serializers.CharField(max_length=50, required=False, allow_blank=True)
    qatar_zone_no = serializers.CharField(max_length=50, required=False, allow_blank=True)

    india_state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    india_district = serializers.CharField(max_length=100, required=False, allow_blank=True)
    india_panchayath = serializers.CharField(max_length=100, required=False, allow_blank=True)
    india_place = serializers.CharField(max_length=100, required=False, allow_blank=True)
    india_house_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    india_contact = serializers.CharField(max_length=20, required=False, allow_blank=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update student with related records"""
        request = self.context.get('request')

        # Update UserProfile
        profile = instance.user.userprofile
        profile_fields = ['full_name', 'gender', 'dob', 'id_card_type', 'id_card_number', 'mobile', 'whatsapp', 'photo']
        profile_mapping = {'name': 'full_name'}

        for field in profile_fields:
            source_field = next((k for k, v in profile_mapping.items() if v == field), field)
            if source_field in validated_data:
                setattr(profile, field, validated_data[source_field])

        profile.save()

        # Update StudentProfile
        student_fields = ['category', 'status', 'has_siblings', 'notes']
        for field in student_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        # Update branch if provided
        if 'branch_id' in validated_data:
            try:
                branch = Branch.objects.get(
                    id=validated_data['branch_id'],
                    organization=request.user.organization,
                    is_active=True
                )
                instance.branch = branch
            except Branch.DoesNotExist:
                raise serializers.ValidationError({"branch_id": "Invalid branch."})

        instance.save()

        # Update StudentFamily
        try:
            family = instance.family
        except StudentFamily.DoesNotExist:
            family = StudentFamily(student=instance)

        family_fields = ['father_name', 'mother_name', 'parent_mobile', 'father_whatsapp', 'email', 'siblings_details']
        for field in family_fields:
            if field in validated_data:
                setattr(family, field, validated_data[field])

        family.save()

        # Update Enrollment (class/division change)
        enrollment = instance.current_enrollment
        if enrollment and ('class_id' in validated_data or 'division_id' in validated_data):
            if 'class_id' in validated_data:
                try:
                    class_obj = Class.objects.get(
                        id=validated_data['class_id'],
                        organization=request.user.organization,
                        is_active=True
                    )
                    enrollment.class_assigned = class_obj
                except Class.DoesNotExist:
                    raise serializers.ValidationError({"class_id": "Invalid class."})

            if 'division_id' in validated_data:
                try:
                    division = Division.objects.get(
                        id=validated_data['division_id'],
                        organization=request.user.organization,
                        is_active=True
                    )
                    enrollment.division_assigned = division
                except Division.DoesNotExist:
                    raise serializers.ValidationError({"division_id": "Invalid division."})

            enrollment.save()

        # Update Addresses
        qatar_fields = ['qatar_place', 'qatar_landmark', 'qatar_building_no', 'qatar_street_no', 'qatar_zone_no']
        if any(f in validated_data for f in qatar_fields):
            qatar_addr, _ = UserAddress.objects.get_or_create(
                user=instance.user,
                address_type='QATAR'
            )
            for field in qatar_fields:
                if field in validated_data:
                    setattr(qatar_addr, field, validated_data[field])
            qatar_addr.save()

        india_fields = ['india_state', 'india_district', 'india_panchayath', 'india_place', 'india_house_name', 'india_contact']
        if any(f in validated_data for f in india_fields):
            india_addr, _ = UserAddress.objects.get_or_create(
                user=instance.user,
                address_type='INDIA'
            )
            for field in india_fields:
                if field in validated_data:
                    setattr(india_addr, field, validated_data[field])
            india_addr.save()

        return instance


# =============================================================================
# PUBLIC STUDENT REGISTRATION SERIALIZERS
# =============================================================================

class StudentRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for public student registration form submission.
    Creates a pending StudentRegistration record.
    """
    # Override fields for validation
    class_to_admit = serializers.UUIDField(source='class_to_admit_id', write_only=True)
    interested_branch = serializers.UUIDField(source='interested_branch_id', write_only=True)

    class Meta:
        model = StudentRegistration
        fields = [
            'admission_type',
            'student_name',
            'gender',
            'dob',
            'study_type',
            'id_card_type',
            'id_card_number',
            'photo',
            'father_name',
            'parent_mobile',
            'father_whatsapp',
            'email',
            'mother_name',
            'siblings_details',
            'qatar_address',
            'india_address',
            'class_to_admit',
            'interested_branch',
            'completed_classes',
            'previous_madrasa',
            'tc_number',
            'aadhar_number',
        ]

    def validate_class_to_admit(self, value):
        """Validate class exists"""
        organization = self.context.get('organization')
        if not Class.objects.filter(id=value, organization=organization, is_active=True).exists():
            raise serializers.ValidationError("Invalid class selected.")
        return value

    def validate_interested_branch(self, value):
        """Validate branch exists"""
        organization = self.context.get('organization')
        if not Branch.objects.filter(id=value, organization=organization, is_active=True).exists():
            raise serializers.ValidationError("Invalid branch selected.")
        return value

    def create(self, validated_data):
        """Create registration with organization context"""
        organization = self.context.get('organization')
        validated_data['organization'] = organization
        validated_data['status'] = 'PENDING'

        # Get actual objects for ForeignKey fields
        class_id = validated_data.pop('class_to_admit_id')
        branch_id = validated_data.pop('interested_branch_id')

        validated_data['class_to_admit'] = Class.objects.get(id=class_id)
        validated_data['interested_branch'] = Branch.objects.get(id=branch_id)

        return super().create(validated_data)


class StudentRegistrationVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying registration status.
    """
    registration_id = serializers.UUIDField(required=False)
    email = serializers.EmailField(required=False)

    def validate(self, attrs):
        if not attrs.get('registration_id') and not attrs.get('email'):
            raise serializers.ValidationError(
                "Either registration_id or email is required."
            )
        return attrs


# =============================================================================
# PENDING STUDENT REGISTRATION SERIALIZERS
# =============================================================================

class PendingStudentListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing pending student registrations.
    """
    interested_branch_name = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentRegistration
        fields = [
            'id',
            'student_name',
            'gender',
            'dob',
            'father_name',
            'parent_mobile',
            'email',
            'interested_branch_name',
            'class_name',
            'study_type',
            'status',
            'submission_date',
            'reviewed_at',
        ]

    def get_interested_branch_name(self, obj):
        return obj.interested_branch.name if obj.interested_branch else None

    def get_class_name(self, obj):
        return obj.class_to_admit.name if obj.class_to_admit else None


class PendingStudentDetailSerializer(serializers.ModelSerializer):
    """
    Complete pending registration details for review.
    """
    interested_branch = BranchMinimalSerializer(read_only=True)
    class_to_admit = ClassMinimalSerializer(read_only=True)
    photo_url = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentRegistration
        fields = [
            'id',
            'admission_type',
            'student_name',
            'gender',
            'dob',
            'study_type',
            'id_card_type',
            'id_card_number',
            'photo_url',
            'father_name',
            'parent_mobile',
            'father_whatsapp',
            'email',
            'mother_name',
            'siblings_details',
            'qatar_address',
            'india_address',
            'class_to_admit',
            'interested_branch',
            'completed_classes',
            'previous_madrasa',
            'tc_number',
            'aadhar_number',
            'status',
            'rejection_reason',
            'info_request_message',
            'reviewed_by_name',
            'reviewed_at',
            'submission_date',
        ]

    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            try:
                return obj.reviewed_by.userprofile.full_name
            except (AttributeError, UserProfile.DoesNotExist):
                return obj.reviewed_by.email
        return None


class PendingStudentApproveSerializer(serializers.Serializer):
    """
    Serializer for approving a pending student registration.
    Creates full student record on approval.
    """
    # Override the branch/class/division from registration if needed
    branch_id = serializers.UUIDField()
    class_id = serializers.UUIDField()
    division_id = serializers.UUIDField()
    category = serializers.ChoiceField(choices=[('PERMANENT', 'Permanent'), ('TEMPORARY', 'Temporary')])

    # Optional overrides
    has_siblings = serializers.BooleanField(required=False, default=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_branch_id(self, value):
        request = self.context.get('request')
        try:
            return Branch.objects.get(id=value, organization=request.user.organization, is_active=True)
        except Branch.DoesNotExist:
            raise serializers.ValidationError("Invalid branch.")

    def validate_class_id(self, value):
        request = self.context.get('request')
        try:
            return Class.objects.get(id=value, organization=request.user.organization, is_active=True)
        except Class.DoesNotExist:
            raise serializers.ValidationError("Invalid class.")

    def validate_division_id(self, value):
        request = self.context.get('request')
        try:
            return Division.objects.get(id=value, organization=request.user.organization, is_active=True)
        except Division.DoesNotExist:
            raise serializers.ValidationError("Invalid division.")

    @transaction.atomic
    def create(self, validated_data):
        """
        Approve registration and create student record.
        """
        registration = self.context.get('registration')
        request = self.context.get('request')
        organization = request.user.organization

        # Get active academic year
        academic_year = AcademicYear.objects.filter(
            organization=organization,
            is_active=True
        ).first()

        if not academic_year:
            raise serializers.ValidationError({"academic_year": "No active academic year found."})

        # Check if email already exists
        if User.objects.filter(email=registration.email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})

        branch = validated_data['branch_id']
        class_obj = validated_data['class_id']
        division = validated_data['division_id']

        # Create User
        user = User.objects.create_user(
            email=registration.email,
            password=User.objects.make_random_password(),
            organization=organization,
            user_type='STUDENT',
            is_active=True
        )

        # Create UserProfile
        UserProfile.objects.create(
            user=user,
            full_name=registration.student_name,
            gender=registration.gender,
            dob=registration.dob,
            id_card_type=registration.id_card_type,
            id_card_number=registration.id_card_number,
            mobile=registration.parent_mobile,
            whatsapp=registration.father_whatsapp,
            photo=registration.photo,
        )

        # Create StudentProfile
        student = StudentProfile.objects.create(
            user=user,
            registration=registration,
            branch=branch,
            category=validated_data['category'],
            status='ACTIVE',
            has_siblings=validated_data.get('has_siblings', False),
            notes=validated_data.get('notes', ''),
            activated_at=timezone.now(),
            activated_by=request.user,
        )

        # Create StudentEnrollment
        StudentEnrollment.objects.create(
            student=student,
            academic_year=academic_year,
            class_assigned=class_obj,
            division_assigned=division,
            enrollment_status='ENROLLED',
            enrollment_date=timezone.now().date(),
        )

        # Create StudentFamily
        StudentFamily.objects.create(
            student=student,
            father_name=registration.father_name,
            mother_name=registration.mother_name,
            parent_mobile=registration.parent_mobile,
            father_whatsapp=registration.father_whatsapp,
            email=registration.email,
            siblings_details=registration.siblings_details,
        )

        # Create Addresses from JSON
        qatar_addr = registration.qatar_address
        if qatar_addr:
            UserAddress.objects.create(
                user=user,
                address_type='QATAR',
                qatar_place=qatar_addr.get('place'),
                qatar_landmark=qatar_addr.get('landmark'),
                qatar_building_no=qatar_addr.get('building_no'),
                qatar_street_no=qatar_addr.get('street_no'),
                qatar_zone_no=qatar_addr.get('zone_no'),
            )

        india_addr = registration.india_address
        if india_addr:
            UserAddress.objects.create(
                user=user,
                address_type='INDIA',
                india_state=india_addr.get('state'),
                india_district=india_addr.get('district'),
                india_panchayath=india_addr.get('panchayath'),
                india_place=india_addr.get('place'),
                india_house_name=india_addr.get('house_name'),
                india_contact=india_addr.get('contact_number'),
            )

        # Create Academic History if available
        if registration.previous_madrasa or registration.completed_classes:
            StudentAcademicHistory.objects.create(
                student=student,
                previous_madrasa=registration.previous_madrasa,
                completed_classes=registration.completed_classes,
                tc_number=registration.tc_number,
            )

        # Update registration status
        registration.status = 'APPROVED'
        registration.reviewed_by = request.user
        registration.reviewed_at = timezone.now()
        registration.save()

        return student


class PendingStudentRejectSerializer(serializers.Serializer):
    """
    Serializer for rejecting a pending student registration.
    """
    rejection_reason = serializers.CharField(max_length=1000)

    def update(self, instance, validated_data):
        """Update registration with rejection"""
        request = self.context.get('request')

        instance.status = 'REJECTED'
        instance.rejection_reason = validated_data['rejection_reason']
        instance.reviewed_by = request.user
        instance.reviewed_at = timezone.now()
        instance.save()

        return instance


class PendingStudentRequestInfoSerializer(serializers.Serializer):
    """
    Serializer for requesting additional information from parent.
    """
    message = serializers.CharField(max_length=2000)

    def update(self, instance, validated_data):
        """Update registration with info request"""
        request = self.context.get('request')

        instance.status = 'INFO_REQUESTED'
        instance.info_request_message = validated_data['message']
        instance.reviewed_by = request.user
        instance.reviewed_at = timezone.now()
        instance.save()

        return instance