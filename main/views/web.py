"""
Web Views for Authentication

This module contains Django views that render HTML templates for authentication.
These views handle the web interface for login and logout.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import logout as django_logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from main.models import Organization


def default_view(request):
    return redirect('/KIC/login/')

@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request, org_code):
    """
    Organization-specific login page

    URL: /<org_code>/login/
    Template: main/login.html

    GET: Renders login form
    POST: Handled by JavaScript/API (AJAX submission)

    Context:
        - organization: Organization object (validated by org_code)
        - org_code: Organization code from URL
        - next: Redirect URL after successful login
    """

    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        # Verify user belongs to this organization
        if hasattr(request.user, 'organization') and request.user.organization.code == org_code:
            return redirect('dashboard', org_code=org_code)
        else:
            # User belongs to different organization
            messages.warning(request, 'You are logged in to a different organization.')
            django_logout(request)

    # Validate organization code
    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        messages.error(request, f'Organization "{org_code}" not found or inactive.')
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid or the organization is inactive.'
        }, status=404)

    # Get redirect URL from query params (for redirecting after login)
    next_url = request.GET.get('next', f'/{org_code}/dashboard/')
    context = {
        'organization': organization,
        'org_code': org_code,
        'next': next_url,
        'page_title': f'Login - {organization.name}',
    }

    return render(request, 'main/login.html', context)


@require_http_methods(["GET"])
def logout_view(request, org_code):
    """
    Logout user and redirect to login page

    URL: /<org_code>/logout/
    Method: POST only (for security)

    This view handles session logout. Token deletion is handled by API.
    """

    # Logout the user
    django_logout(request)

    # Add success message
    messages.success(request, 'You have been successfully logged out.')

    # Redirect to login page
    return redirect('login', org_code=org_code)


def password_reset_request_view(request):
    """
    Password reset request page (forgot password)

    URL: /forgot-password/
    Template: main/forgot_password.html

    GET: Renders password reset request form
    POST: Handled by JavaScript/API (AJAX submission)
    """

    # If user is already logged in, redirect to their dashboard
    if request.user.is_authenticated:
        org_code = request.user.organization.code
        return redirect('dashboard', org_code=org_code)

    context = {
        'page_title': 'Forgot Password',
    }

    return render(request, 'main/forgot_password.html', context)


def password_reset_view(request):
    """
    Password reset page (with token from email)

    URL: /reset-password/
    Template: main/reset_password.html

    GET: Renders password reset form
    POST: Handled by JavaScript/API (AJAX submission)

    Query Parameters:
        - token: Password reset token from email
    """

    # Get token from query params
    token = request.GET.get('token')

    if not token:
        messages.error(request, 'Invalid password reset link.')
        return redirect('password-reset-request')

    context = {
        'page_title': 'Reset Password',
        'token': token,
    }

    return render(request, 'main/reset_password.html', context)

def dashboard_view(request, org_code):
    """
    Main dashboard page - role-based content

    URL: /<org_code>/dashboard/
    Template: main/dashboard.html

    Context:
        - organization: Organization object
        - org_code: Organization code from URL
        - user: Current authenticated user
        - user_role: User's role for permission checks
        - branches: Available branches (for filters)
        - classes: Available classes (for filters)
        - page_title: Page title for browser
    """
    from django.contrib.auth.decorators import login_required
    from main.models import Branch, Class, Division

    # Redirect to login if not authenticated
    if not request.user.is_authenticated:
        return redirect('login', org_code=org_code)

    # Validate organization code
    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        messages.error(request, f'Organization "{org_code}" not found or inactive.')
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid or the organization is inactive.'
        }, status=404)

    # Verify user belongs to this organization
    if request.user.organization != organization:
        messages.warning(request, 'You do not have access to this organization.')
        return redirect('login', org_code=org_code)

    # Get branches and classes for filters
    branches = Branch.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    classes = Class.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('level', 'name')

    divisions = Division.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    # Get user role
    user_role = request.user.role if hasattr(request.user, 'role') else 'unknown'

    context = {
        'organization': organization,
        'org_code': org_code,
        'user': request.user,
        'user_role': user_role,
        'branches': branches,
        'classes': classes,
        'divisions': divisions,
        'page_title': f'Dashboard - {organization.name}',
    }

    return render(request, 'main/dashboard.html', context)


def students_list_view(request, org_code):
    """
    Students management page with filters and search

    URL: /<org_code>/students/
    Template: main/students.html
    """
    from main.models import Branch, Class, Division

    # Redirect to login if not authenticated
    if not request.user.is_authenticated:
        return redirect('login', org_code=org_code)

    # Validate organization code
    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid.'
        }, status=404)

    # Verify user belongs to this organization
    if request.user.organization != organization:
        return redirect('login', org_code=org_code)

    # Get branches and classes for filters
    branches = Branch.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    classes = Class.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('level', 'name')

    divisions = Division.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    context = {
        'organization': organization,
        'org_code': org_code,
        'branches': branches,
        'classes': classes,
        'divisions': divisions,
        'page_title': f'Students - {organization.name}',
    }

    return render(request, 'main/students.html', context)


def pending_registrations_view(request, org_code):
    """
    Pending student and staff registrations

    URL: /<org_code>/registrations/
    Template: main/registrations.html
    """
    from main.models import Branch, Class

    # Redirect to login if not authenticated
    if not request.user.is_authenticated:
        return redirect('login', org_code=org_code)

    # Validate organization code
    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid.'
        }, status=404)

    # Verify user belongs to this organization
    if request.user.organization != organization:
        return redirect('login', org_code=org_code)

    # Get branches and classes for filters
    branches = Branch.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    classes = Class.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('level', 'name')

    context = {
        'organization': organization,
        'org_code': org_code,
        'branches': branches,
        'classes': classes,
        'page_title': f'Pending Registrations - {organization.name}',
    }

    return render(request, 'main/registrations.html', context)


def student_registration_form_view(request, org_code=None):
    """
    Public student registration form

    URL: /register/student/ or /<org_code>/register/student/
    Template: main/student_registration.html
    """
    from main.models import Branch, Class

    # Get organization from URL or query params
    if not org_code:
        org_code = request.GET.get('org')

    if not org_code:
        return render(request, 'main/error.html', {
            'status': 400,
            'error_title': 'Organization Required',
            'error_message': 'Please provide an organization code.'
        }, status=400)

    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid.'
        }, status=404)

    # Get branches and classes
    branches = Branch.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    classes = Class.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('level', 'name')

    context = {
        'organization': organization,
        'org_code': org_code,
        'branches': branches,
        'classes': classes,
        'page_title': f'Student Registration - {organization.name}',
    }

    return render(request, 'main/student_registration.html', context)

def settings_view(request, org_code):
    """
    Settings page

    URL: /<org_code>/settings/
    Template: main/settings.html
    """
    if not request.user.is_authenticated:
        return redirect('login', org_code=org_code)

    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid.'
        }, status=404)

    if request.user.organization != organization:
        return redirect('login', org_code=org_code)

    context = {
        'organization': organization,
        'org_code': org_code,
        'user': request.user,
        'page_title': f'Settings - {organization.name}',
    }

    return render(request, 'main/settings.html', context)


def staff_list_view(request, org_code):
    """
    Staff management page

    URL: /<org_code>/staff/
    Template: main/staff.html
    """
    from main.models import Branch

    if not request.user.is_authenticated:
        return redirect('login', org_code=org_code)

    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid.'
        }, status=404)

    if request.user.organization != organization:
        return redirect('login', org_code=org_code)

    branches = Branch.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    context = {
        'organization': organization,
        'org_code': org_code,
        'user': request.user,
        'branches': branches,
        'page_title': f'Staff Management - {organization.name}',
    }

    return render(request, 'main/staff.html', context)


def fees_view(request, org_code):
    """
    Fee management page

    URL: /<org_code>/fees/
    Template: main/fees.html
    """
    from main.models import Branch, Class

    if not request.user.is_authenticated:
        return redirect('login', org_code=org_code)

    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid.'
        }, status=404)

    if request.user.organization != organization:
        return redirect('login', org_code=org_code)

    branches = Branch.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    classes = Class.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('level', 'name')

    context = {
        'organization': organization,
        'org_code': org_code,
        'user': request.user,
        'branches': branches,
        'classes': classes,
        'page_title': f'Fee Management - {organization.name}',
    }

    return render(request, 'main/fees.html', context)


def attendance_view(request, org_code):
    """
    Attendance management page

    URL: /<org_code>/attendance/
    Template: main/attendance.html
    """
    from main.models import Branch, Class, Division

    if not request.user.is_authenticated:
        return redirect('login', org_code=org_code)

    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid.'
        }, status=404)

    if request.user.organization != organization:
        return redirect('login', org_code=org_code)

    branches = Branch.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    classes = Class.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('level', 'name')

    divisions = Division.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    context = {
        'organization': organization,
        'org_code': org_code,
        'user': request.user,
        'branches': branches,
        'classes': classes,
        'divisions': divisions,
        'page_title': f'Attendance - {organization.name}',
    }

    return render(request, 'main/attendance.html', context)


def reports_view(request, org_code):
    """
    Reports page

    URL: /<org_code>/reports/
    Template: main/reports.html
    """
    from main.models import Branch, Class

    if not request.user.is_authenticated:
        return redirect('login', org_code=org_code)

    try:
        organization = Organization.objects.get(code=org_code, is_active=True)
    except Organization.DoesNotExist:
        return render(request, 'main/error.html', {
            'status': 404,
            'error_title': 'Organization Not Found',
            'error_message': f'The organization code "{org_code}" is invalid.'
        }, status=404)

    if request.user.organization != organization:
        return redirect('login', org_code=org_code)

    branches = Branch.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('name')

    classes = Class.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('level', 'name')

    context = {
        'organization': organization,
        'org_code': org_code,
        'user': request.user,
        'branches': branches,
        'classes': classes,
        'page_title': f'Reports - {organization.name}',
    }

    return render(request, 'main/reports.html', context)