/**
 * API Configuration
 * Centralized API endpoint management
 * Update BASE_URL for production deployment
 */

const API_CONFIG = {
    // Base URL - Update this for production
    BASE_URL: window.location.origin,

    // API Endpoints
    ENDPOINTS: {
        // Authentication
        AUTH: {
            LOGIN: '/api/auth/login/',
            LOGOUT: '/api/auth/logout/',
            REFRESH_TOKEN: '/api/auth/refresh/',
            FORGOT_PASSWORD: '/api/auth/forgot-password/',
            RESET_PASSWORD: '/api/auth/reset-password/',
            CHANGE_PASSWORD: '/api/auth/change-password/',
            GET_USER_INFO: '/api/auth/user/',
        },

        // Student Management
        STUDENTS: {
            LIST: '/api/students/',
            CREATE: '/api/students/create/',
            DETAIL: '/api/students/{id}/',
            UPDATE: '/api/students/{id}/update/',
            DELETE: '/api/students/{id}/delete/',
            SEARCH: '/api/students/search/',
            EXPORT: '/api/students/export/',
            BULK_UPLOAD: '/api/students/bulk-upload/',
        },

        // Student Registration (Public)
        REGISTRATION: {
            STUDENT: {
                SUBMIT: '/api/registration/student/',
                VERIFY: '/api/registration/student/verify/',
            },
            STAFF: {
                SUBMIT: '/api/registration/staff/',
                VERIFY: '/api/registration/staff/verify/',
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
            STAFF: {
                LIST: '/api/pending/staff/',
                DETAIL: '/api/pending/staff/{id}/',
                APPROVE: '/api/pending/staff/{id}/approve/',
                REJECT: '/api/pending/staff/{id}/reject/',
                REQUEST_INFO: '/api/pending/staff/{id}/request-info/',
            },
        },

        // Staff Management
        STAFF: {
            LIST: '/api/staff/',
            CREATE: '/api/staff/create/',
            DETAIL: '/api/staff/{id}/',
            UPDATE: '/api/staff/{id}/update/',
            DELETE: '/api/staff/{id}/delete/',
            SEARCH: '/api/staff/search/',
            EXPORT: '/api/staff/export/',
        },

        // Fee Management
        FEES: {
            CONFIGURATION: {
                MONTHLY: {
                    LIST: '/api/fees/monthly/',
                    CREATE: '/api/fees/monthly/create/',
                    UPDATE: '/api/fees/monthly/{id}/update/',
                    DELETE: '/api/fees/monthly/{id}/delete/',
                },
                ADDITIONAL: {
                    LIST: '/api/fees/additional/',
                    CREATE: '/api/fees/additional/create/',
                    UPDATE: '/api/fees/additional/{id}/update/',
                    DELETE: '/api/fees/additional/{id}/delete/',
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

        // Settings
        SETTINGS: {
            ACADEMIC_YEAR: {
                LIST: '/api/settings/academic-years/',
                CREATE: '/api/settings/academic-years/create/',
                UPDATE: '/api/settings/academic-years/{id}/update/',
                ACTIVATE: '/api/settings/academic-years/{id}/activate/',
            },
            BRANCHES: {
                LIST: '/api/settings/branches/',
                CREATE: '/api/settings/branches/create/',
                UPDATE: '/api/settings/branches/{id}/update/',
                DELETE: '/api/settings/branches/{id}/delete/',
            },
            CLASSES: {
                LIST: '/api/settings/classes/',
                CREATE: '/api/settings/classes/create/',
                UPDATE: '/api/settings/classes/{id}/update/',
                DELETE: '/api/settings/classes/{id}/delete/',
            },
            DIVISIONS: {
                LIST: '/api/settings/divisions/',
                CREATE: '/api/settings/divisions/create/',
                UPDATE: '/api/settings/divisions/{id}/update/',
                DELETE: '/api/settings/divisions/{id}/delete/',
            },
            USERS: {
                LIST: '/api/settings/users/',
                CREATE: '/api/settings/users/create/',
                UPDATE: '/api/settings/users/{id}/update/',
                DELETE: '/api/settings/users/{id}/delete/',
                RESET_PASSWORD: '/api/settings/users/{id}/reset-password/',
            },
            BACKUP: {
                CREATE: '/api/settings/backup/create/',
                LIST: '/api/settings/backup/list/',
                RESTORE: '/api/settings/backup/restore/',
                DOWNLOAD: '/api/settings/backup/{id}/download/',
            },
            AUDIT_LOGS: {
                LIST: '/api/settings/audit-logs/',
                EXPORT: '/api/settings/audit-logs/export/',
            },
        },

        // Dashboard
        DASHBOARD: {
            STATS: '/api/dashboard/stats/',
            RECENT_ACTIVITY: '/api/dashboard/recent-activity/',
            NOTIFICATIONS: '/api/dashboard/notifications/',
        },

        // Utilities
        UTILITIES: {
            STATES: '/api/utilities/states/',
            DISTRICTS: '/api/utilities/districts/{state_id}/',
            UPLOAD_FILE: '/api/utilities/upload/',
        },
    },

    // Request Headers
    getHeaders: function(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        };

        if (includeAuth) {
            const token = localStorage.getItem('auth_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
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
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}