"""
Serializers for Authentication APIs

This module contains all serializers for authentication-related operations
including login, password management, and user profile.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login

    Validates email and password, authenticates user,
    and returns user data with authentication token.
    """
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email is required',
            'invalid': 'Enter a valid email address'
        }
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required'
        }
    )
    remember_me = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        """
        Validate credentials and authenticate user
        """
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Authenticate user
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Invalid email or password',
                    code='authentication_failed'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'Your account has been deactivated. Please contact the administrator.',
                    code='account_inactive'
                )

            attrs['user'] = user
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password"',
                code='missing_credentials'
            )

        return attrs


class UserSerializer(serializers.Serializer):
    """
    Serializer for user profile data
    """
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    organization = serializers.SerializerMethodField()
    branch = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    def get_organization(self, obj):
        """Return organization details"""
        if hasattr(obj, 'organization') and obj.organization:
            return {
                'id': obj.organization.id,
                'name': obj.organization.name,
                'code': obj.organization.code
            }
        return None

    def get_branch(self, obj):
        """Return branch details if user is assigned to a branch"""
        if hasattr(obj, 'branch') and obj.branch:
            return {
                'id': obj.branch.id,
                'name': obj.branch.name,
                'code': obj.branch.code
            }
        return None

    def get_permissions(self, obj):
        """Return user's permissions based on role"""
        role_permissions = {
            'admin': {
                'students': {'view': True, 'create': True, 'edit': True, 'delete': True},
                'staff': {'view': True, 'create': True, 'edit': True, 'delete': True},
                'fees': {'view': True, 'collect': True, 'configure': True, 'reports': True},
                'attendance': {'view': True, 'mark': True, 'reports': True},
                'settings': {'view': True, 'edit': True}
            },
            'chief_head_teacher': {
                'students': {'view': True, 'create': True, 'edit': True, 'delete': True},
                'staff': {'view': True, 'create': True, 'edit': True, 'delete': True},
                'fees': {'view': True, 'collect': True, 'configure': True, 'reports': True},
                'attendance': {'view': True, 'mark': True, 'reports': True},
                'settings': {'view': True, 'edit': False}
            },
            'head_teacher': {
                'students': {'view': True, 'create': True, 'edit': True, 'delete': True},
                'staff': {'view': True, 'create': True, 'edit': True, 'delete': True},
                'fees': {'view': True, 'collect': True, 'configure': True, 'reports': True},
                'attendance': {'view': True, 'mark': True, 'reports': True},
                'settings': {'view': False, 'edit': False}
            },
            'teacher': {
                'students': {'view': True, 'create': False, 'edit': False, 'delete': False},
                'staff': {'view': False, 'create': False, 'edit': False, 'delete': False},
                'fees': {'view': False, 'collect': False, 'configure': False, 'reports': False},
                'attendance': {'view': True, 'mark': True, 'reports': False},
                'settings': {'view': False, 'edit': False}
            },
            'accountant': {
                'students': {'view': False, 'create': False, 'edit': False, 'delete': False},
                'staff': {'view': False, 'create': False, 'edit': False, 'delete': False},
                'fees': {'view': True, 'collect': True, 'configure': False, 'reports': True},
                'attendance': {'view': False, 'mark': False, 'reports': False},
                'settings': {'view': False, 'edit': False}
            }
        }

        return role_permissions.get(obj.role, {})


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password (requires current password)
    """
    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={'required': 'Current password is required'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={'required': 'New password is required'}
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={'required': 'Password confirmation is required'}
    )

    def validate_current_password(self, value):
        """Validate that current password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value

    def validate_new_password(self, value):
        """Validate new password using Django's password validators"""
        try:
            validate_password(value, user=self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Ensure new password and confirmation match"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Password confirmation does not match'
            })

        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from current password'
            })

        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Serializer for password reset request (forgot password)
    """
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email is required',
            'invalid': 'Enter a valid email address'
        }
    )

    def validate_email(self, value):
        """Validate that email exists in the system"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            # Don't reveal whether email exists or not (security)
            # Still return success but don't send email
            pass

        return value


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for password reset with token
    """
    token = serializers.CharField(
        required=True,
        error_messages={'required': 'Reset token is required'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={'required': 'New password is required'}
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={'required': 'Password confirmation is required'}
    )

    def validate_new_password(self, value):
        """Validate new password using Django's password validators"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Ensure new password and confirmation match"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Password confirmation does not match'
            })
        return attrs


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for logout (no fields required)
    """
    pass