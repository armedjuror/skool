"""
Serializers Package for Kerala Islamic Centre Madrassa Management System

This package contains all serializers organized by module:
- auth_serializers: Authentication-related serializers
- student_serializers: Student management serializers
- dashboard_serializers: Dashboard data serializers
"""

from .auth_serializers import (
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    LogoutSerializer
)

from .student_serializers import (
    # List/Basic serializers
    StudentListSerializer,
    StudentDetailSerializer,

    # CRUD serializers
    StudentCreateSerializer,
    StudentUpdateSerializer,

    # Registration serializers
    StudentRegistrationSerializer,
    StudentRegistrationVerifySerializer,

    # Pending registration serializers
    PendingStudentListSerializer,
    PendingStudentDetailSerializer,
    PendingStudentApproveSerializer,
    PendingStudentRejectSerializer,
    PendingStudentRequestInfoSerializer,
)

from .dashboard_serializers import (
    DashboardStatsSerializer,
    RecentActivitySerializer,
    NotificationSerializer,
)