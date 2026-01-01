"""
API Views for Kerala Islamic Centre Madrassa Management System

This module implements all API endpoints:
- Authentication (Login, Logout, Password management)
- Dashboard (Stats, Activities, Notifications)
- Student Management (CRUD, Registration, Pending approvals)

All endpoints follow RESTful design with proper error handling and validation.
"""

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework import status
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
    LogoutSerializer
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

from main.permissions import (
    IsOrganizationMember,
    IsAdmin,
    IsHeadTeacher,
    IsTeacher,
    CanManageStudents,
    CanApproveRegistrations,
)

User = get_user_model()


class LoginAPIView(APIView):
    """
    POST /api/auth/login/

    Authenticate user and return authentication token.

    Request Body:
    {
        "email": "user@example.com",
        "password": "password123",
        "remember_me": false  # optional
    }

    Response (200):
    {
        "success": true,
        "message": "Login successful",
        "data": {
            "token": "abc123...",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "head_teacher",
                "organization": {
                    "id": 1,
                    "name": "KIC Qatar",
                    "code": "KIC-QA"
                },
                "branch": {
                    "id": 1,
                    "name": "Doha Branch",
                    "code": "DOH"
                },
                "permissions": {...}
            }
        }
    }

    Error Responses:
    - 400: Validation failed
    - 401: Invalid credentials
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            user = serializer.validated_data['user']
            remember_me = serializer.validated_data.get('remember_me', False)

            # Create or get authentication token
            token, created = Token.objects.get_or_create(user=user)

            # If token is old and user doesn't want to be remembered, regenerate
            if not remember_me and not created:
                # Check if token is older than 24 hours
                token_age = timezone.now() - token.created
                if token_age > timedelta(hours=24):
                    token.delete()
                    token = Token.objects.create(user=user)

            # Log the user in (creates session)
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
                    'user': user_serializer.data
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Login failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    POST /api/auth/logout/

    Logout user and delete authentication token.

    Response (200):
    {
        "success": true,
        "message": "Logout successful"
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Delete the user's token
            request.user.auth_token.delete()
        except Exception:
            pass

        # Logout from session
        logout(request)

        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    """
    GET /api/auth/user/

    Get current authenticated user's information.

    Response (200):
    {
        "success": true,
        "data": {
            "id": 1,
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "head_teacher",
            "organization": {...},
            "branch": {...},
            "permissions": {...}
        }
    }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """
    POST /api/auth/change-password/

    Change user's password (requires current password).

    Request Body:
    {
        "current_password": "oldpass123",
        "new_password": "newpass123",
        "confirm_password": "newpass123"
    }

    Response (200):
    {
        "success": true,
        "message": "Password changed successfully"
    }

    Error Responses:
    - 400: Validation failed
    - 401: Current password incorrect
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # Set new password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()

            # Delete old token and create new one (force re-login on other devices)
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


class ForgotPasswordAPIView(APIView):
    """
    POST /api/auth/forgot-password/

    Request password reset (sends email with reset token).

    Request Body:
    {
        "email": "user@example.com"
    }

    Response (200):
    {
        "success": true,
        "message": "Password reset instructions sent to your email"
    }

    Note: For security, always returns success even if email doesn't exist
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email, is_active=True)

                # Generate password reset token
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode()).hexdigest()

                # Store token hash and expiry in user model
                # Note: You'll need to add these fields to your User model
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
                # Don't reveal if email exists or not (security measure)
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


class ResetPasswordAPIView(APIView):
    """
    POST /api/auth/reset-password/

    Reset password using token from email.

    Request Body:
    {
        "token": "abc123...",
        "new_password": "newpass123",
        "confirm_password": "newpass123"
    }

    Response (200):
    {
        "success": true,
        "message": "Password reset successful"
    }

    Error Responses:
    - 400: Validation failed
    - 401: Invalid or expired token
    """

    permission_classes = [AllowAny]

    def post(self, request):
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

                # Delete all existing tokens (force re-login on all devices)
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
# DASHBOARD API VIEWS
# =============================================================================

class DashboardStatsAPIView(APIView):
    """
    GET /api/dashboard/stats/

    Get dashboard statistics based on user role.

    Response (200):
    {
        "success": true,
        "data": {
            "students": {...},
            "staff": {...},
            "registrations": {...},
            "fees": {...},
            "attendance": {...}
        }
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization
        user_role = request.user.role
        today = timezone.now().date()

        # Get active academic year
        academic_year = AcademicYear.objects.filter(
            organization=organization,
            is_active=True
        ).first()

        # Base querysets filtered by organization
        students_qs = StudentProfile.objects.filter(
            user__organization=organization
        )
        staff_qs = StaffProfile.objects.filter(
            user__organization=organization
        )

        # For non-admin users, filter by branch if applicable
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
        teachers_count = staff_qs.filter(
            user__user_type='TEACHER',
            status='ACTIVE'
        ).count()
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
            'pending_staff': 0,  # Staff registration not yet implemented
            'total_pending': pending_students_qs.count()
        }

        # Fee statistics (this month)
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
        active_students = students_qs.filter(status='ACTIVE')

        # Today's student attendance
        student_attendance_today = StudentAttendance.objects.filter(
            organization=organization,
            date=today
        )
        if user_branch:
            student_attendance_today = student_attendance_today.filter(
                student__branch=user_branch
            )

        present_students = student_attendance_today.filter(status='PRESENT').count()
        total_marked = student_attendance_today.count()

        student_percentage = 0
        if total_marked > 0:
            student_percentage = round((present_students / total_marked) * 100, 1)

        # Today's staff attendance
        staff_attendance_today = StaffAttendance.objects.filter(
            organization=organization,
            date=today
        )

        present_staff = staff_attendance_today.filter(status='PRESENT').count()
        total_staff_marked = staff_attendance_today.count()

        staff_percentage = 0
        if total_staff_marked > 0:
            staff_percentage = round((present_staff / total_staff_marked) * 100, 1)

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
                'student_average': student_percentage,  # Simplified for now
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


class RecentActivityAPIView(APIView):
    """
    GET /api/dashboard/recent-activity/

    Get recent system activities.

    Query Parameters:
        - limit: Number of activities (default: 10)

    Response (200):
    {
        "success": true,
        "activities": [...]
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization
        limit = int(request.query_params.get('limit', 10))

        # Get recent audit logs
        activities = AuditLog.objects.filter(
            organization=organization
        ).select_related('user').order_by('-timestamp')[:limit]

        # Map entity types to icons and colors
        type_mapping = {
            'StudentRegistration': {
                'type': 'student_registered',
                'icon': 'fa-user-plus',
                'color': 'primary'
            },
            'StudentProfile': {
                'type': 'student_approved',
                'icon': 'fa-user-check',
                'color': 'success'
            },
            'FeeCollection': {
                'type': 'fee_collected',
                'icon': 'fa-money-bill',
                'color': 'success'
            },
            'StudentAttendance': {
                'type': 'attendance_marked',
                'icon': 'fa-calendar-check',
                'color': 'info'
            },
            'StaffProfile': {
                'type': 'staff_added',
                'icon': 'fa-user-tie',
                'color': 'primary'
            },
            'LeaveRequest': {
                'type': 'leave_requested',
                'icon': 'fa-calendar-times',
                'color': 'warning'
            }
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


class NotificationsAPIView(APIView):
    """
    GET /api/dashboard/notifications/

    Get user notifications.

    Response (200):
    {
        "success": true,
        "unread_count": 5,
        "notifications": [...]
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization
        user_role = request.user.role
        notifications = []

        # Check for pending registrations (for admins and head teachers)
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

        # Check for fee dues (for admins and accountants)
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
# STUDENT MANAGEMENT API VIEWS
# =============================================================================

class StudentPagination(PageNumberPagination):
    """Custom pagination for student list"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class StudentListAPIView(ListAPIView):
    """
    GET /api/students/

    List all students with pagination and filters.

    Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)
        - status: Filter by status (active/inactive)
        - category: Filter by category (permanent/temporary)
        - branch: Filter by branch ID
        - class: Filter by class ID
        - division: Filter by division ID
        - search: Search by name/admission number/mobile

    Response (200):
    {
        "success": true,
        "count": 100,
        "next": "url",
        "previous": "url",
        "results": [...]
    }
    """
    permission_classes = [IsAuthenticated, CanManageStudents]
    serializer_class = StudentListSerializer
    pagination_class = StudentPagination

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

        # Filter by class through enrollment
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

        # Search
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

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'count': response.data.get('count', 0),
            'next': response.data.get('next'),
            'previous': response.data.get('previous'),
            'results': response.data.get('results', [])
        })


class StudentDetailAPIView(RetrieveAPIView):
    """
    GET /api/students/{id}/

    Get detailed student information.

    Response (200):
    {
        "success": true,
        "data": {...}
    }
    """
    permission_classes = [IsAuthenticated, CanManageStudents]
    serializer_class = StudentDetailSerializer
    lookup_field = 'id'

    def get_queryset(self):
        organization = self.request.user.organization
        return StudentProfile.objects.filter(
            user__organization=organization
        ).select_related(
            'user__userprofile',
            'branch',
            'family'
        ).prefetch_related(
            'enrollments__class_assigned',
            'enrollments__division_assigned',
            'enrollments__academic_year',
            'user__addresses',
            'academic_history'
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })


class StudentCreateAPIView(CreateAPIView):
    """
    POST /api/students/create/

    Create new student (Direct admission by admin).

    Request: See StudentCreateSerializer for fields

    Response (201):
    {
        "success": true,
        "message": "Student created successfully",
        "data": {
            "id": "uuid",
            "admission_number": "WAKR0001",
            "name": "..."
        }
    }
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = StudentCreateSerializer

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


class StudentUpdateAPIView(UpdateAPIView):
    """
    PUT/PATCH /api/students/{id}/update/

    Update student information.

    Response (200):
    {
        "success": true,
        "message": "Student updated successfully",
        "data": {...}
    }
    """
    permission_classes = [IsAuthenticated, IsHeadTeacher]
    serializer_class = StudentUpdateSerializer
    lookup_field = 'id'

    def get_queryset(self):
        organization = self.request.user.organization
        return StudentProfile.objects.filter(
            user__organization=organization
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )

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


class StudentDeleteAPIView(APIView):
    """
    DELETE /api/students/{id}/delete/

    Soft delete student (set status to inactive).

    Response (200):
    {
        "success": true,
        "message": "Student deleted successfully"
    }
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, id):
        organization = request.user.organization

        try:
            student = StudentProfile.objects.get(
                id=id,
                user__organization=organization
            )
        except StudentProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Soft delete - set status to inactive
        student.status = 'INACTIVE'
        student.save()

        # Also deactivate user account
        student.user.is_active = False
        student.user.save()

        return Response({
            'success': True,
            'message': 'Student deleted successfully'
        })


class StudentSearchAPIView(ListAPIView):
    """
    GET /api/students/search/

    Advanced student search with multiple filters.
    Same as StudentListAPIView but with more specific search capabilities.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StudentListSerializer
    pagination_class = StudentPagination

    def get_queryset(self):
        return StudentListAPIView.get_queryset(self)

    def list(self, request, *args, **kwargs):
        return StudentListAPIView.list(self, request, *args, **kwargs)


# =============================================================================
# PUBLIC STUDENT REGISTRATION API VIEWS
# =============================================================================

class StudentRegistrationSubmitAPIView(CreateAPIView):
    """
    POST /api/registration/student/

    Submit student registration form (Public).

    Request: See StudentRegistrationSerializer for fields

    Response (201):
    {
        "success": true,
        "message": "Registration submitted successfully",
        "data": {
            "registration_id": "uuid",
            "student_name": "...",
            "submission_date": "...",
            "status": "PENDING"
        }
    }
    """
    permission_classes = [AllowAny]
    serializer_class = StudentRegistrationSerializer

    def create(self, request, *args, **kwargs):
        # Get organization from request data or URL
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

        serializer = self.get_serializer(
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


class StudentRegistrationVerifyAPIView(APIView):
    """
    GET /api/registration/student/verify/

    Verify registration status (Public).

    Query Parameters:
        - registration_id: Registration UUID
        - email: Registered email

    Response (200):
    {
        "success": true,
        "data": {...}
    }
    """
    permission_classes = [AllowAny]

    def get(self, request):
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
# PENDING STUDENT REGISTRATION API VIEWS
# =============================================================================

class PendingStudentListAPIView(ListAPIView):
    """
    GET /api/pending/students/

    List all pending student registrations.

    Query Parameters:
        - status: Filter by status (PENDING/APPROVED/REJECTED/INFO_REQUESTED)
        - branch: Interested branch ID
        - submission_date_from: Filter from date
        - submission_date_to: Filter to date

    Response (200):
    {
        "success": true,
        "count": 25,
        "results": [...]
    }
    """
    permission_classes = [IsAuthenticated, CanApproveRegistrations]
    serializer_class = PendingStudentListSerializer
    pagination_class = StudentPagination

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
            # Default to pending only
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


class PendingStudentDetailAPIView(RetrieveAPIView):
    """
    GET /api/pending/students/{id}/

    Get complete pending registration details.

    Response (200):
    {
        "success": true,
        "data": {...}
    }
    """
    permission_classes = [IsAuthenticated, CanApproveRegistrations]
    serializer_class = PendingStudentDetailSerializer
    lookup_field = 'id'

    def get_queryset(self):
        organization = self.request.user.organization
        return StudentRegistration.objects.filter(
            organization=organization
        ).select_related(
            'interested_branch',
            'class_to_admit',
            'reviewed_by'
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })


class PendingStudentApproveAPIView(APIView):
    """
    POST /api/pending/students/{id}/approve/

    Approve registration and create student record.

    Request:
    {
        "branch_id": "uuid",
        "class_id": "uuid",
        "division_id": "uuid",
        "category": "PERMANENT",
        "has_siblings": false,
        "notes": ""
    }

    Response (200):
    {
        "success": true,
        "message": "Student registration approved",
        "data": {
            "student_id": "uuid",
            "admission_number": "WAKR0001",
            "status": "ACTIVE"
        }
    }
    """
    permission_classes = [IsAuthenticated, CanApproveRegistrations]

    def post(self, request, id):
        organization = request.user.organization

        try:
            registration = StudentRegistration.objects.get(
                id=id,
                organization=organization,
                status='PENDING'
            )
        except StudentRegistration.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Registration not found or already processed'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PendingStudentApproveSerializer(
            data=request.data,
            context={
                'request': request,
                'registration': registration
            }
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


class PendingStudentRejectAPIView(APIView):
    """
    POST /api/pending/students/{id}/reject/

    Reject registration.

    Request:
    {
        "rejection_reason": "..."
    }

    Response (200):
    {
        "success": true,
        "message": "Registration rejected",
        "data": {...}
    }
    """
    permission_classes = [IsAuthenticated, CanApproveRegistrations]

    def post(self, request, id):
        organization = request.user.organization

        try:
            registration = StudentRegistration.objects.get(
                id=id,
                organization=organization,
                status='PENDING'
            )
        except StudentRegistration.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Registration not found or already processed'
            }, status=status.HTTP_404_NOT_FOUND)

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


class PendingStudentRequestInfoAPIView(APIView):
    """
    POST /api/pending/students/{id}/request-info/

    Request additional information from parent.

    Request:
    {
        "message": "Please submit..."
    }

    Response (200):
    {
        "success": true,
        "message": "Information request sent",
        "data": {...}
    }
    """
    permission_classes = [IsAuthenticated, CanApproveRegistrations]

    def post(self, request, id):
        organization = request.user.organization

        try:
            registration = StudentRegistration.objects.get(
                id=id,
                organization=organization,
                status__in=['PENDING', 'INFO_REQUESTED']
            )
        except StudentRegistration.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Registration not found or already processed'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PendingStudentRequestInfoSerializer(
            registration,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            registration = serializer.save()

            # TODO: Send email notification to parent

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
# UTILITY API VIEWS
# =============================================================================

class BranchListAPIView(APIView):
    """
    GET /api/utilities/branches/

    Get list of branches for the organization.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization
        branches = Branch.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('name')

        serializer = BranchMinimalSerializer(branches, many=True)
        return Response({
            'success': True,
            'results': serializer.data
        })


class ClassListAPIView(APIView):
    """
    GET /api/utilities/classes/

    Get list of classes for the organization.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization
        classes = Class.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('display_order', 'name')

        serializer = ClassMinimalSerializer(classes, many=True)
        return Response({
            'success': True,
            'results': serializer.data
        })


class DivisionListAPIView(APIView):
    """
    GET /api/utilities/divisions/

    Get list of divisions for the organization.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
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