"""
Serializers for S3 Upload API endpoints.
"""

from rest_framework import serializers


class PresignedUploadRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a presigned upload URL.
    """
    filename = serializers.CharField(
        max_length=255,
        help_text="Original filename"
    )
    content_type = serializers.CharField(
        max_length=100,
        help_text="MIME type of the file (e.g., 'image/jpeg')"
    )
    file_category = serializers.ChoiceField(
        choices=['image', 'document', 'any'],
        default='image',
        help_text="Category of file for validation"
    )
    file_size = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="File size in bytes (optional, for pre-validation)"
    )
    entity_type = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Related entity type (e.g., 'student', 'staff')"
    )
    entity_id = serializers.UUIDField(
        required=False,
        help_text="Related entity ID"
    )
    metadata = serializers.DictField(
        required=False,
        help_text="Additional metadata to attach to the file"
    )


class PresignedUploadResponseSerializer(serializers.Serializer):
    """
    Serializer for presigned upload URL response.
    """
    upload_url = serializers.URLField(
        help_text="URL to POST the file to"
    )
    fields = serializers.DictField(
        help_text="Form fields to include with the upload"
    )
    s3_key = serializers.CharField(
        help_text="S3 object key for the uploaded file"
    )
    expires_in = serializers.IntegerField(
        help_text="Seconds until the presigned URL expires"
    )
    max_file_size = serializers.IntegerField(
        help_text="Maximum allowed file size in bytes"
    )


class UploadConfirmationSerializer(serializers.Serializer):
    """
    Serializer for confirming an upload and registering it.
    """
    s3_key = serializers.CharField(
        max_length=500,
        help_text="S3 object key returned from presigned URL generation"
    )
    entity_type = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Model name to associate with (e.g., 'Organization', 'UserProfile')"
    )
    entity_id = serializers.UUIDField(
        required=False,
        help_text="ID of the entity to associate the file with"
    )
    field_name = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Field name to update (e.g., 'logo', 'photo')"
    )


class FileInfoSerializer(serializers.Serializer):
    """
    Serializer for file information response.
    """
    key = serializers.CharField()
    size = serializers.IntegerField()
    content_type = serializers.CharField()
    last_modified = serializers.CharField()
    url = serializers.URLField()
    metadata = serializers.DictField(required=False)
