/**
 * Dashboard Page JavaScript
 */

$(document).ready(function() {
    Dashboard.init();
});

const Dashboard = {
    init: function() {
        this.loadStats();
        this.loadRecentActivities();
        this.loadAttendanceSummary();
        this.loadFeeDueSummary();
        this.filterContentByRole();
    },

    /**
     * Load dashboard statistics
     */
    loadStats: async function() {
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DASHBOARD.STATS),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            // Update stat cards
            $('#totalStudents').text(response.total_students || 0);
            $('#totalStaff').text(response.total_staff || 0);
            $('#pendingRegistrations').text(response.pending_registrations || 0);
            $('#monthlyCollection').text(Utils.formatCurrency(response.monthly_collection || 0));

            // Animate numbers
            this.animateValue('totalStudents', 0, response.total_students || 0, 1000);
            this.animateValue('totalStaff', 0, response.total_staff || 0, 1000);
            this.animateValue('pendingRegistrations', 0, response.pending_registrations || 0, 1000);

        } catch (error) {
            console.error('Failed to load stats:', error);
            Utils.showToast('Failed to load dashboard statistics', 'error');
        }
    },

    /**
     * Load recent activities
     */
    loadRecentActivities: async function() {
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DASHBOARD.RECENT_ACTIVITY),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const activities = response.activities || [];

            if (activities.length === 0) {
                $('#recentActivities').html(`
                    <div class="empty-state">
                        <i class="fas fa-clipboard"></i>
                        <h5>No Recent Activities</h5>
                        <p>Activities will appear here as they occur</p>
                    </div>
                `);
                return;
            }

            let html = '<div class="list-group list-group-flush">';

            activities.forEach(activity => {
                const icon = this.getActivityIcon(activity.type);
                const color = this.getActivityColor(activity.type);

                html += `
                    <div class="list-group-item border-0 px-0">
                        <div class="d-flex align-items-start">
                            <div class="me-3">
                                <div class="rounded-circle bg-${color} bg-opacity-10 p-2" style="width: 40px; height: 40px;">
                                    <i class="fas ${icon} text-${color}"></i>
                                </div>
                            </div>
                            <div class="flex-grow-1">
                                <h6 class="mb-1">${activity.title}</h6>
                                <p class="mb-1 text-muted small">${activity.description}</p>
                                <small class="text-muted">
                                    <i class="far fa-clock me-1"></i>
                                    ${Utils.formatDate(activity.timestamp, true)}
                                </small>
                            </div>
                        </div>
                    </div>
                `;
            });

            html += '</div>';
            $('#recentActivities').html(html);

        } catch (error) {
            console.error('Failed to load recent activities:', error);
            $('#recentActivities').html(`
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h5>Failed to Load</h5>
                    <p>Unable to load recent activities</p>
                </div>
            `);
        }
    },

    /**
     * Load attendance summary
     */
    loadAttendanceSummary: async function() {
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.ATTENDANCE.STUDENT.SUMMARY),
                method: 'GET',
                headers: API_CONFIG.getHeaders(),
                data: { date: new Date().toISOString().split('T')[0] }
            });

            const summary = response.summary || {};
            const total = summary.total || 0;
            const present = summary.present || 0;
            const absent = summary.absent || 0;
            const percentage = total > 0 ? ((present / total) * 100).toFixed(1) : 0;

            const html = `
                <div class="text-center mb-4">
                    <div class="position-relative d-inline-block">
                        <svg width="120" height="120">
                            <circle cx="60" cy="60" r="50" fill="none" stroke="#e9ecef" stroke-width="10"/>
                            <circle cx="60" cy="60" r="50" fill="none" stroke="#5a8f7b" stroke-width="10"
                                    stroke-dasharray="${(percentage / 100) * 314} 314"
                                    stroke-dashoffset="0"
                                    transform="rotate(-90 60 60)"/>
                        </svg>
                        <div class="position-absolute top-50 start-50 translate-middle">
                            <h3 class="mb-0">${percentage}%</h3>
                        </div>
                    </div>
                </div>
                
                <div class="row text-center">
                    <div class="col-4">
                        <h4 class="mb-1">${total}</h4>
                        <small class="text-muted">Total</small>
                    </div>
                    <div class="col-4">
                        <h4 class="mb-1 text-success">${present}</h4>
                        <small class="text-muted">Present</small>
                    </div>
                    <div class="col-4">
                        <h4 class="mb-1 text-danger">${absent}</h4>
                        <small class="text-muted">Absent</small>
                    </div>
                </div>
                
                <div class="mt-3">
                    <a href="/attendance" class="btn btn-outline-primary btn-sm w-100">
                        View Details
                    </a>
                </div>
            `;

            $('#attendanceSummary').html(html);

        } catch (error) {
            console.error('Failed to load attendance summary:', error);
            $('#attendanceSummary').html(`
                <div class="empty-state">
                    <i class="fas fa-calendar-times"></i>
                    <p>No attendance data</p>
                </div>
            `);
        }
    },

    /**
     * Load fee due summary
     */
    loadFeeDueSummary: async function() {
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.REPORTS.DUE_REPORT),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const summary = response.summary || [];

            if (summary.length === 0) {
                $('#feeDueSummary').html(`
                    <div class="empty-state">
                        <i class="fas fa-check-circle"></i>
                        <h5>All Clear!</h5>
                        <p>No pending fee dues</p>
                    </div>
                `);
                return;
            }

            let html = `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Branch</th>
                                <th>Students</th>
                                <th class="text-end">Amount Due</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            summary.forEach(item => {
                html += `
                    <tr>
                        <td><strong>${item.branch_name}</strong></td>
                        <td>${item.student_count}</td>
                        <td class="text-end">
                            <span class="badge badge-danger">
                                ${Utils.formatCurrency(item.total_due)}
                            </span>
                        </td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
                <div class="text-center mt-3">
                    <a href="/fees" class="btn btn-outline-primary btn-sm">
                        View All Dues
                    </a>
                </div>
            `;

            $('#feeDueSummary').html(html);

        } catch (error) {
            console.error('Failed to load fee due summary:', error);
            $('#feeDueSummary').html(`
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Unable to load fee dues</p>
                </div>
            `);
        }
    },

    /**
     * Get icon for activity type
     */
    getActivityIcon: function(type) {
        const icons = {
            'student_registered': 'fa-user-plus',
            'fee_collected': 'fa-money-bill',
            'attendance_marked': 'fa-calendar-check',
            'staff_added': 'fa-user-tie',
            'default': 'fa-info-circle'
        };
        return icons[type] || icons.default;
    },

    /**
     * Get color for activity type
     */
    getActivityColor: function(type) {
        const colors = {
            'student_registered': 'primary',
            'fee_collected': 'success',
            'attendance_marked': 'info',
            'staff_added': 'warning',
            'default': 'secondary'
        };
        return colors[type] || colors.default;
    },

    /**
     * Animate number value
     */
    animateValue: function(id, start, end, duration) {
        const element = document.getElementById(id);
        if (!element) return;

        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;

        const timer = setInterval(function() {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.round(current);
        }, 16);
    },

    /**
     * Filter content based on user role
     */
    filterContentByRole: function() {
        const userRole = Utils.storage.get('user_role');

        if (userRole === 'teacher') {
            $('.admin-only, .head-teacher-only').hide();
        } else if (userRole === 'head_teacher') {
            $('.admin-only').hide();
        }
    }
};