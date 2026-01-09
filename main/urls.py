"""
URL Configuration for Kerala Islamic Centre Madrassa Management System

This module contains all URL patterns for:
- Web views (HTML pages)
- API views (REST endpoints)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# API Views
from main.views.api import (
    # ViewSets
    AuthViewSet,
    DashboardViewSet,
    StudentViewSet,
    StudentRegistrationViewSet,
    PendingStudentViewSet,
    SettingsViewSet,
    # CRUD ViewSets
    AcademicYearViewSet,
    BranchViewSet,
    ClassViewSet,
    DivisionViewSet,
    StaffViewSet,
    SystemSettingViewSet, UsersViewSet,
)
# Web Views
from main.views.web import (
    login_view,
    logout_view,
    password_reset_request_view,
    password_reset_view,
    dashboard_view,
    students_list_view,
    pending_registrations_view,
    student_registration_form_view,
    settings_view,
    staff_list_view,
    fees_view,
    attendance_view,
    reports_view,
)

router = DefaultRouter()

# Register ViewSets
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'students', StudentViewSet, basename='students')
router.register(r'registration/student', StudentRegistrationViewSet, basename='registration')
router.register(r'pending/students', PendingStudentViewSet, basename='pending-students')
router.register(r'utilities', SettingsViewSet, basename='utilities')

# CRUD ViewSets for Settings
router.register(r'academic-years', AcademicYearViewSet, basename='academic-years')
router.register(r'branches', BranchViewSet, basename='branches')
router.register(r'classes', ClassViewSet, basename='classes')
router.register(r'divisions', DivisionViewSet, basename='divisions')
router.register(r'staffs', StaffViewSet, basename='staff')
router.register(r'users', UsersViewSet, basename='users')
router.register(r'system-settings', SystemSettingViewSet, basename='system-settings')


urlpatterns = [
    # ==========================================================================
    # WEB VIEWS (HTML Pages)
    # ==========================================================================

    # Authentication
    path('<str:org_code>/login/', login_view, name='login'),
    path('<str:org_code>/logout/', logout_view, name='logout'),
    path('forgot-password/', password_reset_request_view, name='password-reset-request'),
    path('reset-password/', password_reset_view, name='password-reset'),

    # Dashboard
    path('<str:org_code>/dashboard/', dashboard_view, name='dashboard'),

    # Students
    path('<str:org_code>/students/', students_list_view, name='students-list'),

    # Pending Registrations
    path('<str:org_code>/registrations/', pending_registrations_view, name='pending-registrations'),

    # Public Registration Forms
    path('register/student/', student_registration_form_view, name='student-registration-public'),
    path('<str:org_code>/register/student/', student_registration_form_view, name='student-registration'),

    # Staff Management
    path('<str:org_code>/staff/', staff_list_view, name='staff-list'),

    # Fee Management
    path('<str:org_code>/fees/', fees_view, name='fees'),

    # Attendance
    path('<str:org_code>/attendance/', attendance_view, name='attendance'),

    # Reports
    path('<str:org_code>/reports/', reports_view, name='reports'),

    # Settings
    path('<str:org_code>/settings/', settings_view, name='settings'),
    # ==========================================================================
    # API VIEWS (REST Endpoints)
    # ==========================================================================
    path('api/', include(router.urls)),
    # Authentication APIs
    # path('api/auth/login/', LoginAPIView.as_view(), name='api-login'),
    # path('api/auth/logout/', LogoutAPIView.as_view(), name='api-logout'),
    # path('api/auth/user/', CurrentUserAPIView.as_view(), name='api-current-user'),
    # path('api/auth/change-password/', ChangePasswordAPIView.as_view(), name='api-change-password'),
    # path('api/auth/forgot-password/', ForgotPasswordAPIView.as_view(), name='api-forgot-password'),
    # path('api/auth/reset-password/', ResetPasswordAPIView.as_view(), name='api-reset-password'),
    #
    # # Dashboard APIs
    # path('api/dashboard/stats/', DashboardStatsAPIView.as_view(), name='api-dashboard-stats'),
    # path('api/dashboard/recent-activity/', RecentActivityAPIView.as_view(), name='api-recent-activity'),
    # path('api/dashboard/notifications/', NotificationsAPIView.as_view(), name='api-notifications'),
    #
    # # Student CRUD APIs
    # path('api/students/', StudentListAPIView.as_view(), name='api-student-list'),
    # path('api/students/<uuid:id>/', StudentDetailAPIView.as_view(), name='api-student-detail'),
    # path('api/students/create/', StudentCreateAPIView.as_view(), name='api-student-create'),
    # path('api/students/<uuid:id>/update/', StudentUpdateAPIView.as_view(), name='api-student-update'),
    # path('api/students/<uuid:id>/delete/', StudentDeleteAPIView.as_view(), name='api-student-delete'),
    # path('api/students/search/', StudentSearchAPIView.as_view(), name='api-student-search'),
    #
    # # Student Registration APIs (Public)
    # path('api/registration/student/', StudentRegistrationSubmitAPIView.as_view(), name='api-student-registration'),
    # path('api/registration/student/verify/', StudentRegistrationVerifyAPIView.as_view(), name='api-registration-verify'),
    #
    # # Pending Student Registration APIs
    # path('api/pending/students/', PendingStudentListAPIView.as_view(), name='api-pending-students'),
    # path('api/pending/students/<uuid:id>/', PendingStudentDetailAPIView.as_view(), name='api-pending-student-detail'),
    # path('api/pending/students/<uuid:id>/approve/', PendingStudentApproveAPIView.as_view(), name='api-pending-student-approve'),
    # path('api/pending/students/<uuid:id>/reject/', PendingStudentRejectAPIView.as_view(), name='api-pending-student-reject'),
    # path('api/pending/students/<uuid:id>/request-info/', PendingStudentRequestInfoAPIView.as_view(), name='api-pending-student-request-info'),
    #
    # # Utility APIs
    # path('api/settings/branches/', BranchListAPIView.as_view(), name='api-branches'),
    # path('api/settings/classes/', ClassListAPIView.as_view(), name='api-classes'),
    # path('api/settings/divisions/', DivisionListAPIView.as_view(), name='api-divisions'),
]