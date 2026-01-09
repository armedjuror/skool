/**
 * Utility Functions
 * Common helper functions used throughout the application
 */

const Utils = {
    /**
     * Show global loader
     */
    showLoader: function() {
        $('#globalLoader').addClass('active');
    },

    /**
     * Hide global loader
     */
    hideLoader: function() {
        $('#globalLoader').removeClass('active');
    },

    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - Type: success, error, warning, info
     * @param {number} duration - Duration in milliseconds (default: 3000)
     */
    showToast: function(message, type = 'info', duration = 3000) {
        const toastId = 'toast_' + Date.now();
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        const titleMap = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Information'
        };

        const toastHtml = `
            <div id="${toastId}" class="toast ${type}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas ${iconMap[type]} me-2"></i>
                    <strong class="me-auto">${titleMap[type]}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        $('#toastContainer').append(toastHtml);

        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: duration
        });

        toast.show();

        // Remove from DOM after hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            $(this).remove();
        });
    },

    /**
     * Format date to readable format
     * @param {string} dateString - ISO date string
     * @param {boolean} includeTime - Include time in format
     */
    formatDate: function(dateString, includeTime = false) {
        if (!dateString) return '-';

        const date = new Date(dateString);
        const options = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };

        if (includeTime) {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }

        return date.toLocaleDateString('en-US', options);
    },

    /**
     * Format currency
     * @param {number} amount - Amount to format
     * @param {string} currency - Currency code (default: QAR)
     */
    formatCurrency: function(amount, currency = 'QAR') {
        if (amount === null || amount === undefined) return '-';
        return `${currency} ${parseFloat(amount).toFixed(2)}`;
    },

    /**
     * Debounce function
     * @param {function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     */
    debounce: function(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Validate email format
     * @param {string} email - Email to validate
     */
    isValidEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * Validate phone number (digits only)
     * @param {string} phone - Phone number to validate
     */
    isValidPhone: function(phone) {
        const re = /^\d{8,15}$/;
        return re.test(phone);
    },

    /**
     * Get query parameter from URL
     * @param {string} param - Parameter name
     */
    getQueryParam: function(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    },

    /**
     * Update URL without reloading page
     * @param {string} url - New URL
     */
    updateUrl: function(url) {
        window.history.pushState({}, '', url);
    },

    /**
     * Serialize form data to JSON
     * @param {jQuery} $form - Form element
     */
    serializeForm: function($form) {
        const formData = {};
        $form.serializeArray().forEach(item => {
            if (formData[item.name]) {
                if (!Array.isArray(formData[item.name])) {
                    formData[item.name] = [formData[item.name]];
                }
                formData[item.name].push(item.value);
            } else {
                formData[item.name] = item.value;
            }
        });
        return formData;
    },

    /**
     * Reset form and clear validation
     * @param {jQuery} $form - Form element
     */
    resetForm: function($form) {
        $form[0].reset();
        $form.find('.is-invalid').removeClass('is-invalid');
        $form.find('.invalid-feedback').remove();
    },

    /**
     * Display form validation errors
     * @param {jQuery} $form - Form element
     * @param {object} errors - Error object from API
     */
    showFormErrors: function($form, errors) {
        // Clear existing errors
        $form.find('.is-invalid').removeClass('is-invalid');
        $form.find('.invalid-feedback').remove();

        // Add new errors
        Object.keys(errors).forEach(fieldName => {
            const $field = $form.find(`[name="${fieldName}"]`);
            const errorMessage = Array.isArray(errors[fieldName])
                ? errors[fieldName][0]
                : errors[fieldName];

            if ($field.length) {
                $field.addClass('is-invalid');
                $field.after(`<div class="invalid-feedback d-block">${errorMessage}</div>`);
            }
        });
    },

    /**
     * Confirm dialog
     * @param {string} message - Confirmation message
     * @param {function} onConfirm - Callback on confirmation
     * @param {function} onCancel - Callback on cancel
     */
    confirm: function(message, onConfirm, onCancel = null) {
        Modal.show({
            title: 'Confirm Action',
            body: `<p>${message}</p>`,
            buttons: [
                {
                    label: 'Cancel',
                    class: 'btn-secondary',
                    onClick: function() {
                        Modal.hide();
                        if (onCancel) onCancel();
                    }
                },
                {
                    label: 'Confirm',
                    class: 'btn-primary',
                    onClick: function() {
                        Modal.hide();
                        onConfirm();
                    }
                }
            ]
        });
    },

    /**
     * Download file from blob
     * @param {Blob} blob - File blob
     * @param {string} filename - File name
     */
    downloadFile: function(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    },

    /**
     * Export table to Excel
     * @param {string} tableId - Table element ID
     * @param {string} filename - Export filename
     */
    exportTableToExcel: function(tableId, filename = 'export.xlsx') {
        // This would integrate with a library like SheetJS
        // Placeholder for actual implementation
        Utils.showToast('Export functionality will be implemented', 'info');
    },

    /**
     * Truncate text
     * @param {string} text - Text to truncate
     * @param {number} length - Maximum length
     */
    truncate: function(text, length = 50) {
        if (!text) return '';
        return text.length > length ? text.substring(0, length) + '...' : text;
    },

    /**
     * Generate random ID
     */
    generateId: function() {
        return 'id_' + Math.random().toString(36).substr(2, 9);
    },

    /**
     * Check if user has permission
     * @param {string} permission - Permission to check
     */
    hasPermission: function(permission) {
        const userRole = localStorage.getItem('user_role');
        const permissions = {
            admin: ['all'],
            head_teacher: ['view_students', 'manage_students', 'view_staff', 'manage_fees', 'view_attendance', 'mark_attendance'],
            teacher: ['view_students', 'view_attendance', 'mark_attendance']
        };

        return permissions[userRole] &&
               (permissions[userRole].includes('all') || permissions[userRole].includes(permission));
    },

    /**
     * Storage helpers
     */
    storage: {
        set: function(key, value) {
            localStorage.setItem(key, JSON.stringify(value));
        },
        get: function(key) {
            const item = localStorage.getItem(key);
            try {
                return JSON.parse(item);
            } catch (e) {
                return item;
            }
        },
        remove: function(key) {
            localStorage.removeItem(key);
        },
        clear: function() {
            localStorage.clear();
        }
    },

    /**
     * File upload preview
     * @param {File} file - File object
     * @param {jQuery} $preview - Preview element
     */
    previewImage: function(file, $preview) {
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                $preview.html(`<img src="${e.target.result}" alt="Preview" class="img-fluid rounded">`);
            };
            reader.readAsDataURL(file);
        }
    },

    /**
     * Calculate age from date of birth
     * @param {string} dob - Date of birth (YYYY-MM-DD)
     */
    calculateAge: function(dob) {
        if (!dob) return 0;
        const today = new Date();
        const birthDate = new Date(dob);
        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();

        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }

        return age;
    },

    /**
     * Format number with commas
     * @param {number} num - Number to format
     * @param {number} decimals - Decimal places (default: 2)
     */
    formatNumber: function(num, decimals = 2) {
        if (num === null || num === undefined || isNaN(num)) return '0';
        return parseFloat(num).toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    },

    /**
     * Format date and time
     * @param {string} dateString - ISO date string
     */
    formatDateTime: function(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Get org code from URL
     */
    getOrgCode: function() {
        const pathParts = window.location.pathname.split('/');
        return pathParts[1] || '';
    }
};

// Auto-hide loader on page load
$(document).ready(function() {
    Utils.hideLoader();
});