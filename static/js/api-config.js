/**
 * API Configuration
 * Centralized API endpoint management
 * Update BASE_URL for production deployment
 */

const API_CONFIG = {
    // Base URL - Update this for production
    BASE_URL: window.location.origin,

    // API Endpoints - Updated for DRF ViewSet routes
    ENDPOINTS: {
        // Authentication
        AUTH: {
            LOGIN: '/api/auth/login/',
            LOGOUT: '/api/auth/logout/',
            FORGOT_PASSWORD: '/api/auth/forgot-password/',
            RESET_PASSWORD: '/api/auth/reset-password/',
            CHANGE_PASSWORD: '/api/auth/change-password/',
            GET_USER_INFO: '/api/auth/user/',
        },

        // Student Management (ViewSet routes)
        STUDENTS: {
            LIST: '/api/students/',
            CREATE: '/api/students/',
            DETAIL: '/api/students/{id}/',
            UPDATE: '/api/students/{id}/',
            DELETE: '/api/students/{id}/',
            SEARCH: '/api/students/search/',
        },

        // Student Registration (Public)
        REGISTRATION: {
            STUDENT: {
                SUBMIT: '/api/registration/student/submit/',
                VERIFY: '/api/registration/student/verify/',
            },
        },

        // Pending Registrations
        PENDING: {
            STUDENTS: {
                LIST: '/api/pending/students/',
                DETAIL: '/api/pending/students/{id}/',
                APPROVE: '/api/pending/students/{id}/approve/',
                REJECT: '/api/pending/students/{id}/reject/',
                REQUEST_INFO: '/api/pending/students/{id}/request-info/',
            },
        },

        // Staff Management (ViewSet routes)
        STAFFS: {
            LIST: '/api/staffs/',
            CREATE: '/api/staffs/',
            DETAIL: '/api/staffs/{id}/',
            UPDATE: '/api/staffs/{id}/',
            DELETE: '/api/staffs/{id}/',
            SEARCH: '/api/staffs/',
            RESET_PASSWORD: '/api/staffs/{id}/reset-password/',
        },

        // Teachers (alias for staff with teacher role)
        TEACHERS: {
            LIST: '/api/staffs/?user_type=TEACHER',
        },

        // Academic Year Management (singular for backwards compatibility)
        ACADEMIC_YEAR: {
            LIST: '/api/academic-years/',
            CREATE: '/api/academic-years/',
            DETAIL: '/api/academic-years/{id}/',
            UPDATE: '/api/academic-years/{id}/',
            DELETE: '/api/academic-years/{id}/',
            ACTIVATE: '/api/academic-years/{id}/activate/',
        },

        // Also expose as plural
        ACADEMIC_YEARS: {
            LIST: '/api/academic-years/',
            CREATE: '/api/academic-years/',
            DETAIL: '/api/academic-years/{id}/',
            UPDATE: '/api/academic-years/{id}/',
            DELETE: '/api/academic-years/{id}/',
            ACTIVATE: '/api/academic-years/{id}/activate/',
        },

        // Branch Management
        BRANCHES: {
            LIST: '/api/branches/',
            CREATE: '/api/branches/',
            DETAIL: '/api/branches/{id}/',
            UPDATE: '/api/branches/{id}/',
            DELETE: '/api/branches/{id}/',
        },

        // Class Management
        CLASSES: {
            LIST: '/api/classes/',
            CREATE: '/api/classes/',
            DETAIL: '/api/classes/{id}/',
            UPDATE: '/api/classes/{id}/',
            DELETE: '/api/classes/{id}/',
        },

        // Division Management
        DIVISIONS: {
            LIST: '/api/divisions/',
            CREATE: '/api/divisions/',
            DETAIL: '/api/divisions/{id}/',
            UPDATE: '/api/divisions/{id}/',
            DELETE: '/api/divisions/{id}/',
        },

        USERS: {
            LIST: '/api/users/',
            CREATE: '/api/users/',
            DETAIL: '/api/users/{id}/',
            UPDATE: '/api/users/{id}/',
            DELETE: '/api/users/{id}/',
            RESET_PASSWORD: '/api/users/{id}/reset_password/',
        },

        // System Settings Management
        SYSTEM_SETTINGS: {
            LIST: '/api/system-settings/',
            CREATE: '/api/system-settings/',
            DETAIL: '/api/system-settings/{id}/',
            UPDATE: '/api/system-settings/{id}/',
            DELETE: '/api/system-settings/{id}/',
            BY_KEY: '/api/system-settings/by-key/{key}/',
        },

        // System operations (placeholder endpoints)
        SYSTEM: {
            BACKUP: '/api/system/backup/',
            BACKUP_SCHEDULE: '/api/system/backup-schedule/',
            RESTORE: '/api/system/restore/',
            PASSWORD_POLICY: '/api/system/password-policy/',
            SESSION_TIMEOUT: '/api/system/session-timeout/',
            AUDIT_LOGS: '/api/dashboard/recent-activity/',
        },

        // Settings endpoint
        SETTINGS: '/api/system-settings/',

        // Fee Management
        FEES: {
            CONFIGURATION: {
                MONTHLY: {
                    LIST: '/api/fees/monthly/',
                    CREATE: '/api/fees/monthly/',
                    UPDATE: '/api/fees/monthly/{id}/',
                    DELETE: '/api/fees/monthly/{id}/',
                },
                ADDITIONAL: {
                    LIST: '/api/fees/additional/',
                    CREATE: '/api/fees/additional/',
                    UPDATE: '/api/fees/additional/{id}/',
                    DELETE: '/api/fees/additional/{id}/',
                },
            },
            COLLECTION: {
                COLLECT: '/api/fees/collect/',
                RECEIPT: '/api/fees/receipt/{id}/',
                PRINT_RECEIPT: '/api/fees/receipt/{id}/print/',
            },
            REPORTS: {
                DUE_REPORT: '/api/fees/reports/due/',
                COLLECTION_REPORT: '/api/fees/reports/collection/',
                FEE_MASTER_REPORT: '/api/fees/reports/fee-master/',
                CLASS_WISE_REPORT: '/api/fees/reports/class-wise/',
            },
            STUDENT: {
                FEE_DETAILS: '/api/fees/student/{id}/',
                FEE_HISTORY: '/api/fees/student/{id}/history/',
            },
        },

        // Attendance Management
        ATTENDANCE: {
            STUDENT: {
                MARK: '/api/attendance/student/mark/',
                LIST: '/api/attendance/student/list/',
                SUMMARY: '/api/attendance/student/summary/',
            },
            STAFF: {
                MARK: '/api/attendance/staff/mark/',
                LIST: '/api/attendance/staff/list/',
                SUMMARY: '/api/attendance/staff/summary/',
            },
            REPORTS: {
                DAILY_SUMMARY: '/api/attendance/reports/daily/',
                MONTHLY_REPORT: '/api/attendance/reports/monthly/',
                DEFAULTER_REPORT: '/api/attendance/reports/defaulters/',
            },
        },

        // Reports
        REPORTS: {
            STUDENT_LIST: '/api/reports/students/',
            STAFF_LIST: '/api/reports/staff/',
            FEE_SUMMARY: '/api/reports/fees/',
            ATTENDANCE_SUMMARY: '/api/reports/attendance/',
            CUSTOM: '/api/reports/custom/',
        },

        // Dashboard
        DASHBOARD: {
            STATS: '/api/dashboard/stats/',
            RECENT_ACTIVITY: '/api/dashboard/recent-activity/',
            NOTIFICATIONS: '/api/dashboard/notifications/',
        },

        // Utilities (for dropdowns/selects in forms)
        UTILITIES: {
            BRANCHES: '/api/utilities/branches/',
            CLASSES: '/api/utilities/classes/',
            DIVISIONS: '/api/utilities/divisions/',
        },
    },

    // Get CSRF token from cookie
    getCSRFToken: function() {
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
    },

    // Request Headers
    getHeaders: function(includeAuth = true, isFormData = false) {
        const headers = {
            'X-Requested-With': 'XMLHttpRequest',
        };

        // Don't set Content-Type for FormData (browser will set it with boundary)
        if (!isFormData) {
            headers['Content-Type'] = 'application/json';
        }

        // Add CSRF token
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        // Add Authorization header if authenticated
        if (includeAuth) {
            // Token is stored via Utils.storage.set() which uses JSON.stringify
            // So we need to parse it back
            let token = localStorage.getItem('auth_token');
            if (token) {
                try {
                    token = JSON.parse(token);
                } catch (e) {
                    // Token might be stored as plain string
                }
                // DRF TokenAuthentication uses "Token" prefix
                headers['Authorization'] = `Token ${token}`;
            }
        }

        return headers;
    },

    // Build full URL
    getUrl: function(endpoint, params = {}) {
        let url = this.BASE_URL + endpoint;

        // Replace URL parameters (e.g., {id})
        Object.keys(params).forEach(key => {
            url = url.replace(`{${key}}`, params[key]);
        });

        return url;
    },

    // Build URL with query parameters
    getUrlWithQuery: function(endpoint, queryParams = {}) {
        const url = this.getUrl(endpoint);
        const params = new URLSearchParams(queryParams);
        return params.toString() ? `${url}?${params.toString()}` : url;
    },

    // Helper method for making API requests
    request: async function(endpoint, options = {}) {
        Utils.showLoader()
        const {
            method = 'GET',
            params = {},
            query = {},
            body = null,
            includeAuth = true,
            isFormData = false,
        } = options;

        const url = Object.keys(query).length > 0
            ? this.getUrlWithQuery(this.getUrl(endpoint, params), query)
            : this.getUrl(endpoint, params);

        const fetchOptions = {
            method,
            headers: this.getHeaders(includeAuth, isFormData),
            credentials: 'same-origin',
        };

        if (body && method !== 'GET') {
            fetchOptions.body = isFormData ? body : JSON.stringify(body);
        }

        try {
            const response = await fetch(url, fetchOptions);
            const data = await response.json();

            if (!response.ok) {
                throw {
                    status: response.status,
                    message: data.message || 'Request failed',
                    errors: data.errors || {},
                    data
                };
            }

            return data;
        } catch (error) {
            if (error.status) {
                throw error;
            }
            throw {
                status: 0,
                message: error.message || 'Network error',
                errors: {}
            };
        } finally {
            Utils.hideLoader()
        }
    },

    // Convenience methods for common HTTP verbs
    get: function(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    },

    post: function(endpoint, body, options = {}) {
        return this.request(endpoint, { ...options, method: 'POST', body });
    },

    put: function(endpoint, body, options = {}) {
        return this.request(endpoint, { ...options, method: 'PUT', body });
    },

    patch: function(endpoint, body, options = {}) {
        return this.request(endpoint, { ...options, method: 'PATCH', body });
    },

    delete: function(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    },
};

// Configure jQuery AJAX to include CSRF token and credentials
(function() {
    // Get CSRF token
    function getCookie(name) {
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

    // Check if method requires CSRF
    function csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    // Configure jQuery AJAX defaults
    if (typeof $ !== 'undefined' && $.ajaxSetup) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                // Add CSRF token for unsafe methods
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            },
            xhrFields: {
                withCredentials: true
            }
        });
    }
})();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}