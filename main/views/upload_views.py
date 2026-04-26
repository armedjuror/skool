"""
API Views for S3 Upload operations.

Provides endpoints for:
- Generating presigned upload URLs
- Confirming uploads
- Getting file information
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.apps import apps
from django.core.exceptions import ValidationError

from main.services.s3_service import S3Service
from main.serializers.upload_serializers import (
    PresignedUploadRequestSerializer,
    PresignedUploadResponseSerializer,
    UploadConfirmationSerializer,
)


class S3UploadViewSet(viewsets.GenericViewSet):
    """
    ViewSet for S3 upload operations.

    Endpoints:
    - POST /api/uploads/presigned-url/ - Get presigned upload URL
    - POST /api/uploads/confirm/ - Confirm upload and register file
    - GET /api/uploads/info/ - Get file information
    - POST /api/uploads/public-presigned-url/ - Public presigned URL (for registration forms)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s3_service = S3Service()

    def get_permissions(self):
        if self.action == 'public_presigned_url':
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='presigned-url')
    def presigned_url(self, request):
        """
        POST /api/uploads/presigned-url/

        Generate a presigned URL for authenticated users to upload files.
        Files are scoped to the user's organization.
        """
        serializer = PresignedUploadRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        organization = request.user.organization

        try:
            result = self.s3_service.generate_presigned_upload_url(
                organization_code=organization.code,
                filename=data['filename'],
                content_type=data['content_type'],
                file_category=data.get('file_category', 'image'),
                file_size=data.get('file_size'),
                entity_type=data.get('entity_type'),
                entity_id=str(data['entity_id']) if data.get('entity_id') else None,
                metadata=data.get('metadata', {})
            )

            response_serializer = PresignedUploadResponseSerializer(result)

            return Response({
                'success': True,
                'message': 'Presigned URL generated successfully',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e),
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to generate presigned URL: {str(e)}',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='public-presigned-url')
    def public_presigned_url(self, request):
        """
        POST /api/uploads/public-presigned-url/

        Generate a presigned URL for public uploads (e.g., student registration).
        Requires org_code in request body.
        """
        org_code = request.data.get('org_code')

        if not org_code:
            return Response({
                'success': False,
                'message': 'Organization code is required',
                'errors': {'org_code': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate organization exists
        from main.models import Organization
        try:
            organization = Organization.objects.get(code=org_code, is_active=True)
        except Organization.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid organization code',
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PresignedUploadRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Restrict public uploads to images only for security
        if data.get('file_category', 'image') != 'image':
            return Response({
                'success': False,
                'message': 'Public uploads only support images',
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = self.s3_service.generate_presigned_upload_url(
                organization_code=organization.code,
                filename=data['filename'],
                content_type=data['content_type'],
                file_category='image',
                file_size=data.get('file_size'),
                entity_type='registration',  # Always 'registration' for public
                metadata={'source': 'public_registration'}
            )

            response_serializer = PresignedUploadResponseSerializer(result)

            return Response({
                'success': True,
                'message': 'Presigned URL generated successfully',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e),
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to generate presigned URL: {str(e)}',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def confirm(self, request):
        """
        POST /api/uploads/confirm/

        Confirm that an upload completed and optionally associate it
        with a model field.
        """
        serializer = UploadConfirmationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        s3_key = data['s3_key']

        # Verify the file exists in S3
        if not self.s3_service.verify_upload_exists(s3_key):
            return Response({
                'success': False,
                'message': 'File not found in storage',
                'errors': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Get file info
        file_info = self.s3_service.get_file_info(s3_key)

        # If entity association is requested, update the model
        if data.get('entity_type') and data.get('entity_id') and data.get('field_name'):
            try:
                # Get the model class
                model_name = data['entity_type']

                # Map common names to actual models
                model_mapping = {
                    'Organization': 'main.Organization',
                    'UserProfile': 'main.UserProfile',
                    'StudentRegistration': 'main.StudentRegistration',
                    'DocumentUpload': 'main.DocumentUpload',
                }

                model_path = model_mapping.get(model_name, f'main.{model_name}')
                app_label, model_class = model_path.rsplit('.', 1)
                Model = apps.get_model(app_label, model_class)

                # Get the instance
                instance = Model.objects.get(id=data['entity_id'])

                # Verify organization access
                org = request.user.organization
                if hasattr(instance, 'organization') and instance.organization != org:
                    return Response({
                        'success': False,
                        'message': 'Access denied',
                        'errors': {}
                    }, status=status.HTTP_403_FORBIDDEN)

                # Update the field with the S3 key
                field_name = data['field_name']
                setattr(instance, field_name, s3_key)
                instance.save(update_fields=[field_name])

                file_info['associated'] = True
                file_info['entity_type'] = model_name
                file_info['entity_id'] = str(data['entity_id'])
                file_info['field_name'] = field_name

            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Failed to associate file: {str(e)}',
                    'errors': {}
                }, status=status.HTTP_400_BAD_REQUEST)

        # Generate a presigned URL for viewing the file
        file_info['url'] = self.s3_service.generate_presigned_download_url(s3_key)

        return Response({
            'success': True,
            'message': 'Upload confirmed successfully',
            'data': file_info
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def info(self, request):
        """
        GET /api/uploads/info/?key=<s3_key>

        Get information about an uploaded file.
        """
        s3_key = request.query_params.get('key')

        if not s3_key:
            return Response({
                'success': False,
                'message': 'S3 key is required',
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify organization access
        org_code = request.user.organization.code.lower()
        if not s3_key.startswith(f'media/{org_code}/'):
            return Response({
                'success': False,
                'message': 'Access denied',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        file_info = self.s3_service.get_file_info(s3_key)

        if not file_info:
            return Response({
                'success': False,
                'message': 'File not found',
                'errors': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Add presigned download URL
        file_info['url'] = self.s3_service.generate_presigned_download_url(s3_key)

        return Response({
            'success': True,
            'data': file_info
        }, status=status.HTTP_200_OK)
