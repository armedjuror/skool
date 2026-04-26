"""
S3 Service for AWS S3 operations including presigned URL generation.

This service provides:
- Presigned URL generation for direct client uploads
- File validation (type, size)
- Organization-scoped file paths
- Upload confirmation and registration
"""

import uuid
import mimetypes
from datetime import datetime
from typing import Dict, Optional

from django.conf import settings
from django.core.exceptions import ValidationError

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config


class S3Service:
    """
    Service class for S3 operations with presigned URL support.
    """

    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def get_allowed_content_types(self, file_category: str) -> list:
        """
        Get allowed content types for a file category.

        Args:
            file_category: 'image', 'document', or 'any'

        Returns:
            List of allowed MIME types
        """
        return settings.AWS_ALLOWED_FILE_TYPES.get(file_category, ['*'])

    def validate_file_type(self, content_type: str, file_category: str) -> bool:
        """
        Validate if a content type is allowed for the given category.

        Args:
            content_type: MIME type of the file
            file_category: Category ('image', 'document', 'any')

        Returns:
            True if valid, raises ValidationError otherwise
        """
        allowed_types = self.get_allowed_content_types(file_category)

        if '*' in allowed_types:
            return True

        if content_type not in allowed_types:
            raise ValidationError(
                f"File type '{content_type}' not allowed. "
                f"Allowed types: {', '.join(allowed_types)}"
            )

        return True

    def validate_file_size(self, file_size_bytes: int) -> bool:
        """
        Validate file size against maximum allowed.

        Args:
            file_size_bytes: Size of file in bytes

        Returns:
            True if valid, raises ValidationError otherwise
        """
        max_size_bytes = settings.AWS_MAX_FILE_SIZE_MB * 1024 * 1024

        if file_size_bytes > max_size_bytes:
            raise ValidationError(
                f"File size exceeds maximum allowed "
                f"({settings.AWS_MAX_FILE_SIZE_MB} MB)"
            )

        return True

    def generate_s3_key(
        self,
        organization_code: str,
        file_category: str,
        original_filename: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> str:
        """
        Generate a unique S3 object key with organization scoping.

        Path structure:
        media/{org_code}/{category}/{YYYY}/{MM}/{uuid}_{original_filename}

        Args:
            organization_code: Organization code for scoping
            file_category: Category of file (photos, documents, logos)
            original_filename: Original filename
            entity_type: Optional entity type (student, staff, etc.)
            entity_id: Optional entity ID

        Returns:
            S3 object key
        """
        now = datetime.utcnow()
        unique_id = uuid.uuid4().hex[:12]

        # Sanitize filename
        safe_filename = "".join(
            c for c in original_filename if c.isalnum() or c in '.-_'
        ).strip()

        # Ensure filename isn't empty after sanitization
        if not safe_filename:
            extension = mimetypes.guess_extension(file_category) or '.bin'
            safe_filename = f"file{extension}"

        # Build path components
        path_parts = [
            'media',
            organization_code.lower(),
            file_category,
            str(now.year),
            f"{now.month:02d}",
        ]

        if entity_type:
            path_parts.append(entity_type)

        # Final filename with UUID prefix for uniqueness
        filename = f"{unique_id}_{safe_filename}"
        path_parts.append(filename)

        return '/'.join(path_parts)

    def generate_presigned_upload_url(
        self,
        organization_code: str,
        filename: str,
        content_type: str,
        file_category: str = 'image',
        file_size: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a presigned URL for direct client upload to S3.

        Args:
            organization_code: Organization code for scoping
            filename: Original filename
            content_type: MIME type of the file
            file_category: Category ('image', 'document')
            file_size: Optional file size for pre-validation
            entity_type: Optional entity type
            entity_id: Optional entity ID
            metadata: Optional metadata to attach to the file

        Returns:
            Dict with presigned URL, fields, and upload key
        """
        # Validate file type
        self.validate_file_type(content_type, file_category)

        # Validate file size if provided
        if file_size:
            self.validate_file_size(file_size)

        # Generate unique S3 key
        s3_key = self.generate_s3_key(
            organization_code=organization_code,
            file_category=file_category,
            original_filename=filename,
            entity_type=entity_type,
            entity_id=entity_id
        )

        try:
            # Generate presigned POST data (preferred for browser uploads)
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={
                    'Content-Type': content_type,
                },
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 0, settings.AWS_MAX_FILE_SIZE_MB * 1024 * 1024],
                ],
                ExpiresIn=settings.AWS_PRESIGNED_UPLOAD_EXPIRY
            )

            return {
                'upload_url': presigned_post['url'],
                'fields': presigned_post['fields'],
                's3_key': s3_key,
                'expires_in': settings.AWS_PRESIGNED_UPLOAD_EXPIRY,
                'max_file_size': settings.AWS_MAX_FILE_SIZE_MB * 1024 * 1024,
            }

        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    def generate_presigned_download_url(
        self,
        s3_key: str,
        expiry_seconds: Optional[int] = None
    ) -> str:
        """
        Generate a presigned URL for downloading/viewing a file.

        Args:
            s3_key: S3 object key
            expiry_seconds: URL expiry time (default from settings)

        Returns:
            Presigned URL string
        """
        expiry = expiry_seconds or settings.AWS_PRESIGNED_URL_EXPIRY

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                },
                ExpiresIn=expiry
            )
            return url

        except ClientError as e:
            raise Exception(f"Failed to generate download URL: {str(e)}")

    def verify_upload_exists(self, s3_key: str) -> bool:
        """
        Verify that a file exists in S3 after upload.

        Args:
            s3_key: S3 object key

        Returns:
            True if file exists
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def get_file_info(self, s3_key: str) -> Optional[Dict]:
        """
        Get metadata about a file in S3.

        Args:
            s3_key: S3 object key

        Returns:
            Dict with file info or None if not found
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            return {
                'key': s3_key,
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'].isoformat(),
                'metadata': response.get('Metadata', {}),
            }

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            raise

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: S3 object key

        Returns:
            True if deleted successfully
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError:
            return False

    def get_full_url(self, s3_key: str) -> str:
        """
        Get the full public URL for an S3 object.
        Note: This only works if the object is public.

        For private objects, use generate_presigned_download_url.

        Args:
            s3_key: S3 object key

        Returns:
            Full URL to the object
        """
        return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
