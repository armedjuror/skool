"""
API Views for Kerala Islamic Centre Madrassa Management System - REFACTORED

This module implements all API endpoints using DRF ViewSets for cleaner code:
- Authentication (Login, Logout, Password management)
- Dashboard (Stats, Activities, Notifications)
- Student Management (CRUD, Registration, Pending approvals)

All endpoints follow RESTful design with proper error handling and validation.
"""
from django.urls import reverse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import login, logout, get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
import secrets
import hashlib
from datetime import timedelta, date
from decimal import Decimal

from main.models import (
    Organization,
    Branch,
    Class,
    Division,
    AcademicYear,
    StudentProfile,
    StudentRegistration,
    StudentEnrollment,
    StaffProfile,
    FeeCollection,
    StudentFeeDue,
    StudentAttendance,
    StaffAttendance,
    AuditLog,
)

from main.serializers.auth_serializers import (
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    LogoutSerializer, UserAPISerializer
)

from main.serializers.student_serializers import (
    StudentListSerializer,
    StudentDetailSerializer,
    StudentCreateSerializer,
    StudentUpdateSerializer,
    StudentRegistrationSerializer,
    StudentRegistrationVerifySerializer,
    PendingStudentListSerializer,
    PendingStudentDetailSerializer,
    PendingStudentApproveSerializer,
    PendingStudentRejectSerializer,
    PendingStudentRequestInfoSerializer,
    BranchMinimalSerializer,
    ClassMinimalSerializer,
    DivisionMinimalSerializer,
)

from main.serializers.settings_serializers import (
    AcademicYearListSerializer,
    AcademicYearDetailSerializer,
    AcademicYearCreateSerializer,
    AcademicYearUpdateSerializer,
    BranchListSerializer,
    BranchDetailSerializer,
    BranchCreateSerializer,
    BranchUpdateSerializer,
    ClassListSerializer,
    ClassDetailSerializer,
    ClassCreateSerializer,
    ClassUpdateSerializer,
    DivisionListSerializer,
    DivisionDetailSerializer,
    DivisionCreateSerializer,
    DivisionUpdateSerializer,
    StaffListSerializer,
    StaffDetailSerializer,
    StaffCreateSerializer,
    StaffUpdateSerializer,
    SystemSettingListSerializer,
    SystemSettingDetailSerializer,
    SystemSettingCreateSerializer,
    SystemSettingUpdateSerializer,
)

from main.permissions import (
    IsOrganizationMember,
    IsAdmin,
    IsHeadTeacher,
    IsTeacher,
    CanManageStudents,
    CanApproveRegistrations,
)

User = get_user_model()


# =============================================================================
# AUTHENTICATION VIEWSET
# =============================================================================

class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for authentication operations.

    Endpoints:
    - POST /api/auth/login/ - Login user
    - POST /api/auth/logout/ - Logout user
    - GET /api/auth/user/ - Get current user
    - POST /api/auth/change-password/ - Change password
    - POST /api/auth/forgot-password/ - Request password reset
    - POST /api/auth/reset-password/ - Reset password with token
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        POST /api/auth/login/

        Authenticate user and return authentication token.
        """
        serializer = LoginSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = serializer.validated_data['user']
            remember_me = serializer.validated_data.get('remember_me', False)

            # Create or get authentication token
            token, created = Token.objects.get_or_create(user=user)

            # If token is old and user doesn't want to be remembered, regenerate
            if not remember_me and not created:
                token_age = timezone.now() - token.created
                if token_age > timedelta(hours=24):
                    token.delete()
                    token = Token.objects.create(user=user)

            # Log the user in
            login(request, user)

            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            # Serialize user data
            user_serializer = UserSerializer(user)

            return Response({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'token': token.key,
                    'user': user_serializer.data,
                    'next': reverse('dashboard', args=[user.organization.code],),
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Login failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        POST /api/auth/logout/

        Logout user and delete authentication token.
        """
        try:
            request.user.auth_token.delete()
        except Exception:
            pass

        logout(request)

        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def user(self, request):
        """
        GET /api/auth/user/

        Get current authenticated user's information.
        """
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        """
        POST /api/auth/change-password/

        Change user's password (requires current password).
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # Set new password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()

            # Delete old token and create new one
            try:
                request.user.auth_token.delete()
            except Exception:
                pass

            Token.objects.create(user=request.user)

            return Response({
                'success': True,
                'message': 'Password changed successfully. Please login again with your new password.'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Password change failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        """
        POST /api/auth/forgot-password/

        Request password reset (sends email with reset token).
        """
        serializer = ForgotPasswordSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email, is_active=True)

                # Generate password reset token
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode()).hexdigest()

                # Store token hash and expiry
                user.password_reset_token = token_hash
                user.password_reset_expires = timezone.now() + timedelta(hours=24)
                user.save(update_fields=['password_reset_token', 'password_reset_expires'])

                # Send password reset email
                reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

                send_mail(
                    subject='Password Reset Request - KIC Madrassa',
                    message=f'''
Hello {user.first_name},

You have requested to reset your password for KIC Madrassa Management System.

Please click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
KIC Madrassa Team
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except User.DoesNotExist:
                pass

            return Response({
                'success': True,
                'message': 'If your email is registered, you will receive password reset instructions shortly.'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Invalid request',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        """
        POST /api/auth/reset-password/

        Reset password using token from email.
        """
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']

            # Hash the token to compare with database
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            try:
                # Find user with this token
                user = User.objects.get(
                    password_reset_token=token_hash,
                    password_reset_expires__gt=timezone.now(),
                    is_active=True
                )

                # Set new password
                user.set_password(new_password)
                user.password_reset_token = None
                user.password_reset_expires = None
                user.save(update_fields=['password', 'password_reset_token', 'password_reset_expires'])

                # Delete all existing tokens
                Token.objects.filter(user=user).delete()

                # Send confirmation email
                send_mail(
                    subject='Password Reset Successful - KIC Madrassa',
                    message=f'''
Hello {user.first_name},

Your password has been successfully reset.

If you did not perform this action, please contact the administrator immediately.

Best regards,
KIC Madrassa Team
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )

                return Response({
                    'success': True,
                    'message': 'Password reset successful. Please login with your new password.'
                }, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Invalid or expired reset token'
                }, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'success': False,
            'message': 'Password reset failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# DASHBOARD VIEWSET
# =============================================================================

class DashboardViewSet(viewsets.GenericViewSet):
    """
    ViewSet for dashboard operations.

    Endpoints:
    - GET /api/dashboard/stats/ - Get dashboard statistics
    - GET /api/dashboard/recent-activity/ - Get recent activities
    - GET /api/dashboard/notifications/ - Get notifications
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        GET /api/dashboard/stats/

        Get dashboard statistics based on user role.
        """
        organization = request.user.organization
        user_role = request.user.role
        today = timezone.now().date()

        # Get active academic year
        academic_year = AcademicYear.objects.filter(
            organization=organization,
            is_active=True
        ).first()

        # Base querysets
        students_qs = StudentProfile.objects.filter(user__organization=organization)
        staff_qs = StaffProfile.objects.filter(user__organization=organization)

        # Branch filtering for non-admin users
        user_branch = None
        if hasattr(request.user, 'staffprofile'):
            user_branch = request.user.staffprofile.branch

        if user_role not in ['admin', 'chief_head_teacher'] and user_branch:
            students_qs = students_qs.filter(branch=user_branch)
            staff_qs = staff_qs.filter(branch=user_branch)

        # Student statistics
        students_data = {
            'total': students_qs.count(),
            'active': students_qs.filter(status='ACTIVE').count(),
            'inactive': students_qs.exclude(status='ACTIVE').count(),
            'by_branch': list(
                students_qs.filter(status='ACTIVE')
                .values('branch__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
        }

        # Staff statistics
        teachers_count = staff_qs.filter(user__user_type='TEACHER', status='ACTIVE').count()
        head_teachers_count = staff_qs.filter(
            user__user_type__in=['HEAD_TEACHER', 'CHIEF_HEAD_TEACHER'],
            status='ACTIVE'
        ).count()

        staff_data = {
            'total': staff_qs.count(),
            'active': staff_qs.filter(status='ACTIVE').count(),
            'by_role': {
                'teachers': teachers_count,
                'head_teachers': head_teachers_count,
                'others': staff_qs.filter(status='ACTIVE').count() - teachers_count - head_teachers_count
            }
        }

        # Pending registrations
        pending_students_qs = StudentRegistration.objects.filter(
            organization=organization,
            status='PENDING'
        )
        if user_branch:
            pending_students_qs = pending_students_qs.filter(interested_branch=user_branch)

        registrations_data = {
            'pending_students': pending_students_qs.count(),
            'pending_staff': 0,
            'total_pending': pending_students_qs.count()
        }

        # Fee statistics
        current_month = today.month
        current_year = today.year

        fees_collected_qs = FeeCollection.objects.filter(
            organization=organization,
            collection_date__month=current_month,
            collection_date__year=current_year,
            status='APPROVED'
        )

        fees_due_qs = StudentFeeDue.objects.filter(
            student__user__organization=organization,
            due_amount__gt=0
        )

        if user_branch:
            fees_collected_qs = fees_collected_qs.filter(student__branch=user_branch)
            fees_due_qs = fees_due_qs.filter(student__branch=user_branch)

        this_month_collection = fees_collected_qs.aggregate(
            total=Coalesce(Sum('total_amount'), Decimal('0'))
        )['total']

        pending_dues = fees_due_qs.aggregate(
            total=Coalesce(Sum('due_amount'), Decimal('0'))
        )['total']

        fees_data = {
            'this_month_collection': float(this_month_collection),
            'pending_dues': float(pending_dues),
            'total_students_with_dues': fees_due_qs.values('student').distinct().count()
        }

        # Attendance statistics
        student_attendance_today = StudentAttendance.objects.filter(
            organization=organization,
            date=today
        )
        if user_branch:
            student_attendance_today = student_attendance_today.filter(student__branch=user_branch)

        present_students = student_attendance_today.filter(status='PRESENT').count()
        total_marked = student_attendance_today.count()
        student_percentage = round((present_students / total_marked) * 100, 1) if total_marked > 0 else 0

        staff_attendance_today = StaffAttendance.objects.filter(
            organization=organization,
            date=today
        )

        present_staff = staff_attendance_today.filter(status='PRESENT').count()
        total_staff_marked = staff_attendance_today.count()
        staff_percentage = round((present_staff / total_staff_marked) * 100, 1) if total_staff_marked > 0 else 0

        attendance_data = {
            'today': {
                'student_percentage': student_percentage,
                'staff_percentage': staff_percentage,
                'students_present': present_students,
                'students_total': total_marked,
                'staff_present': present_staff,
                'staff_total': total_staff_marked
            },
            'this_month': {
                'student_average': student_percentage,
                'staff_average': staff_percentage
            }
        }

        return Response({
            'success': True,
            'data': {
                'students': students_data,
                'staff': staff_data,
                'registrations': registrations_data,
                'fees': fees_data,
                'attendance': attendance_data
            }
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='recent-activity')
    def recent_activity(self, request):
        """
        GET /api/dashboard/recent-activity/

        Get recent system activities.
        """
        organization = request.user.organization
        limit = int(request.query_params.get('limit', 10))

        activities = AuditLog.objects.filter(
            organization=organization
        ).select_related('user').order_by('-timestamp')[:limit]

        type_mapping = {
            'StudentRegistration': {'type': 'student_registered', 'icon': 'fa-user-plus', 'color': 'primary'},
            'StudentProfile': {'type': 'student_approved', 'icon': 'fa-user-check', 'color': 'success'},
            'FeeCollection': {'type': 'fee_collected', 'icon': 'fa-money-bill', 'color': 'success'},
            'StudentAttendance': {'type': 'attendance_marked', 'icon': 'fa-calendar-check', 'color': 'info'},
            'StaffProfile': {'type': 'staff_added', 'icon': 'fa-user-tie', 'color': 'primary'},
            'LeaveRequest': {'type': 'leave_requested', 'icon': 'fa-calendar-times', 'color': 'warning'}
        }

        result = []
        for activity in activities:
            mapping = type_mapping.get(activity.entity_type, {
                'type': 'system_activity',
                'icon': 'fa-cog',
                'color': 'secondary'
            })

            user_name = 'System'
            if activity.user:
                try:
                    user_name = activity.user.userprofile.full_name
                except:
                    user_name = activity.user.email

            result.append({
                'id': str(activity.id),
                'type': mapping['type'],
                'title': f"{activity.get_action_display()} {activity.entity_type}",
                'description': f"{user_name} {activity.get_action_display().lower()} a {activity.entity_type}",
                'timestamp': activity.timestamp,
                'user': user_name,
                'icon': mapping['icon'],
                'color': mapping['color']
            })

        return Response({
            'success': True,
            'activities': result
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def notifications(self, request):
        """
        GET /api/dashboard/notifications/

        Get user notifications.
        """
        organization = request.user.organization
        user_role = request.user.role
        notifications = []

        # Pending registrations
        if user_role in ['admin', 'chief_head_teacher', 'head_teacher']:
            pending_count = StudentRegistration.objects.filter(
                organization=organization,
                status='PENDING'
            ).count()

            if pending_count > 0:
                notifications.append({
                    'id': 'pending-registrations',
                    'type': 'pending_registration',
                    'title': 'New Registrations Pending',
                    'message': f'{pending_count} new student registration(s) waiting for approval',
                    'created_at': timezone.now(),
                    'is_read': False,
                    'action_url': '/registrations/'
                })

        # Fee dues
        if user_role in ['admin', 'chief_head_teacher', 'head_teacher', 'accountant']:
            overdue_count = StudentFeeDue.objects.filter(
                student__user__organization=organization,
                due_amount__gt=0,
                due_date__lt=timezone.now().date()
            ).values('student').distinct().count()

            if overdue_count > 0:
                notifications.append({
                    'id': 'overdue-fees',
                    'type': 'fee_reminder',
                    'title': 'Overdue Fee Payments',
                    'message': f'{overdue_count} student(s) have overdue fee payments',
                    'created_at': timezone.now(),
                    'is_read': False,
                    'action_url': '/fees/'
                })

        return Response({
            'success': True,
            'unread_count': len([n for n in notifications if not n['is_read']]),
            'notifications': notifications
        }, status=status.HTTP_200_OK)


# =============================================================================
# STUDENT VIEWSET
# =============================================================================

class StudentPagination(PageNumberPagination):
    """Custom pagination for student list"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for student management.

    Endpoints:
    - GET /api/students/ - List students (with pagination and filters)
    - POST /api/students/ - Create student (direct admission)
    - GET /api/students/{id}/ - Get student details
    - PUT/PATCH /api/students/{id}/ - Update student
    - DELETE /api/students/{id}/ - Delete student (soft delete)
    - GET /api/students/search/ - Advanced search
    """
    permission_classes = [IsAuthenticated, CanManageStudents]
    pagination_class = StudentPagination
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'search':
            return StudentListSerializer
        elif self.action == 'retrieve':
            return StudentDetailSerializer
        elif self.action == 'create':
            return StudentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StudentUpdateSerializer
        return StudentListSerializer

    def get_queryset(self):
        organization = self.request.user.organization
        queryset = StudentProfile.objects.filter(
            user__organization=organization
        ).select_related(
            'user__userprofile',
            'branch'
        ).prefetch_related(
            'enrollments__class_assigned',
            'enrollments__division_assigned',
            'enrollments__academic_year',
            'family'
        )

        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category=category_filter.upper())

        branch_filter = self.request.query_params.get('branch')
        if branch_filter:
            queryset = queryset.filter(branch_id=branch_filter)

        class_filter = self.request.query_params.get('class')
        if class_filter:
            queryset = queryset.filter(
                enrollments__class_assigned_id=class_filter,
                enrollments__academic_year__is_active=True,
                enrollments__enrollment_status='ENROLLED'
            )

        division_filter = self.request.query_params.get('division')
        if division_filter:
            queryset = queryset.filter(
                enrollments__division_assigned_id=division_filter,
                enrollments__academic_year__is_active=True,
                enrollments__enrollment_status='ENROLLED'
            )

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__userprofile__full_name__icontains=search) |
                Q(admission_number__icontains=search) |
                Q(family__parent_mobile__icontains=search)
            )

        # Role-based filtering
        user_role = self.request.user.role
        if user_role not in ['admin', 'chief_head_teacher']:
            if hasattr(self.request.user, 'staffprofile') and self.request.user.staffprofile.branch:
                queryset = queryset.filter(branch=self.request.user.staffprofile.branch)

        return queryset.distinct().order_by('-created_at')

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsHeadTeacher()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'count': response.data.get('count', 0),
            'next': response.data.get('next'),
            'previous': response.data.get('previous'),
            'results': response.data.get('results', [])
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            student = serializer.save()
            return Response({
                'success': True,
                'message': 'Student created successfully',
                'data': {
                    'id': str(student.id),
                    'admission_number': student.admission_number,
                    'name': student.user.userprofile.full_name
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'message': 'Student creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            student = serializer.save()
            return Response({
                'success': True,
                'message': 'Student updated successfully',
                'data': {
                    'id': str(student.id),
                    'admission_number': student.admission_number,
                    'name': student.user.userprofile.full_name
                }
            })

        return Response({
            'success': False,
            'message': 'Student update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        student = self.get_object()

        # Soft delete
        student.status = 'INACTIVE'
        student.save()

        student.user.is_active = False
        student.user.save()

        return Response({
            'success': True,
            'message': 'Student deleted successfully'
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        GET /api/students/search/

        Advanced student search with multiple filters.
        """
        return self.list(request)


# =============================================================================
# STUDENT REGISTRATION VIEWSET (PUBLIC)
# =============================================================================

class StudentRegistrationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for public student registration.

    Endpoints:
    - POST /api/registration/student/ - Submit registration
    - GET /api/registration/student/verify/ - Verify registration status
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def submit(self, request):
        """
        POST /api/registration/student/

        Submit student registration form (Public).
        """
        org_code = request.data.get('org_code') or request.query_params.get('org_code')

        if not org_code:
            return Response({
                'success': False,
                'message': 'Organization code is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            organization = Organization.objects.get(code=org_code, is_active=True)
        except Organization.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid organization code'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = StudentRegistrationSerializer(
            data=request.data,
            context={'organization': organization}
        )

        if serializer.is_valid():
            registration = serializer.save()
            return Response({
                'success': True,
                'message': 'Registration submitted successfully',
                'data': {
                    'registration_id': str(registration.id),
                    'student_name': registration.student_name,
                    'submission_date': registration.submission_date,
                    'status': registration.status
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def verify(self, request):
        """
        GET /api/registration/student/verify/

        Verify registration status (Public).
        """
        registration_id = request.query_params.get('registration_id')
        email = request.query_params.get('email')

        if not registration_id and not email:
            return Response({
                'success': False,
                'message': 'Either registration_id or email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if registration_id:
                registration = StudentRegistration.objects.get(id=registration_id)
            else:
                registration = StudentRegistration.objects.filter(
                    email=email
                ).order_by('-submission_date').first()

                if not registration:
                    raise StudentRegistration.DoesNotExist()

            return Response({
                'success': True,
                'data': {
                    'registration_id': str(registration.id),
                    'student_name': registration.student_name,
                    'submission_date': registration.submission_date,
                    'status': registration.status,
                    'status_display': registration.get_status_display(),
                    'info_request_message': registration.info_request_message,
                    'rejection_reason': registration.rejection_reason
                }
            })

        except StudentRegistration.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Registration not found'
            }, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# PENDING STUDENT REGISTRATION VIEWSET
# =============================================================================

class PendingStudentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for pending student registrations.

    Endpoints:
    - GET /api/pending/students/ - List pending registrations
    - GET /api/pending/students/{id}/ - Get registration details
    - POST /api/pending/students/{id}/approve/ - Approve registration
    - POST /api/pending/students/{id}/reject/ - Reject registration
    - POST /api/pending/students/{id}/request-info/ - Request more info
    """
    permission_classes = [IsAuthenticated, CanApproveRegistrations]
    pagination_class = StudentPagination
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'list':
            return PendingStudentListSerializer
        elif self.action == 'retrieve':
            return PendingStudentDetailSerializer
        elif self.action == 'approve':
            return PendingStudentApproveSerializer
        elif self.action == 'reject':
            return PendingStudentRejectSerializer
        elif self.action == 'request_info':
            return PendingStudentRequestInfoSerializer
        return PendingStudentListSerializer

    def get_queryset(self):
        organization = self.request.user.organization
        queryset = StudentRegistration.objects.filter(
            organization=organization
        ).select_related(
            'interested_branch',
            'class_to_admit'
        ).order_by('-submission_date')

        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        else:
            queryset = queryset.filter(status='PENDING')

        branch_filter = self.request.query_params.get('branch')
        if branch_filter:
            queryset = queryset.filter(interested_branch_id=branch_filter)

        date_from = self.request.query_params.get('submission_date_from')
        if date_from:
            queryset = queryset.filter(submission_date__date__gte=date_from)

        date_to = self.request.query_params.get('submission_date_to')
        if date_to:
            queryset = queryset.filter(submission_date__date__lte=date_to)

        # Role-based filtering
        user_role = self.request.user.role
        if user_role == 'head_teacher':
            if hasattr(self.request.user, 'staffprofile') and self.request.user.staffprofile.branch:
                queryset = queryset.filter(
                    interested_branch=self.request.user.staffprofile.branch
                )

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'count': response.data.get('count', 0),
            'results': response.data.get('results', [])
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, id=None):
        """
        POST /api/pending/students/{id}/approve/

        Approve registration and create student record.
        """
        registration = self.get_object()

        if registration.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Registration already processed'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PendingStudentApproveSerializer(
            data=request.data,
            context={'request': request, 'registration': registration}
        )

        if serializer.is_valid():
            student = serializer.save()
            return Response({
                'success': True,
                'message': 'Student registration approved',
                'data': {
                    'student_id': str(student.id),
                    'admission_number': student.admission_number,
                    'status': student.status
                }
            })

        return Response({
            'success': False,
            'message': 'Approval failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reject(self, request, id=None):
        """
        POST /api/pending/students/{id}/reject/

        Reject registration.
        """
        registration = self.get_object()

        if registration.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Registration already processed'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PendingStudentRejectSerializer(
            registration,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            registration = serializer.save()
            return Response({
                'success': True,
                'message': 'Registration rejected',
                'data': {
                    'registration_id': str(registration.id),
                    'status': registration.status
                }
            })

        return Response({
            'success': False,
            'message': 'Rejection failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='request-info')
    def request_info(self, request, id=None):
        """
        POST /api/pending/students/{id}/request-info/

        Request additional information from parent.
        """
        registration = self.get_object()

        if registration.status not in ['PENDING', 'INFO_REQUESTED']:
            return Response({
                'success': False,
                'message': 'Registration already processed'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PendingStudentRequestInfoSerializer(
            registration,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            registration = serializer.save()

            return Response({
                'success': True,
                'message': 'Information request sent',
                'data': {
                    'registration_id': str(registration.id),
                    'status': registration.status
                }
            })

        return Response({
            'success': False,
            'message': 'Request failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# UTILITY VIEWSETS
# =============================================================================

class SettingsViewSet(viewsets.GenericViewSet):
    """
    ViewSet for utility operations.

    Endpoints:
    - GET /api/utilities/branches/ - List branches
    - GET /api/utilities/classes/ - List classes
    - GET /api/utilities/divisions/ - List divisions
    """
    permission_classes = []

    @action(detail=False, methods=['get'])
    def branches(self, request):
        """GET /api/utilities/branches/"""
        if request.user.is_authenticated:
            organization = request.user.organization
            branches = Branch.objects.filter(
                organization=organization,
                is_active=True
            ).order_by('name')
        else:
            org_code = request.GET.get('org_code')
            branches = Branch.objects.filter(
                organization__code=org_code,
                is_active=True
            ).order_by('name')


        serializer = BranchMinimalSerializer(branches, many=True)
        return Response({
            'success': True,
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def classes(self, request):
        """GET /api/utilities/classes/"""
        if request.user.is_authenticated:
            organization = request.user.organization
            classes = Class.objects.filter(
                organization=organization,
                is_active=True
            ).order_by('level', 'name')
        else:
            org_code = request.GET.get('org_code')
            classes = Class.objects.filter(
                organization__code=org_code,
                is_active=True
            ).order_by('level', 'name')

        serializer = ClassMinimalSerializer(classes, many=True)
        return Response({
            'success': True,
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def divisions(self, request):
        """GET /api/utilities/divisions/"""
        organization = request.user.organization
        divisions = Division.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('name')

        serializer = DivisionMinimalSerializer(divisions, many=True)
        return Response({
            'success': True,
            'results': serializer.data
        })


# =============================================================================
# ACADEMIC YEAR VIEWSET
# =============================================================================

class AcademicYearViewSet(viewsets.ModelViewSet):
    """
    ViewSet for academic year management.

    Endpoints:
    - GET /api/academic-years/ - List academic years
    - POST /api/academic-years/ - Create academic year
    - GET /api/academic-years/{id}/ - Get academic year details
    - PUT/PATCH /api/academic-years/{id}/ - Update academic year
    - DELETE /api/academic-years/{id}/ - Delete academic year
    - POST /api/academic-years/{id}/activate/ - Activate academic year
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StudentPagination
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'list':
            return AcademicYearListSerializer
        elif self.action == 'retrieve':
            return AcademicYearDetailSerializer
        elif self.action == 'create':
            return AcademicYearCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AcademicYearUpdateSerializer
        return AcademicYearListSerializer

    def get_queryset(self):
        organization = self.request.user.organization
        return AcademicYear.objects.filter(
            organization=organization
        ).order_by('-start_date')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'count': response.data.get('count', 0),
            'results': response.data.get('results', [])
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            academic_year = serializer.save()
            return Response({
                'success': True,
                'message': 'Academic year created successfully',
                'data': AcademicYearDetailSerializer(academic_year).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Academic year creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            academic_year = serializer.save()
            return Response({
                'success': True,
                'message': 'Academic year updated successfully',
                'data': AcademicYearDetailSerializer(academic_year).data
            })
        return Response({
            'success': False,
            'message': 'Academic year update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if there are enrollments in this academic year
        if instance.student_enrollments.exists():
            return Response({
                'success': False,
                'message': 'Cannot delete academic year with student enrollments'
            }, status=status.HTTP_400_BAD_REQUEST)
        instance.delete()
        return Response({
            'success': True,
            'message': 'Academic year deleted successfully'
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, id=None):
        """POST /api/academic-years/{id}/activate/ - Activate academic year"""
        instance = self.get_object()
        instance.is_active = True
        instance.save()  # The model's save method handles deactivating others
        return Response({
            'success': True,
            'message': 'Academic year activated successfully',
            'data': AcademicYearDetailSerializer(instance).data
        })


# =============================================================================
# BRANCH VIEWSET
# =============================================================================

class BranchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for branch management.

    Endpoints:
    - GET /api/branches/ - List branches
    - POST /api/branches/ - Create branch
    - GET /api/branches/{id}/ - Get branch details
    - PUT/PATCH /api/branches/{id}/ - Update branch
    - DELETE /api/branches/{id}/ - Delete branch (soft delete)
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StudentPagination
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'list':
            return BranchListSerializer
        elif self.action == 'retrieve':
            return BranchDetailSerializer
        elif self.action == 'create':
            return BranchCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BranchUpdateSerializer
        return BranchListSerializer

    def get_queryset(self):
        organization = self.request.user.organization
        queryset = Branch.objects.filter(
            organization=organization
        ).select_related('head_teacher__userprofile').order_by('name')

        # Apply filters
        is_active = self.request.query_params.get('is_active', True)
        print(is_active)
        if is_active:
            queryset = queryset.filter(is_active=True)
        else:
            queryset = queryset.filter(is_active=False)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'count': response.data.get('count', 0),
            'results': response.data.get('results', [])
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            branch = serializer.save()
            return Response({
                'success': True,
                'message': 'Branch created successfully',
                'data': BranchDetailSerializer(branch).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Branch creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            branch = serializer.save()
            return Response({
                'success': True,
                'message': 'Branch updated successfully',
                'data': BranchDetailSerializer(branch).data
            })
        return Response({
            'success': False,
            'message': 'Branch update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Soft delete - set is_active to False
        instance.is_active = False
        instance.save()
        return Response({
            'success': True,
            'message': 'Branch deleted successfully'
        })


# =============================================================================
# CLASS VIEWSET
# =============================================================================

class ClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet for class management.

    Endpoints:
    - GET /api/classes/ - List classes
    - POST /api/classes/ - Create class
    - GET /api/classes/{id}/ - Get class details
    - PUT/PATCH /api/classes/{id}/ - Update class
    - DELETE /api/classes/{id}/ - Delete class (soft delete)
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StudentPagination
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'list':
            return ClassListSerializer
        elif self.action == 'retrieve':
            return ClassDetailSerializer
        elif self.action == 'create':
            return ClassCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ClassUpdateSerializer
        return ClassListSerializer

    def get_queryset(self):
        organization = self.request.user.organization
        queryset = Class.objects.filter(
            organization=organization
        ).order_by( 'level')

        # Apply filters
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'count': response.data.get('count', 0),
            'results': response.data.get('results', [])
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            class_obj = serializer.save()
            return Response({
                'success': True,
                'message': 'Class created successfully',
                'data': ClassDetailSerializer(class_obj).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Class creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            class_obj = serializer.save()
            return Response({
                'success': True,
                'message': 'Class updated successfully',
                'data': ClassDetailSerializer(class_obj).data
            })
        return Response({
            'success': False,
            'message': 'Class update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if there are enrollments in this class
        if instance.enrolled_students.exists():
            return Response({
                'success': False,
                'message': 'Cannot delete class with enrolled students'
            }, status=status.HTTP_400_BAD_REQUEST)
        # Soft delete
        instance.is_active = False
        instance.save()
        return Response({
            'success': True,
            'message': 'Class deleted successfully'
        })


# =============================================================================
# DIVISION VIEWSET
# =============================================================================

class DivisionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for division management.

    Endpoints:
    - GET /api/divisions/ - List divisions
    - POST /api/divisions/ - Create division
    - GET /api/divisions/{id}/ - Get division details
    - PUT/PATCH /api/divisions/{id}/ - Update division
    - DELETE /api/divisions/{id}/ - Delete division (soft delete)
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StudentPagination
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'list':
            return DivisionListSerializer
        elif self.action == 'retrieve':
            return DivisionDetailSerializer
        elif self.action == 'create':
            return DivisionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DivisionUpdateSerializer
        return DivisionListSerializer

    def get_queryset(self):
        organization = self.request.user.organization
        queryset = Division.objects.filter(
            organization=organization
        ).order_by('name')

        # Apply filters
        is_active = self.request.query_params.get('is_active', True)
        if is_active:
            queryset = queryset.filter(is_active=True)
        else:
            queryset = queryset.filter(is_active=False)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'count': response.data.get('count', 0),
            'results': response.data.get('results', [])
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            division = serializer.save()
            return Response({
                'success': True,
                'message': 'Division created successfully',
                'data': DivisionDetailSerializer(division).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Division creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            division = serializer.save()
            return Response({
                'success': True,
                'message': 'Division updated successfully',
                'data': DivisionDetailSerializer(division).data
            })
        return Response({
            'success': False,
            'message': 'Division update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if there are enrollments in this division
        if instance.enrolled_students.exists():
            return Response({
                'success': False,
                'message': 'Cannot delete division with enrolled students'
            }, status=status.HTTP_400_BAD_REQUEST)
        # Soft delete
        instance.is_active = False
        instance.save()
        return Response({
            'success': True,
            'message': 'Division deleted successfully'
        })


# =============================================================================
# STAFF VIEWSET
# =============================================================================

class StaffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for staff management.

    Endpoints:
    - GET /api/staff/ - List staff members
    - POST /api/staff/ - Create staff member
    - GET /api/staff/{id}/ - Get staff details
    - PUT/PATCH /api/staff/{id}/ - Update staff member
    - DELETE /api/staff/{id}/ - Delete staff member (soft delete)
    """
    permission_classes = [IsAuthenticated, IsHeadTeacher]
    pagination_class = StudentPagination
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'list':
            return StaffListSerializer
        elif self.action == 'retrieve':
            return StaffDetailSerializer
        elif self.action == 'create':
            return StaffCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StaffUpdateSerializer
        return StaffListSerializer

    def get_queryset(self):
        organization = self.request.user.organization
        queryset = StaffProfile.objects.filter(
            user__organization=organization
        ).select_related(
            'user__userprofile',
            'branch'
        ).order_by('staff_number')

        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category=category_filter.upper())

        branch_filter = self.request.query_params.get('branch')
        if branch_filter:
            queryset = queryset.filter(branch_id=branch_filter)

        user_type_filter = self.request.query_params.get('user_type')
        if user_type_filter:
            queryset = queryset.filter(user__user_type=user_type_filter.upper())

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__userprofile__full_name__icontains=search) |
                Q(staff_number__icontains=search) |
                Q(user__email__icontains=search)
            )

        # Role-based filtering
        user_role = self.request.user.role
        if user_role not in ['admin', 'chief_head_teacher']:
            if hasattr(self.request.user, 'staffprofile') and self.request.user.staffprofile.branch:
                queryset = queryset.filter(branch=self.request.user.staffprofile.branch)

        return queryset

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsAdmin()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'count': response.data.get('count', 0),
            'results': response.data.get('results', [])
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            staff = serializer.save()
            return Response({
                'success': True,
                'message': 'Staff member created successfully',
                'data': {
                    'id': str(staff.id),
                    'staff_number': staff.staff_number,
                    'name': staff.user.userprofile.full_name
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Staff creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            staff = serializer.save()
            return Response({
                'success': True,
                'message': 'Staff member updated successfully',
                'data': {
                    'id': str(staff.id),
                    'staff_number': staff.staff_number,
                    'name': staff.user.userprofile.full_name
                }
            })
        return Response({
            'success': False,
            'message': 'Staff update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Soft delete
        instance.status = 'INACTIVE'
        instance.save()
        instance.user.is_active = False
        instance.user.save()
        return Response({
            'success': True,
            'message': 'Staff member deleted successfully'
        })


# =============================================================================
# SYSTEM SETTINGS VIEWSET
# =============================================================================

from main.models import SystemSetting


class SystemSettingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for system settings management.

    Endpoints:
    - GET /api/system-settings/ - List system settings
    - POST /api/system-settings/ - Create system setting
    - GET /api/system-settings/{id}/ - Get system setting details
    - PUT/PATCH /api/system-settings/{id}/ - Update system setting
    - DELETE /api/system-settings/{id}/ - Delete system setting
    - GET /api/system-settings/by-key/{key}/ - Get setting by key
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StudentPagination
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'list':
            return SystemSettingListSerializer
        elif self.action == 'retrieve' or self.action == 'by_key':
            return SystemSettingDetailSerializer
        elif self.action == 'create':
            return SystemSettingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SystemSettingUpdateSerializer
        return SystemSettingListSerializer

    def get_queryset(self):
        organization = self.request.user.organization
        queryset = SystemSetting.objects.filter(
            organization=organization
        ).order_by('category', 'key')

        # Apply filters
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category=category_filter)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'count': response.data.get('count', 0),
            'results': response.data.get('results', [])
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            setting = serializer.save()
            return Response({
                'success': True,
                'message': 'System setting created successfully',
                'data': SystemSettingDetailSerializer(setting).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'System setting creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            setting = serializer.save()
            return Response({
                'success': True,
                'message': 'System setting updated successfully',
                'data': SystemSettingDetailSerializer(setting).data
            })
        return Response({
            'success': False,
            'message': 'System setting update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'System setting deleted successfully'
        })

    @action(detail=False, methods=['get'], url_path='by-key/(?P<key>[^/.]+)')
    def by_key(self, request, key=None):
        """GET /api/system-settings/by-key/{key}/ - Get setting by key"""
        organization = request.user.organization
        try:
            setting = SystemSetting.objects.get(organization=organization, key=key)
            serializer = self.get_serializer(setting)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except SystemSetting.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Setting with key "{key}" not found'
            }, status=status.HTTP_404_NOT_FOUND)


class UsersViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = UserAPISerializer
    lookup_field = 'id'

    def get_queryset(self):
        return User.objects.filter(organization=self.request.user.organization, is_active=True)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(organization=request.user.organization)
            return Response({
                'success': True,
                'message': 'User created successfully',
                'data': UserAPISerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'User creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response({
            'success': True,
            'message': 'User deleted successfully'
        })

    @action(detail=True, methods=['post'])
    def reset_password(self, request, *args, **kwargs):
        user = self.get_object()
        password = request.data.get('password')
        try:
            user.set_password(password)
            user.save()
            return Response({
                'success': True,
                'message': 'Password updated successfully'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': f'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
