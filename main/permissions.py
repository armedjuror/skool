"""
Custom Permissions for Kerala Islamic Centre Madrassa Management System

This module implements role-based access control (RBAC) for the multi-tenant
madrassa management system with organization and branch-level filtering.

Roles Hierarchy (from highest to lowest):
1. Admin (Super Admin)
2. Chief Head Teacher
3. Head Teacher (Branch-level)
4. Teacher
5. Accountant
"""

from rest_framework.permissions import BasePermission


class IsOrganizationMember(BasePermission):
    """
    Permission to check if user belongs to the organization.

    Applied to all authenticated views to ensure organization-level data isolation.
    Users can only access data from their own organization.
    """

    message = "You do not have permission to access this organization's data."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Get organization from view kwargs (from URL)
        org_code = view.kwargs.get('org_code')
        if not org_code:
            return False

        # Check if user belongs to this organization
        return request.user.organization.code == org_code

    def has_object_permission(self, request, view, obj):
        """Ensure object belongs to user's organization"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if object has organization attribute
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization

        return False


class IsAdmin(BasePermission):
    """
    Permission for Admin or Chief Head Teacher only.

    These roles have full access to:
    - All students (across all branches)
    - All staff management
    - All fee operations
    - All attendance records
    - Full system settings
    """

    message = "Only Admins or Chief Head Teachers can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['admin', 'chief_head_teacher']


class IsHeadTeacher(BasePermission):
    """
    Permission for Head Teacher or above (includes Admin and Chief Head Teacher).

    Head Teachers have:
    - Full access to their branch's students
    - Branch staff management
    - Branch fee operations
    - Branch attendance records
    - Limited settings access
    """

    message = "This action requires Head Teacher level access or above."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['admin', 'chief_head_teacher', 'head_teacher']

    def has_object_permission(self, request, view, obj):
        """Head teachers can only access their branch's data"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins and Chief Head Teachers can access all branches
        if request.user.role in ['admin', 'chief_head_teacher']:
            return True

        # Head teachers can only access their branch
        if request.user.role == 'head_teacher':
            if hasattr(obj, 'branch'):
                return obj.branch == request.user.branch

        return False


class IsTeacher(BasePermission):
    """
    Permission for Teacher or above.

    Teachers have:
    - View access to students in their classes
    - No staff access
    - No fee operations
    - Can mark attendance for their classes
    - No settings access
    """

    message = "This action requires Teacher level access or above."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['admin', 'chief_head_teacher', 'head_teacher', 'teacher']


class IsAccountant(BasePermission):
    """
    Permission for Accountant role.

    Accountants have:
    - No student management access
    - No staff access
    - Full fee operations (view, collect, reports)
    - No attendance access
    - No settings access
    """

    message = "This action requires Accountant access."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role == 'accountant'


class IsBranchStaff(BasePermission):
    """
    Permission to check if user belongs to specific branch.

    Used for branch-level filtering where Head Teachers and below
    should only access their assigned branch data.
    """

    message = "You do not have permission to access this branch's data."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins and Chief Head Teachers can access all branches
        if request.user.role in ['admin', 'chief_head_teacher']:
            return True

        # Get branch from request (could be in URL params or POST data)
        branch_id = view.kwargs.get('branch_id') or request.data.get('branch_id')
        if not branch_id:
            return False

        # Check if user's branch matches requested branch
        return str(request.user.branch_id) == str(branch_id)

    def has_object_permission(self, request, view, obj):
        """Ensure object belongs to user's branch"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins and Chief Head Teachers can access all branches
        if request.user.role in ['admin', 'chief_head_teacher']:
            return True

        # Check if object has branch attribute
        if hasattr(obj, 'branch'):
            return obj.branch == request.user.branch

        return False


class CanManageStudents(BasePermission):
    """
    Permission to manage students (create, update, delete).
    Only Head Teachers and above can manage students.
    """

    message = "You do not have permission to manage students."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Teachers can only view, not manage
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.role in ['admin', 'chief_head_teacher', 'head_teacher', 'teacher']

        # Only Head Teachers and above can create/update/delete
        return request.user.role in ['admin', 'chief_head_teacher', 'head_teacher']


class CanManageStaff(BasePermission):
    """
    Permission to manage staff (create, update, delete).
    Only Head Teachers and above can manage staff.
    """

    message = "You do not have permission to manage staff."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['admin', 'chief_head_teacher', 'head_teacher']


class CanManageFees(BasePermission):
    """
    Permission to manage fees.
    Accountants and Head Teachers (and above) can manage fees.
    """

    message = "You do not have permission to manage fees."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['admin', 'chief_head_teacher', 'head_teacher', 'accountant']


class CanMarkAttendance(BasePermission):
    """
    Permission to mark attendance.
    Teachers and above can mark attendance.
    """

    message = "You do not have permission to mark attendance."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['admin', 'chief_head_teacher', 'head_teacher', 'teacher']


class CanManageSettings(BasePermission):
    """
    Permission to manage system settings.
    Only Admins and Chief Head Teachers can manage settings.
    """

    message = "You do not have permission to manage system settings."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['admin', 'chief_head_teacher']


class CanApproveRegistrations(BasePermission):
    """
    Permission to approve/reject pending registrations.
    Only Head Teachers and above can approve registrations.
    """

    message = "You do not have permission to approve registrations."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['admin', 'chief_head_teacher', 'head_teacher']


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Write permissions are only allowed to the owner
        return obj.owner == request.user