"""
Settings and Configuration Serializers

This module contains all serializers for settings-related operations:
- Academic Year CRUD
- Branch CRUD
- Class CRUD
- Division CRUD
- Staff CRUD
- System Settings CRUD
"""

from rest_framework import serializers
from django.utils import timezone
from django.db import transaction

from main.models import (
    AcademicYear,
    Branch,
    Class,
    Division,
    StaffProfile,
    SystemSetting,
    User,
    UserProfile,
    UserAddress,
)


# =============================================================================
# ACADEMIC YEAR SERIALIZERS
# =============================================================================

class AcademicYearListSerializer(serializers.ModelSerializer):
    """Serializer for academic year list view"""
    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active', 'created_at']


class AcademicYearDetailSerializer(serializers.ModelSerializer):
    """Serializer for academic year detail view"""
    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active', 'created_at', 'updated_at']


class AcademicYearCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new academic year"""
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_active']

    def validate_name(self, value):
        """Check if academic year name already exists in organization"""
        request = self.context.get('request')
        if AcademicYear.objects.filter(
            organization=request.user.organization,
            name=value
        ).exists():
            raise serializers.ValidationError("An academic year with this name already exists.")
        return value

    def validate(self, attrs):
        """Validate date range"""
        if attrs['start_date'] >= attrs['end_date']:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['organization'] = request.user.organization
        return super().create(validated_data)


class AcademicYearUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an academic year"""
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_active']

    def validate_name(self, value):
        """Check if academic year name already exists in organization"""
        request = self.context.get('request')
        instance = self.instance
        if AcademicYear.objects.filter(
            organization=request.user.organization,
            name=value
        ).exclude(id=instance.id).exists():
            raise serializers.ValidationError("An academic year with this name already exists.")
        return value

    def validate(self, attrs):
        """Validate date range"""
        start_date = attrs.get('start_date', self.instance.start_date)
        end_date = attrs.get('end_date', self.instance.end_date)
        if start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        return attrs


# =============================================================================
# BRANCH SERIALIZERS
# =============================================================================

class BranchListSerializer(serializers.ModelSerializer):
    """Serializer for branch list view"""
    head_teacher_name = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    staff_count = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'code', 'phone', 'email', 'address',
            'head_teacher_name', 'student_count', 'staff_count', 'is_active', 'created_at'
        ]

    def get_head_teacher_name(self, obj):
        if obj.head_teacher:
            try:
                return obj.head_teacher.userprofile.full_name
            except (AttributeError, UserProfile.DoesNotExist):
                return obj.head_teacher.email
        return None

    def get_student_count(self, obj):
        return obj.students.filter(status='ACTIVE').count()

    def get_staff_count(self, obj):
        return obj.staff_members.filter(status='ACTIVE').count()


class BranchDetailSerializer(serializers.ModelSerializer):
    """Serializer for branch detail view"""
    head_teacher_name = serializers.SerializerMethodField()
    head_teacher_id = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'code', 'address', 'phone', 'email', 'address',
            'head_teacher', 'head_teacher_id', 'head_teacher_name', 'is_active',
            'created_at', 'updated_at'
        ]

    def get_head_teacher_name(self, obj):
        if obj.head_teacher:
            try:
                return obj.head_teacher.userprofile.full_name
            except (AttributeError, UserProfile.DoesNotExist):
                return obj.head_teacher.email
        return None

    def get_head_teacher_id(self, obj):
        return str(obj.head_teacher.id) if obj.head_teacher else None


class BranchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new branch"""
    head_teacher_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Branch
        fields = ['name', 'code', 'address', 'phone', 'email', 'head_teacher_id', 'is_active']

    def validate_code(self, value):
        """Check if branch code already exists in organization"""
        request = self.context.get('request')
        if Branch.objects.filter(
            organization=request.user.organization,
            code=value.upper()
        ).exists():
            raise serializers.ValidationError("A branch with this code already exists.")
        return value.upper()

    def validate_head_teacher_id(self, value):
        """Validate head teacher exists and is eligible"""
        if value:
            request = self.context.get('request')
            try:
                user = User.objects.get(
                    id=value,
                    organization=request.user.organization,
                    user_type__in=['HEAD_TEACHER', 'CHIEF_HEAD_TEACHER'],
                    is_active=True
                )
                return user
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid head teacher.")
        return None

    def create(self, validated_data):
        request = self.context.get('request')
        head_teacher = validated_data.pop('head_teacher_id', None)
        validated_data['organization'] = request.user.organization
        validated_data['head_teacher'] = head_teacher
        return super().create(validated_data)


class BranchUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a branch"""
    head_teacher_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Branch
        fields = ['name', 'address', 'phone', 'email', 'head_teacher_id', 'is_active']

    # def validate_code(self, value):
    #     """Check if branch code already exists in organization"""
    #     request = self.context.get('request')
    #     instance = self.instance
    #     if Branch.objects.filter(
    #         organization=request.user.organization,
    #         code=value.upper()
    #     ).exclude(id=instance.id).exists():
    #         raise serializers.ValidationError("A branch with this code already exists.")
    #     return value.upper()

    def validate_head_teacher_id(self, value):
        """Validate head teacher exists and is eligible"""
        if value:
            request = self.context.get('request')
            try:
                user = User.objects.get(
                    id=value,
                    organization=request.user.organization,
                    user_type__in=['HEAD_TEACHER', 'CHIEF_HEAD_TEACHER'],
                    is_active=True
                )
                return user
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid head teacher.")
        return None

    def update(self, instance, validated_data):
        head_teacher = validated_data.pop('head_teacher_id', None)
        if 'head_teacher_id' in self.initial_data:
            instance.head_teacher = head_teacher
        return super().update(instance, validated_data)


# =============================================================================
# CLASS SERIALIZERS
# =============================================================================

class ClassListSerializer(serializers.ModelSerializer):
    """Serializer for class list view"""
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = ['id', 'name', 'level', 'is_active', 'student_count', 'created_at']

    def get_student_count(self, obj):
        return obj.enrolled_students.filter(
            enrollment_status='ENROLLED',
            academic_year__is_active=True
        ).count()


class ClassDetailSerializer(serializers.ModelSerializer):
    """Serializer for class detail view"""
    class Meta:
        model = Class
        fields = ['id', 'name', 'level', 'is_active', 'created_at', 'updated_at']


class ClassCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new class"""
    class Meta:
        model = Class
        fields = ['name', 'level', 'is_active']

    def validate_name(self, value):
        """Check if class name already exists in organization"""
        request = self.context.get('request')
        if Class.objects.filter(
            organization=request.user.organization,
            name=value
        ).exists():
            raise serializers.ValidationError("A class with this name already exists.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['organization'] = request.user.organization
        return super().create(validated_data)


class ClassUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a class"""
    class Meta:
        model = Class
        fields = ['name', 'level', 'is_active']

    def validate_name(self, value):
        """Check if class name already exists in organization"""
        request = self.context.get('request')
        instance = self.instance
        if Class.objects.filter(
            organization=request.user.organization,
            name=value
        ).exclude(id=instance.id).exists():
            raise serializers.ValidationError("A class with this name already exists.")
        return value


# =============================================================================
# DIVISION SERIALIZERS
# =============================================================================

class DivisionListSerializer(serializers.ModelSerializer):
    """Serializer for division list view"""
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Division
        fields = ['id', 'name', 'is_active', 'student_count', 'created_at']

    def get_student_count(self, obj):
        return obj.enrolled_students.filter(
            enrollment_status='ENROLLED',
            academic_year__is_active=True
        ).count()


class DivisionDetailSerializer(serializers.ModelSerializer):
    """Serializer for division detail view"""
    class Meta:
        model = Division
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at']


class DivisionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new division"""
    class Meta:
        model = Division
        fields = ['name', 'is_active']

    def validate_name(self, value):
        """Check if division name already exists in organization"""
        request = self.context.get('request')
        if Division.objects.filter(
            organization=request.user.organization,
            name=value
        ).exists():
            raise serializers.ValidationError("A division with this name already exists.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['organization'] = request.user.organization
        return super().create(validated_data)


class DivisionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a division"""
    class Meta:
        model = Division
        fields = ['name', 'is_active']

    def validate_name(self, value):
        """Check if division name already exists in organization"""
        request = self.context.get('request')
        instance = self.instance
        if Division.objects.filter(
            organization=request.user.organization,
            name=value
        ).exclude(id=instance.id).exists():
            raise serializers.ValidationError("A division with this name already exists.")
        return value


# =============================================================================
# STAFF SERIALIZERS
# =============================================================================

class StaffListSerializer(serializers.ModelSerializer):
    """Serializer for staff list view"""
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    user_type_display = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'staff_number', 'name', 'email', 'user_type', 'user_type_display',
            'category', 'status', 'branch_name', 'monthly_salary', 'photo_url', 'created_at'
        ]

    def get_name(self, obj):
        try:
            return obj.user.userprofile.full_name
        except (AttributeError, UserProfile.DoesNotExist):
            return obj.user.email

    def get_email(self, obj):
        return obj.user.email

    def get_user_type(self, obj):
        return obj.user.user_type

    def get_user_type_display(self, obj):
        return obj.user.get_user_type_display()

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else None

    def get_photo_url(self, obj):
        try:
            if obj.user.userprofile.photo:
                return obj.user.userprofile.photo.url
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return None


class StaffDetailSerializer(serializers.ModelSerializer):
    """Serializer for staff detail view"""
    personal_info = serializers.SerializerMethodField()
    employment_info = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'staff_number', 'category', 'status',
            'monthly_salary', 'other_allowances',
            'religious_academic_details', 'academic_details',
            'previous_madrasa', 'msr_number', 'aadhar_number', 'notes',
            'personal_info', 'employment_info', 'addresses',
            'created_at', 'updated_at'
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
                'email': obj.user.email,
                'photo_url': profile.photo.url if profile.photo else None,
            }
        except (AttributeError, UserProfile.DoesNotExist):
            return {'email': obj.user.email}

    def get_employment_info(self, obj):
        return {
            'user_type': obj.user.user_type,
            'user_type_display': obj.user.get_user_type_display(),
            'branch': {
                'id': str(obj.branch.id),
                'name': obj.branch.name,
                'code': obj.branch.code
            } if obj.branch else None,
            'assigned_head_teacher': {
                'id': str(obj.assigned_head_teacher.id),
                'name': obj.assigned_head_teacher.userprofile.full_name
            } if obj.assigned_head_teacher else None,
        }

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


class StaffCreateSerializer(serializers.Serializer):
    """Serializer for creating a new staff member"""
    # Personal Information
    name = serializers.CharField(max_length=200)
    gender = serializers.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')])
    dob = serializers.DateField()
    id_card_type = serializers.ChoiceField(choices=[('QID', 'Qatar ID'), ('PASSPORT', 'Passport')])
    id_card_number = serializers.CharField(max_length=50)
    mobile = serializers.CharField(max_length=20)
    whatsapp = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField()
    photo = serializers.ImageField(required=False, allow_null=True)

    # Employment Information
    user_type = serializers.ChoiceField(choices=[
        ('ADMIN', 'Admin'),
        ('CHIEF_HEAD_TEACHER', 'Chief Head Teacher'),
        ('HEAD_TEACHER', 'Head Teacher'),
        ('TEACHER', 'Teacher'),
        ('ACCOUNTANT', 'Accountant'),
        ('OFFICE_STAFF', 'Office Staff'),
    ])
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    category = serializers.ChoiceField(choices=[('PERMANENT', 'Permanent'), ('TEMPORARY', 'Temporary')])
    status = serializers.ChoiceField(
        choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')],
        default='ACTIVE'
    )
    monthly_salary = serializers.DecimalField(max_digits=10, decimal_places=2)
    other_allowances = serializers.JSONField(required=False, default=dict)

    # Academic Details
    religious_academic_details = serializers.CharField(required=False, allow_blank=True)
    academic_details = serializers.CharField(required=False, allow_blank=True)
    previous_madrasa = serializers.CharField(max_length=200, required=False, allow_blank=True)
    msr_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    aadhar_number = serializers.CharField(max_length=12, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

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

    def validate_email(self, value):
        """Check if email is already in use"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_branch_id(self, value):
        """Validate branch exists and belongs to organization"""
        if value:
            request = self.context.get('request')
            try:
                branch = Branch.objects.get(id=value, organization=request.user.organization, is_active=True)
                return branch
            except Branch.DoesNotExist:
                raise serializers.ValidationError("Invalid branch.")
        return None

    @transaction.atomic
    def create(self, validated_data):
        """Create staff with all related records"""
        request = self.context.get('request')
        organization = request.user.organization

        branch = validated_data.pop('branch_id', None)

        # Create User
        user = User.objects.create_user(
            email=validated_data['email'],
            password=User.objects.make_random_password(),
            organization=organization,
            user_type=validated_data['user_type'],
            is_active=True,
            is_staff=validated_data['user_type'] in ['ADMIN', 'CHIEF_HEAD_TEACHER']
        )

        # Create UserProfile
        UserProfile.objects.create(
            user=user,
            full_name=validated_data['name'],
            gender=validated_data['gender'],
            dob=validated_data['dob'],
            id_card_type=validated_data['id_card_type'],
            id_card_number=validated_data['id_card_number'],
            mobile=validated_data['mobile'],
            whatsapp=validated_data.get('whatsapp'),
            photo=validated_data.get('photo'),
        )

        # Create StaffProfile (staff_number auto-generated)
        staff = StaffProfile.objects.create(
            user=user,
            branch=branch,
            category=validated_data['category'],
            status=validated_data.get('status', 'ACTIVE'),
            monthly_salary=validated_data['monthly_salary'],
            other_allowances=validated_data.get('other_allowances', {}),
            religious_academic_details=validated_data.get('religious_academic_details'),
            academic_details=validated_data.get('academic_details'),
            previous_madrasa=validated_data.get('previous_madrasa'),
            msr_number=validated_data.get('msr_number'),
            aadhar_number=validated_data.get('aadhar_number'),
            notes=validated_data.get('notes'),
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

        return staff


class StaffUpdateSerializer(serializers.Serializer):
    """Serializer for updating staff information"""
    # Personal Information (optional for updates)
    name = serializers.CharField(max_length=200, required=False)
    gender = serializers.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')], required=False)
    dob = serializers.DateField(required=False)
    id_card_type = serializers.ChoiceField(
        choices=[('QID', 'Qatar ID'), ('PASSPORT', 'Passport')],
        required=False
    )
    id_card_number = serializers.CharField(max_length=50, required=False)
    mobile = serializers.CharField(max_length=20, required=False)
    whatsapp = serializers.CharField(max_length=20, required=False, allow_blank=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    # Employment Information
    user_type = serializers.ChoiceField(choices=[
        ('ADMIN', 'Admin'),
        ('CHIEF_HEAD_TEACHER', 'Chief Head Teacher'),
        ('HEAD_TEACHER', 'Head Teacher'),
        ('TEACHER', 'Teacher'),
        ('ACCOUNTANT', 'Accountant'),
        ('OFFICE_STAFF', 'Office Staff'),
    ], required=False)
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    category = serializers.ChoiceField(
        choices=[('PERMANENT', 'Permanent'), ('TEMPORARY', 'Temporary')],
        required=False
    )
    status = serializers.ChoiceField(
        choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')],
        required=False
    )
    monthly_salary = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    other_allowances = serializers.JSONField(required=False)

    # Academic Details
    religious_academic_details = serializers.CharField(required=False, allow_blank=True)
    academic_details = serializers.CharField(required=False, allow_blank=True)
    previous_madrasa = serializers.CharField(max_length=200, required=False, allow_blank=True)
    msr_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    aadhar_number = serializers.CharField(max_length=12, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

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
        """Update staff with related records"""
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

        # Update User type if provided
        if 'user_type' in validated_data:
            instance.user.user_type = validated_data['user_type']
            instance.user.save()

        # Update StaffProfile
        staff_fields = [
            'category', 'status', 'monthly_salary', 'other_allowances',
            'religious_academic_details', 'academic_details', 'previous_madrasa',
            'msr_number', 'aadhar_number', 'notes'
        ]
        for field in staff_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        # Update branch if provided
        if 'branch_id' in validated_data:
            branch_id = validated_data['branch_id']
            if branch_id:
                try:
                    branch = Branch.objects.get(
                        id=branch_id,
                        organization=request.user.organization,
                        is_active=True
                    )
                    instance.branch = branch
                except Branch.DoesNotExist:
                    raise serializers.ValidationError({"branch_id": "Invalid branch."})
            else:
                instance.branch = None

        instance.save()

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
# SYSTEM SETTINGS SERIALIZERS
# =============================================================================

class SystemSettingListSerializer(serializers.ModelSerializer):
    """Serializer for system settings list view"""
    class Meta:
        model = SystemSetting
        fields = ['id', 'key', 'value', 'description', 'category', 'created_at']


class SystemSettingDetailSerializer(serializers.ModelSerializer):
    """Serializer for system settings detail view"""
    class Meta:
        model = SystemSetting
        fields = ['id', 'key', 'value', 'description', 'category', 'created_at', 'updated_at']


class SystemSettingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new system setting"""
    class Meta:
        model = SystemSetting
        fields = ['key', 'value', 'description', 'category']

    def validate_key(self, value):
        """Check if setting key already exists in organization"""
        request = self.context.get('request')
        if SystemSetting.objects.filter(
            organization=request.user.organization,
            key=value
        ).exists():
            raise serializers.ValidationError("A setting with this key already exists.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['organization'] = request.user.organization
        return super().create(validated_data)


class SystemSettingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a system setting"""
    class Meta:
        model = SystemSetting
        fields = ['key', 'value', 'description', 'category']

    def validate_key(self, value):
        """Check if setting key already exists in organization"""
        request = self.context.get('request')
        instance = self.instance
        if SystemSetting.objects.filter(
            organization=request.user.organization,
            key=value
        ).exclude(id=instance.id).exists():
            raise serializers.ValidationError("A setting with this key already exists.")
        return value