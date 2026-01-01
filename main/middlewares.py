"""
Custom Middleware for KIC Madrassa Management System

This module contains middleware for:
1. Organization context injection
2. Token authentication for API requests
3. Multi-tenancy enforcement
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser


class OrganizationMiddleware(MiddlewareMixin):
    """
    Middleware to inject organization context into request

    This middleware extracts the organization code from the URL and
    adds the organization object to the request for easy access.

    URL Pattern: /<org_code>/...
    """

    def process_request(self, request):
        """Add organization to request if org_code is in URL"""

        # Skip for API endpoints (they use different auth)
        if request.path.startswith('/api/'):
            return None

        # Extract org_code from URL path
        path_parts = request.path.strip('/').split('/')

        if path_parts and path_parts[0]:
            org_code = path_parts[0]

            # Try to get organization
            from main.models import Organization
            try:
                organization = Organization.objects.get(
                    code=org_code,
                    is_active=True
                )
                request.organization = organization
            except Organization.DoesNotExist:
                request.organization = None
        else:
            request.organization = None

        return None


class TokenAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate API requests using token from Authorization header

    This middleware checks for Bearer token in Authorization header and
    authenticates the user for API requests.

    Header Format: Authorization: Bearer <token>
    """

    def process_request(self, request):
        """Authenticate user from token if present"""

        # Only process API requests
        if not request.path.startswith('/api/'):
            return None

        # Skip authentication endpoints
        if request.path.startswith('/api/auth/login/') or \
                request.path.startswith('/api/auth/forgot-password/') or \
                request.path.startswith('/api/auth/reset-password/') or \
                request.path.startswith('/api/registration/'):
            return None

        # Get authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header.startswith('Bearer '):
            token_key = auth_header.split(' ')[1]

            try:
                # Get token and user
                token = Token.objects.select_related('user').get(key=token_key)

                # Check if user is active
                if token.user.is_active:
                    request.user = token.user
                else:
                    request.user = AnonymousUser()
            except Token.DoesNotExist:
                request.user = AnonymousUser()

        return None


class MultiTenancyMiddleware(MiddlewareMixin):
    """
    Middleware to enforce multi-tenancy isolation

    This middleware ensures that users can only access data from their
    own organization. It validates that the authenticated user belongs
    to the organization specified in the request.
    """

    def process_request(self, request):
        """Validate user's organization matches request organization"""

        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None

        # Skip for API auth endpoints
        if request.path.startswith('/api/auth/'):
            return None

        # For API requests, check org_code in URL or headers
        if request.path.startswith('/api/'):
            # Organization can be in custom header for API requests
            org_code = request.META.get('HTTP_X_ORGANIZATION_CODE')

            if org_code:
                # Validate user belongs to this organization
                if hasattr(request.user, 'organization'):
                    if request.user.organization.code != org_code:
                        return JsonResponse({
                            'success': False,
                            'message': 'You do not have permission to access this organization\'s data'
                        }, status=403)

        # For web requests, check org_code in URL
        else:
            if hasattr(request, 'organization') and request.organization:
                # Validate user belongs to this organization
                if hasattr(request.user, 'organization'):
                    if request.user.organization != request.organization:
                        from django.shortcuts import render
                        return render(request, 'main/error.html', {
                            'error_title': 'Access Denied',
                            'error_message': 'You do not have permission to access this organization.'
                        }, status=403)

        return None


class APIErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware to handle API errors and return consistent JSON responses
    """

    def process_exception(self, request, exception):
        """Handle exceptions for API requests"""

        # Only process API requests
        if not request.path.startswith('/api/'):
            return None

        # Log the exception
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'API Error: {str(exception)}', exc_info=True)

        # Return JSON error response
        return JsonResponse({
            'success': False,
            'message': 'An internal server error occurred. Please try again later.',
            'error': str(exception) if settings.DEBUG else 'Internal server error'
        }, status=500)


class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt API endpoints from CSRF validation

    API endpoints use token authentication, so they don't need CSRF protection.
    """

    def process_request(self, request):
        """Exempt API requests from CSRF validation"""

        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)

        return None