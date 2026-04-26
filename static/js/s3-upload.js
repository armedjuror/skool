/**
 * S3 Upload Utility
 * Handles presigned URL uploads from Django templates
 *
 * Usage:
 *   const uploader = new S3Uploader();
 *
 *   // For authenticated users
 *   const result = await uploader.uploadFile(file, {
 *       fileCategory: 'image',
 *       entityType: 'student',
 *       entityId: 'uuid-here'
 *   });
 *
 *   // For public forms (registration)
 *   const result = await uploader.uploadFilePublic(file, orgCode, {
 *       fileCategory: 'image'
 *   });
 */

class S3Uploader {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || (typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : window.location.origin);
        this.maxRetries = options.maxRetries || 3;
        this.onProgress = options.onProgress || null;
    }

    /**
     * Get CSRF token from cookie
     */
    getCSRFToken() {
        if (typeof API_CONFIG !== 'undefined' && API_CONFIG.getCSRFToken) {
            return API_CONFIG.getCSRFToken();
        }
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Get presigned URL for authenticated uploads
     */
    async getPresignedUrl(filename, contentType, options = {}) {
        const endpoint = typeof API_CONFIG !== 'undefined'
            ? API_CONFIG.ENDPOINTS.UPLOADS.PRESIGNED_URL
            : '/api/uploads/presigned-url/';

        const response = await API_CONFIG.post(endpoint, {
            filename: filename,
            content_type: contentType,
            file_category: options.fileCategory || 'image',
            file_size: options.fileSize,
            entity_type: options.entityType,
            entity_id: options.entityId,
            metadata: options.metadata
        });

        if (!response.success) {
            throw new Error(response.message || 'Failed to get presigned URL');
        }

        return response.data;
    }

    /**
     * Get presigned URL for public uploads (e.g., registration forms)
     */
    async getPresignedUrlPublic(filename, contentType, orgCode, options = {}) {
        const endpoint = typeof API_CONFIG !== 'undefined'
            ? API_CONFIG.ENDPOINTS.UPLOADS.PUBLIC_PRESIGNED_URL
            : '/api/uploads/public-presigned-url/';

        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                org_code: orgCode,
                filename: filename,
                content_type: contentType,
                file_category: options.fileCategory || 'image',
                file_size: options.fileSize
            })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || 'Failed to get presigned URL');
        }

        return data.data;
    }

    /**
     * Upload file directly to S3 using presigned POST
     */
    async uploadToS3(file, presignedData, onProgress = null) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();

            // Add all the presigned fields first (order matters for S3)
            Object.keys(presignedData.fields).forEach(key => {
                formData.append(key, presignedData.fields[key]);
            });

            // Add the file last
            formData.append('file', file);

            const xhr = new XMLHttpRequest();

            // Track upload progress
            if (onProgress || this.onProgress) {
                xhr.upload.onprogress = (event) => {
                    if (event.lengthComputable) {
                        const percentComplete = Math.round((event.loaded / event.total) * 100);
                        const progressCallback = onProgress || this.onProgress;
                        if (progressCallback) {
                            progressCallback({
                                loaded: event.loaded,
                                total: event.total,
                                percent: percentComplete
                            });
                        }
                    }
                };
            }

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve({
                        success: true,
                        s3Key: presignedData.s3_key
                    });
                } else {
                    reject(new Error(`Upload failed with status ${xhr.status}`));
                }
            };

            xhr.onerror = () => {
                reject(new Error('Upload failed due to network error'));
            };

            xhr.open('POST', presignedData.upload_url);
            xhr.send(formData);
        });
    }

    /**
     * Confirm upload and optionally associate with a model
     */
    async confirmUpload(s3Key, options = {}) {
        const endpoint = typeof API_CONFIG !== 'undefined'
            ? API_CONFIG.ENDPOINTS.UPLOADS.CONFIRM
            : '/api/uploads/confirm/';

        const response = await API_CONFIG.post(endpoint, {
            s3_key: s3Key,
            entity_type: options.entityType,
            entity_id: options.entityId,
            field_name: options.fieldName
        });

        if (!response.success) {
            throw new Error(response.message || 'Failed to confirm upload');
        }

        return response.data;
    }

    /**
     * Complete upload flow for authenticated users
     * Gets presigned URL, uploads to S3, and optionally confirms
     */
    async uploadFile(file, options = {}) {
        const { onProgress, ...presignedOptions } = options;

        // Validate file size (10MB default)
        const maxSize = options.maxSize || 10 * 1024 * 1024;
        if (file.size > maxSize) {
            throw new Error(`File size exceeds maximum allowed (${Math.round(maxSize / 1024 / 1024)}MB)`);
        }

        // Get presigned URL
        const presignedData = await this.getPresignedUrl(
            file.name,
            file.type,
            {
                ...presignedOptions,
                fileSize: file.size
            }
        );

        // Upload to S3
        const uploadResult = await this.uploadToS3(file, presignedData, onProgress);

        // Confirm upload (optional - only if associating with a model)
        if (options.entityType && options.entityId && options.fieldName) {
            const confirmResult = await this.confirmUpload(uploadResult.s3Key, {
                entityType: options.entityType,
                entityId: options.entityId,
                fieldName: options.fieldName
            });
            return confirmResult;
        }

        return {
            success: true,
            s3_key: uploadResult.s3Key
        };
    }

    /**
     * Complete upload flow for public forms (no auth required)
     */
    async uploadFilePublic(file, orgCode, options = {}) {
        const { onProgress, ...presignedOptions } = options;

        // Validate file size (5MB for public uploads)
        const maxSize = options.maxSize || 5 * 1024 * 1024;
        if (file.size > maxSize) {
            throw new Error(`File size exceeds maximum allowed (${Math.round(maxSize / 1024 / 1024)}MB)`);
        }

        // Validate file type (only images for public)
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            throw new Error('Only image files (JPG, PNG, GIF, WEBP) are allowed');
        }

        // Get presigned URL
        const presignedData = await this.getPresignedUrlPublic(
            file.name,
            file.type,
            orgCode,
            {
                ...presignedOptions,
                fileSize: file.size
            }
        );

        // Upload to S3
        const uploadResult = await this.uploadToS3(file, presignedData, onProgress);

        return {
            success: true,
            s3_key: uploadResult.s3Key
        };
    }

    /**
     * Validate file before upload
     */
    validateFile(file, options = {}) {
        const errors = [];

        // Check file size
        const maxSize = options.maxSize || 10 * 1024 * 1024;
        if (file.size > maxSize) {
            errors.push(`File size exceeds maximum (${Math.round(maxSize / 1024 / 1024)}MB)`);
        }

        // Check file type
        const allowedTypes = options.allowedTypes || ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
            errors.push(`File type not allowed. Allowed: ${allowedTypes.join(', ')}`);
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Get file information from S3
     */
    async getFileInfo(s3Key) {
        const endpoint = typeof API_CONFIG !== 'undefined'
            ? API_CONFIG.ENDPOINTS.UPLOADS.INFO
            : '/api/uploads/info/';

        const response = await API_CONFIG.get(`${endpoint}?key=${encodeURIComponent(s3Key)}`);

        if (!response.success) {
            throw new Error(response.message || 'Failed to get file info');
        }

        return response.data;
    }
}

// Create global instance
const s3Uploader = new S3Uploader();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { S3Uploader, s3Uploader };
}
