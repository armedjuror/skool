"""
Django Admin Configuration for All Models
Complete admin interface with custom filters, actions, and display options

This file should be split across apps:
- apps/core/admin.py
- apps/users/admin.py
- apps/students/admin.py
- apps/fees/admin.py
- apps/attendance/admin.py
- apps/common/admin.py

Author: Backend Team
Date: December 31, 2024
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from datetime import timedelta

# Import all models (adjust imports based on your app structure)
from main.models import ( Organization, Branch, AcademicYear, Class, Division,
                          User, UserProfile, UserAddress, StaffProfile,
                          TeacherAssignment, StudentRegistration, StudentProfile,
                          StudentEnrollment, StudentFamily, StudentAcademicHistory,
                          FeeType, FeeStructure, StudentFeeConfiguration,
                          FeeCollection, FeeCollectionItem, StudentFeeDue,
                          AttendanceCalendar, StudentAttendance, StaffAttendance, LeaveRequest,
                          SystemSetting, AuditLog, EmailNotification, DocumentUpload
                          )


# ============================================================================
# CORE ORGANIZATION ADMIN
# ============================================================================

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'logo', 'is_active')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Settings', {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'head_teacher_name', 'contact_person', 'is_active']
    list_filter = ['organization', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'contact_person']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['organization', 'head_teacher']

    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'name', 'code', 'is_active')
        }),
        ('Head Teacher', {
            'fields': ('head_teacher',)
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'phone', 'email', 'address')
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def head_teacher_name(self, obj):
        if obj.head_teacher:
            return obj.head_teacher.userprofile.full_name
        return '-'

    head_teacher_name.short_description = 'Head Teacher'


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'start_date', 'end_date', 'is_active_badge', 'created_at']
    list_filter = ['organization', 'is_active', 'start_date']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['organization']

    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'name', 'is_active')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: gray;">Inactive</span>')

    is_active_badge.short_description = 'Status'

    actions = ['make_active']

    def make_active(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one academic year to activate.", level='error')
            return

        academic_year = queryset.first()
        # Deactivate all others in same organization
        AcademicYear.objects.filter(
            organization=academic_year.organization
        ).update(is_active=False)

        # Activate selected
        academic_year.is_active = True
        academic_year.save()

        self.message_user(request, f"{academic_year.name} is now active.")

    make_active.short_description = "Set as active academic year"


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'organization', 'display_order', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'level']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['organization']
    ordering = ['organization', 'display_order']

    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'name', 'level', 'display_order', 'is_active')
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['organization']
    ordering = ['organization', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'name', 'is_active')
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# USER MANAGEMENT ADMIN
# ============================================================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ['full_name', 'gender', 'dob', 'age', 'id_card_type', 'id_card_number',
              'mobile', 'whatsapp', 'photo']
    readonly_fields = ['age']


class UserAddressInline(admin.TabularInline):
    model = UserAddress
    extra = 0
    verbose_name_plural = 'Addresses'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'user_type', 'organization', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['user_type', 'organization', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'userprofile__full_name']
    ordering = ['organization', 'user_type', 'email']

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Organization & Role', {
            'fields': ('organization', 'user_type')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'organization', 'user_type', 'password1', 'password2'),
        }),
    )

    inlines = [UserProfileInline, UserAddressInline]

    def get_full_name(self, obj):
        if hasattr(obj, 'userprofile'):
            return obj.userprofile.full_name
        return obj.email

    get_full_name.short_description = 'Full Name'


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['staff_number', 'get_name', 'user_type', 'category', 'status',
                    'branch', 'monthly_salary']
    list_filter = ['status', 'category', 'branch', 'user__user_type']
    search_fields = ['staff_number', 'user__userprofile__full_name', 'user__email']
    readonly_fields = ['staff_number', 'created_at', 'updated_at']
    autocomplete_fields = ['user', 'branch', 'assigned_head_teacher']

    fieldsets = (
        ('Staff Information', {
            'fields': ('user', 'staff_number', 'category', 'status')
        }),
        ('Assignment', {
            'fields': ('branch', 'assigned_head_teacher')
        }),
        ('Compensation', {
            'fields': ('monthly_salary', 'other_allowances')
        }),
        ('Academic Credentials', {
            'fields': ('religious_academic_details', 'academic_details',
                       'previous_madrasa', 'msr_number', 'aadhar_number'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_name(self, obj):
        return obj.user.userprofile.full_name

    get_name.short_description = 'Name'

    def user_type(self, obj):
        return obj.user.get_user_type_display()

    user_type.short_description = 'Role'

    actions = ['activate_staff', 'deactivate_staff']

    def activate_staff(self, request, queryset):
        updated = queryset.update(status='ACTIVE')
        self.message_user(request, f"{updated} staff members activated.")

    activate_staff.short_description = "Activate selected staff"

    def deactivate_staff(self, request, queryset):
        updated = queryset.update(status='INACTIVE')
        self.message_user(request, f"{updated} staff members deactivated.")

    deactivate_staff.short_description = "Deactivate selected staff"


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ['get_teacher_name', 'branch', 'get_class_division', 'academic_year',
                    'start_date', 'end_date', 'assignment_type', 'is_active']
    list_filter = ['branch', 'academic_year', 'assignment_type', 'is_active', 'start_date']
    search_fields = ['teacher__userprofile__full_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['teacher', 'branch', 'academic_year', 'class_assigned',
                           'division_assigned', 'replaced_by']
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Teacher & Assignment', {
            'fields': ('teacher', 'branch', 'academic_year', 'class_assigned',
                       'division_assigned')
        }),
        ('Assignment Details', {
            'fields': ('assignment_type', 'start_date', 'end_date', 'is_primary', 'is_active')
        }),
        ('Change Information', {
            'fields': ('change_reason', 'replaced_by', 'remarks'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_teacher_name(self, obj):
        return obj.teacher.userprofile.full_name

    get_teacher_name.short_description = 'Teacher'

    def get_class_division(self, obj):
        return f"{obj.class_assigned.name} - {obj.division_assigned.name}"

    get_class_division.short_description = 'Class-Division'


# ============================================================================
# STUDENT LIFECYCLE ADMIN
# ============================================================================

@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'submission_date', 'admission_type', 'study_type',
                    'interested_branch', 'status_badge', 'reviewed_by']
    list_filter = ['status', 'admission_type', 'study_type', 'interested_branch',
                   'submission_date']
    search_fields = ['student_name', 'father_name', 'email', 'parent_mobile',
                     'id_card_number']
    readonly_fields = ['submission_date', 'created_at', 'updated_at']
    autocomplete_fields = ['organization', 'interested_branch', 'class_to_admit',
                           'reviewed_by']
    date_hierarchy = 'submission_date'

    fieldsets = (
        ('Submission Info', {
            'fields': ('organization', 'admission_type', 'submission_date', 'status')
        }),
        ('Student Details', {
            'fields': ('student_name', 'gender', 'dob', 'study_type', 'id_card_type',
                       'id_card_number', 'photo')
        }),
        ('Family Details', {
            'fields': ('father_name', 'mother_name', 'parent_mobile', 'father_whatsapp',
                       'email', 'siblings_details')
        }),
        ('Addresses', {
            'fields': ('qatar_address', 'india_address'),
            'classes': ('collapse',)
        }),
        ('Academic Preference', {
            'fields': ('class_to_admit', 'interested_branch', 'completed_classes',
                       'previous_madrasa', 'tc_number', 'aadhar_number')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'rejection_reason',
                       'info_request_message'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'APPROVED': 'green',
            'REJECTED': 'red',
            'INFO_REQUESTED': 'blue',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    actions = ['approve_registrations', 'reject_registrations']

    def approve_registrations(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} registrations approved.")

    approve_registrations.short_description = "Approve selected registrations"

    def reject_registrations(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='REJECTED',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} registrations rejected.")

    reject_registrations.short_description = "Reject selected registrations"


class StudentEnrollmentInline(admin.TabularInline):
    model = StudentEnrollment
    extra = 0
    fields = ['academic_year', 'class_assigned', 'division_assigned',
              'enrollment_status', 'enrollment_date']
    readonly_fields = ['enrollment_date']
    autocomplete_fields = ['academic_year', 'class_assigned', 'division_assigned']


class StudentFamilyInline(admin.StackedInline):
    model = StudentFamily
    can_delete = False
    verbose_name_plural = 'Family Information'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'get_name', 'category', 'status', 'branch',
                    'get_current_class', 'activated_at']
    list_filter = ['status', 'category', 'branch', 'activated_at']
    search_fields = ['admission_number', 'user__userprofile__full_name',
                     'user__email', 'family__parent_mobile']
    readonly_fields = ['admission_number', 'activated_at', 'created_at', 'updated_at']
    autocomplete_fields = ['user', 'branch', 'registration', 'activated_by']

    fieldsets = (
        ('Student Information', {
            'fields': ('user', 'admission_number', 'registration', 'category', 'status')
        }),
        ('Branch Assignment', {
            'fields': ('branch',)
        }),
        ('Additional Info', {
            'fields': ('has_siblings', 'notes')
        }),
        ('Activation', {
            'fields': ('activated_by', 'activated_at'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [StudentFamilyInline, StudentEnrollmentInline]

    def get_name(self, obj):
        return obj.user.userprofile.full_name

    get_name.short_description = 'Name'

    def get_current_class(self, obj):
        enrollment = obj.current_enrollment
        if enrollment:
            return f"{enrollment.class_assigned.name} - {enrollment.division_assigned.name}"
        return '-'

    get_current_class.short_description = 'Current Class'

    actions = ['activate_students', 'deactivate_students']

    def activate_students(self, request, queryset):
        count = 0
        for student in queryset:
            if student.status != 'ACTIVE':
                student.status = 'ACTIVE'
                student.activated_by = request.user
                student.activated_at = timezone.now()
                student.save()
                count += 1

        self.message_user(request, f"{count} students activated.")

    activate_students.short_description = "Activate selected students"

    def deactivate_students(self, request, queryset):
        updated = queryset.update(status='INACTIVE')
        self.message_user(request, f"{updated} students deactivated.")

    deactivate_students.short_description = "Deactivate selected students"


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['get_student_name', 'get_admission_number', 'academic_year',
                    'get_class_division', 'enrollment_status', 'enrollment_date',
                    'attendance_percentage']
    list_filter = ['academic_year', 'enrollment_status', 'class_assigned',
                   'division_assigned', 'enrollment_date']
    search_fields = ['student__admission_number', 'student__user__userprofile__full_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['student', 'academic_year', 'class_assigned',
                           'division_assigned', 'promoted_to']
    date_hierarchy = 'enrollment_date'

    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'academic_year', 'enrollment_date', 'enrollment_status')
        }),
        ('Class Assignment', {
            'fields': ('class_assigned', 'division_assigned')
        }),
        ('Performance', {
            'fields': ('attendance_percentage', 'final_result'),
            'classes': ('collapse',)
        }),
        ('Promotion', {
            'fields': ('completion_date', 'promoted_to'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )

    def get_student_name(self, obj):
        return obj.student.user.userprofile.full_name

    get_student_name.short_description = 'Student'

    def get_admission_number(self, obj):
        return obj.student.admission_number

    get_admission_number.short_description = 'Admission #'

    def get_class_division(self, obj):
        return f"{obj.class_assigned.name} - {obj.division_assigned.name}"

    get_class_division.short_description = 'Class-Division'

    actions = ['promote_students', 'mark_completed']

    def promote_students(self, request, queryset):
        count = queryset.filter(enrollment_status='ENROLLED').update(
            enrollment_status='PROMOTED',
            completion_date=timezone.now().date()
        )
        self.message_user(request, f"{count} students marked as promoted.")

    promote_students.short_description = "Mark as promoted"

    def mark_completed(self, request, queryset):
        count = queryset.update(
            enrollment_status='COMPLETED',
            completion_date=timezone.now().date()
        )
        self.message_user(request, f"{count} enrollments marked as completed.")

    mark_completed.short_description = "Mark as completed"


@admin.register(StudentAcademicHistory)
class StudentAcademicHistoryAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'previous_madrasa', 'previous_class', 'year', 'tc_number']
    list_filter = ['year']
    search_fields = ['student__admission_number', 'student__user__userprofile__full_name',
                     'previous_madrasa']
    autocomplete_fields = ['student']

    def get_student(self, obj):
        return f"{obj.student.admission_number} - {obj.student.user.userprofile.full_name}"

    get_student.short_description = 'Student'


# ============================================================================
# FEE MANAGEMENT ADMIN
# ============================================================================

@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'charge_trigger', 'charge_month', 'is_recurring',
                    'is_active']
    list_filter = ['category', 'charge_trigger', 'is_recurring', 'is_active', 'organization']
    search_fields = ['name', 'description']
    autocomplete_fields = ['organization']

    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'name', 'description', 'category')
        }),
        ('Auto-Creation Settings', {
            'fields': ('charge_trigger', 'charge_month', 'is_recurring')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['fee_type', 'amount', 'branch', 'class_level', 'academic_year',
                    'applicable_to', 'auto_create_due', 'is_active']
    list_filter = ['organization', 'academic_year', 'branch', 'class_level',
                   'applicable_to', 'is_active']
    search_fields = ['fee_type__name']
    autocomplete_fields = ['organization', 'academic_year', 'branch', 'class_level',
                           'fee_type']

    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'academic_year', 'fee_type', 'amount')
        }),
        ('Applicability', {
            'fields': ('branch', 'class_level', 'applicable_to')
        }),
        ('Validity Period', {
            'fields': ('effective_from', 'effective_to')
        }),
        ('Auto-Creation', {
            'fields': ('auto_create_due', 'due_days_after_trigger')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    actions = ['create_dues_for_all_students']

    def create_dues_for_all_students(self, request, queryset):
        """Bulk create fee dues for selected fee structures"""
        from main.tasks import get_applicable_fee_structure, get_student_fee_amount

        total_created = 0

        for fee_structure in queryset:
            # Get all enrolled students for this academic year
            enrollments = StudentEnrollment.objects.filter(
                academic_year=fee_structure.academic_year,
                enrollment_status='ENROLLED'
            )

            # Filter by branch if specified
            if fee_structure.branch:
                enrollments = enrollments.filter(
                    student__branch=fee_structure.branch
                )

            # Filter by class if specified
            if fee_structure.class_level:
                enrollments = enrollments.filter(
                    class_assigned=fee_structure.class_level
                )

            # Filter by student category
            if fee_structure.applicable_to != 'ALL':
                enrollments = enrollments.filter(
                    student__category=fee_structure.applicable_to
                )

            for enrollment in enrollments:
                # Check if due already exists
                existing = StudentFeeDue.objects.filter(
                    student=enrollment.student,
                    academic_year=fee_structure.academic_year,
                    fee_type=fee_structure.fee_type,
                    creation_source='MANUAL'
                ).exists()

                if not existing:
                    StudentFeeDue.objects.create(
                        student=enrollment.student,
                        academic_year=fee_structure.academic_year,
                        fee_type=fee_structure.fee_type,
                        total_amount=fee_structure.amount,
                        paid_amount=0,
                        due_amount=fee_structure.amount,
                        creation_source='MANUAL',
                        triggered_by_enrollment=enrollment,
                        due_date=timezone.now().date() + timedelta(
                            days=fee_structure.due_days_after_trigger
                        )
                    )
                    total_created += 1

        self.message_user(request, f"Created {total_created} fee due records.")

    create_dues_for_all_students.short_description = "Create dues for all applicable students"


@admin.register(StudentFeeConfiguration)
class StudentFeeConfigurationAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'academic_year', 'fee_type', 'amount',
                    'override_reason', 'updated_by']
    list_filter = ['academic_year', 'fee_type']
    search_fields = ['student__admission_number', 'student__user__userprofile__full_name']
    autocomplete_fields = ['student', 'academic_year', 'fee_type', 'updated_by']

    def get_student(self, obj):
        return f"{obj.student.admission_number} - {obj.student.user.userprofile.full_name}"

    get_student.short_description = 'Student'


class FeeCollectionItemInline(admin.TabularInline):
    model = FeeCollectionItem
    extra = 1
    autocomplete_fields = ['fee_type']


@admin.register(FeeCollection)
class FeeCollectionAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'get_student', 'collection_date', 'total_amount',
                    'payment_method', 'status', 'collected_by']
    list_filter = ['status', 'payment_method', 'collection_date', 'academic_year']
    search_fields = ['receipt_number', 'student__admission_number',
                     'student__user__userprofile__full_name']
    readonly_fields = ['receipt_number', 'created_at', 'updated_at']
    autocomplete_fields = ['organization', 'student', 'academic_year', 'enrollment',
                           'collected_by', 'approved_by']
    date_hierarchy = 'collection_date'

    fieldsets = (
        ('Receipt Information', {
            'fields': ('organization', 'receipt_number', 'status')
        }),
        ('Student & Period', {
            'fields': ('student', 'academic_year', 'enrollment')
        }),
        ('Payment Details', {
            'fields': ('collection_date', 'payment_method', 'total_amount',
                       'reference_number', 'collected_by')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )

    inlines = [FeeCollectionItemInline]

    def get_student(self, obj):
        return f"{obj.student.admission_number} - {obj.student.user.userprofile.full_name}"

    get_student.short_description = 'Student'

    actions = ['approve_collections', 'cancel_collections']

    def approve_collections(self, request, queryset):
        count = queryset.filter(status='PENDING').update(
            status='APPROVED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f"{count} fee collections approved.")

    approve_collections.short_description = "Approve selected collections"

    def cancel_collections(self, request, queryset):
        count = queryset.update(status='CANCELLED')
        self.message_user(request, f"{count} fee collections cancelled.")

    cancel_collections.short_description = "Cancel selected collections"


@admin.register(StudentFeeDue)
class StudentFeeDueAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'fee_type', 'month_display', 'total_amount',
                    'paid_amount', 'due_amount', 'due_date', 'creation_source']
    list_filter = ['creation_source', 'fee_type', 'academic_year', 'month', 'due_date']
    search_fields = ['student__admission_number', 'student__user__userprofile__full_name']
    readonly_fields = ['due_amount', 'created_at', 'updated_at']
    autocomplete_fields = ['student', 'academic_year', 'fee_type',
                           'triggered_by_enrollment']
    date_hierarchy = 'due_date'

    fieldsets = (
        ('Student & Fee Type', {
            'fields': ('student', 'academic_year', 'fee_type')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'paid_amount', 'due_amount')
        }),
        ('Due Information', {
            'fields': ('month', 'due_date', 'last_payment_date')
        }),
        ('Source', {
            'fields': ('creation_source', 'triggered_by_enrollment'),
            'classes': ('collapse',)
        }),
    )

    def get_student(self, obj):
        return f"{obj.student.admission_number} - {obj.student.user.userprofile.full_name}"

    get_student.short_description = 'Student'

    def month_display(self, obj):
        if obj.month:
            import calendar
            return calendar.month_name[obj.month]
        return '-'

    month_display.short_description = 'Month'


# ============================================================================
# ATTENDANCE ADMIN
# ============================================================================

@admin.register(AttendanceCalendar)
class AttendanceCalendarAdmin(admin.ModelAdmin):
    list_display = ['date', 'branch', 'academic_year', 'is_working_day',
                    'holiday_reason', 'created_by']
    list_filter = ['branch', 'academic_year', 'is_working_day', 'date']
    search_fields = ['holiday_reason']
    autocomplete_fields = ['organization', 'academic_year', 'branch', 'created_by']
    date_hierarchy = 'date'


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'date', 'status', 'get_class', 'marked_by']
    list_filter = ['status', 'date', 'enrollment__class_assigned',
                   'enrollment__division_assigned']
    search_fields = ['student__admission_number', 'student__user__userprofile__full_name']
    autocomplete_fields = ['organization', 'student', 'enrollment', 'marked_by']
    date_hierarchy = 'date'

    def get_student(self, obj):
        return f"{obj.student.admission_number} - {obj.student.user.userprofile.full_name}"

    get_student.short_description = 'Student'

    def get_class(self, obj):
        return f"{obj.enrollment.class_assigned.name} - {obj.enrollment.division_assigned.name}"

    get_class.short_description = 'Class'


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ['get_staff', 'date', 'status', 'marked_by']
    list_filter = ['status', 'date', 'staff__user_type']
    search_fields = ['staff__userprofile__full_name', 'staff__email']
    autocomplete_fields = ['organization', 'staff', 'marked_by']
    date_hierarchy = 'date'

    def get_staff(self, obj):
        return obj.staff.userprofile.full_name

    get_staff.short_description = 'Staff'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['get_staff', 'leave_type', 'from_date', 'to_date',
                    'total_days', 'status', 'reviewed_by']
    list_filter = ['status', 'leave_type', 'from_date']
    search_fields = ['requested_by__userprofile__full_name']
    readonly_fields = ['total_days']
    autocomplete_fields = ['organization', 'requested_by', 'reviewed_by']
    date_hierarchy = 'from_date'

    fieldsets = (
        ('Leave Information', {
            'fields': ('organization', 'requested_by', 'leave_type')
        }),
        ('Period', {
            'fields': ('from_date', 'to_date', 'total_days')
        }),
        ('Reason', {
            'fields': ('reason',)
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_staff(self, obj):
        return obj.requested_by.userprofile.full_name

    get_staff.short_description = 'Staff'

    actions = ['approve_leaves', 'reject_leaves']

    def approve_leaves(self, request, queryset):
        count = queryset.filter(status='PENDING').update(
            status='APPROVED',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} leave requests approved.")

    approve_leaves.short_description = "Approve selected leaves"

    def reject_leaves(self, request, queryset):
        count = queryset.filter(status='PENDING').update(
            status='REJECTED',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} leave requests rejected.")

    reject_leaves.short_description = "Reject selected leaves"


# ============================================================================
# SUPPORTING MODELS ADMIN
# ============================================================================

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'get_value_preview', 'category', 'organization']
    list_filter = ['category', 'organization']
    search_fields = ['key', 'description']
    autocomplete_fields = ['organization']

    def get_value_preview(self, obj):
        value_str = str(obj.value)
        return value_str[:50] + '...' if len(value_str) > 50 else value_str

    get_value_preview.short_description = 'Value'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'action', 'entity_type', 'timestamp', 'ip_address']
    list_filter = ['action', 'entity_type', 'timestamp']
    search_fields = ['entity_type', 'entity_id', 'user__userprofile__full_name']
    readonly_fields = ['organization', 'user', 'entity_type', 'entity_id', 'action',
                       'old_values', 'new_values', 'ip_address', 'user_agent', 'timestamp']
    date_hierarchy = 'timestamp'

    def get_user(self, obj):
        if obj.user:
            return obj.user.userprofile.full_name if hasattr(obj.user, 'userprofile') else obj.user.email
        return 'System'

    get_user.short_description = 'User'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'subject', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'created_at', 'sent_at']
    search_fields = ['recipient_email', 'subject']
    readonly_fields = ['sent_at', 'created_at', 'updated_at']
    autocomplete_fields = ['organization']

    fieldsets = (
        ('Email Details', {
            'fields': ('organization', 'recipient_email', 'subject', 'body')
        }),
        ('Template', {
            'fields': ('template_name', 'context_data'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'error_message')
        }),
    )

    actions = ['resend_emails']

    def resend_emails(self, request, queryset):
        count = queryset.filter(status='FAILED').update(status='PENDING')
        self.message_user(request, f"{count} emails queued for resending.")

    resend_emails.short_description = "Resend failed emails"


@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'entity_type', 'file_type', 'get_file_size',
                    'uploaded_by', 'created_at']
    list_filter = ['entity_type', 'file_type', 'created_at']
    search_fields = ['file_name', 'description', 'entity_type']
    readonly_fields = ['file_size', 'created_at', 'updated_at']
    autocomplete_fields = ['organization', 'uploaded_by']

    def get_file_size(self, obj):
        """Convert bytes to human readable format"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    get_file_size.short_description = 'File Size'


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

admin.site.site_header = "Skool Management"
admin.site.site_title = "Skool Admin"
admin.site.index_title = "Welcome to Skool"