/**
 * Reports Page JavaScript
 * Handles various report generation and export
 */

let currentReport = null;
let reportData = null;

$(document).ready(function() {
    Reports.init();
});

const Reports = {
    init: function() {
        this.loadFilterOptions();
        this.setupForms();
    },

    /**
     * Load filter options for all reports
     */
    loadFilterOptions: async function() {
        try {
            // Load branches
            const branchesResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.BRANCHES),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const branches = branchesResponse.results || [];
            const branchSelects = $('#attBranch, #leaveBranch, #feedueBranch, #collectionBranch, #studentBranch, #staffBranch');
            branches.forEach(branch => {
                branchSelects.each(function() {
                    $(this).append(`<option value="${branch.id}">${branch.name}</option>`);
                });
            });

            // Load classes
            const classesResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.CLASSES),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const classes = classesResponse.results || [];
            const classSelects = $('#feedueClass, #studentClass');
            classes.forEach(cls => {
                classSelects.each(function() {
                    $(this).append(`<option value="${cls.id}">${cls.name}</option>`);
                });
            });

        } catch (error) {
            console.error('Failed to load filter options:', error);
        }
    },

    /**
     * Setup form handlers
     */
    setupForms: function() {
        $('#attendanceReportForm').on('submit', function(e) {
            e.preventDefault();
            Reports.generateAttendanceReport();
        });

        $('#leaveReportForm').on('submit', function(e) {
            e.preventDefault();
            Reports.generateLeaveReport();
        });

        $('#feeDueReportForm').on('submit', function(e) {
            e.preventDefault();
            Reports.generateFeeDueReport();
        });

        $('#feeCollectionReportForm').on('submit', function(e) {
            e.preventDefault();
            Reports.generateFeeCollectionReport();
        });

        $('#studentReportForm').on('submit', function(e) {
            e.preventDefault();
            Reports.generateStudentReport();
        });

        $('#staffReportForm').on('submit', function(e) {
            e.preventDefault();
            Reports.generateStaffReport();
        });
    },

    /**
     * Select a report type
     */
    selectReport: function(reportType) {
        currentReport = reportType;

        // Remove active class from all cards
        $('.report-card').removeClass('active');
        $(event.target).closest('.report-card').addClass('active');

        // Hide all report sections
        $('.report-section').hide();
        $('#reportContent').show();

        // Show selected report
        switch(reportType) {
            case 'attendance':
                $('#attendanceReport').show();
                break;
            case 'leave':
                $('#leaveReport').show();
                break;
            case 'fee_due':
                $('#feeDueReport').show();
                break;
            case 'fee_collection':
                $('#feeCollectionReport').show();
                break;
            case 'student':
                $('#studentReport').show();
                break;
            case 'staff':
                $('#staffReport').show();
                break;
        }
    },

    /**
     * Generate Attendance Report
     */
    generateAttendanceReport: async function() {
        Utils.showLoader();

        try {
            const filters = Utils.serializeForm($('#attendanceReportForm'));
            const response = await $.ajax({
                url: API_CONFIG.getUrlWithQuery(API_CONFIG.ENDPOINTS.ATTENDANCE.REPORTS.MONTHLY_REPORT, filters),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            reportData = response.data || response;

            // Generate summary
            const summary = reportData.summary || {};
            let html = `
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card bg-success text-white">
                            <div class="card-body text-center">
                                <h3>${summary.total_present || 0}</h3>
                                <p class="mb-0">Present Days</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-danger text-white">
                            <div class="card-body text-center">
                                <h3>${summary.total_absent || 0}</h3>
                                <p class="mb-0">Absent Days</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-warning text-dark">
                            <div class="card-body text-center">
                                <h3>${summary.total_late || 0}</h3>
                                <p class="mb-0">Late Days</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-info text-white">
                            <div class="card-body text-center">
                                <h3>${summary.attendance_percentage || 0}%</h3>
                                <p class="mb-0">Attendance Rate</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Generate table
            const records = reportData.records || [];
            if (records.length > 0) {
                html += `
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Name</th>
                                <th>ID</th>
                                <th>Branch</th>
                                <th>Present</th>
                                <th>Absent</th>
                                <th>Late</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                records.forEach((record, index) => {
                    html += `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${record.name}</td>
                            <td>${record.id_number || '-'}</td>
                            <td>${record.branch_name || '-'}</td>
                            <td class="text-success">${record.present_days || 0}</td>
                            <td class="text-danger">${record.absent_days || 0}</td>
                            <td class="text-warning">${record.late_days || 0}</td>
                            <td>
                                <div class="progress" style="height: 20px;">
                                    <div class="progress-bar bg-success" style="width: ${record.percentage || 0}%">
                                        ${record.percentage || 0}%
                                    </div>
                                </div>
                            </td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
            } else {
                html += '<p class="text-muted text-center">No records found</p>';
            }

            $('#attendanceReportData').html(html);

        } catch (error) {
            console.error('Failed to generate report:', error);
            Utils.showToast('Failed to generate report', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Generate Leave Report
     */
    generateLeaveReport: async function() {
        Utils.showLoader();

        try {
            const filters = Utils.serializeForm($('#leaveReportForm'));
            const response = await $.ajax({
                url: API_CONFIG.getUrlWithQuery('/api/reports/leave/', filters),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            reportData = response.data || response;

            const summary = reportData.summary || {};
            let html = `
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card bg-primary text-white">
                            <div class="card-body text-center">
                                <h3>${summary.total_requests || 0}</h3>
                                <p class="mb-0">Total Requests</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-success text-white">
                            <div class="card-body text-center">
                                <h3>${summary.approved || 0}</h3>
                                <p class="mb-0">Approved</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-danger text-white">
                            <div class="card-body text-center">
                                <h3>${summary.rejected || 0}</h3>
                                <p class="mb-0">Rejected</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Branch-wise breakdown
            const branchData = reportData.by_branch || [];
            if (branchData.length > 0) {
                html += '<h6 class="mt-4 mb-3">Branch-wise Breakdown</h6>';
                html += `
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Branch</th>
                                <th>Total Requests</th>
                                <th>Approved</th>
                                <th>Rejected</th>
                                <th>Pending</th>
                                <th>Total Days</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                branchData.forEach(branch => {
                    html += `
                        <tr>
                            <td>${branch.name}</td>
                            <td>${branch.total}</td>
                            <td class="text-success">${branch.approved}</td>
                            <td class="text-danger">${branch.rejected}</td>
                            <td class="text-warning">${branch.pending}</td>
                            <td>${branch.total_days}</td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
            }

            $('#leaveReportData').html(html);

        } catch (error) {
            console.error('Failed to generate report:', error);
            Utils.showToast('Failed to generate report', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Generate Fee Due Report
     */
    generateFeeDueReport: async function() {
        Utils.showLoader();

        try {
            const filters = Utils.serializeForm($('#feeDueReportForm'));
            const response = await $.ajax({
                url: API_CONFIG.getUrlWithQuery(API_CONFIG.ENDPOINTS.FEES.REPORTS.DUE_REPORT, filters),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            reportData = response.data || response;

            const summary = reportData.summary || {};
            let html = `
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card bg-danger text-white">
                            <div class="card-body text-center">
                                <h3>QAR ${Utils.formatNumber(summary.total_due || 0)}</h3>
                                <p class="mb-0">Total Due Amount</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-warning text-dark">
                            <div class="card-body text-center">
                                <h3>${summary.students_with_dues || 0}</h3>
                                <p class="mb-0">Students with Dues</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-info text-white">
                            <div class="card-body text-center">
                                <h3>${summary.overdue_count || 0}</h3>
                                <p class="mb-0">Overdue Payments</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            const records = reportData.results || [];
            if (records.length > 0) {
                html += `
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Adm No</th>
                                <th>Student Name</th>
                                <th>Class</th>
                                <th>Branch</th>
                                <th>Fee Type</th>
                                <th>Due Amount</th>
                                <th>Due Date</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                records.forEach((record, index) => {
                    const isOverdue = new Date(record.due_date) < new Date();
                    html += `
                        <tr class="${isOverdue ? 'table-danger' : ''}">
                            <td>${index + 1}</td>
                            <td>${record.admission_number}</td>
                            <td>${record.student_name}</td>
                            <td>${record.class_name || '-'}</td>
                            <td>${record.branch_name || '-'}</td>
                            <td>${record.fee_type_name}</td>
                            <td class="text-danger fw-bold">QAR ${Utils.formatNumber(record.due_amount)}</td>
                            <td>${Utils.formatDate(record.due_date)} ${isOverdue ? '<span class="badge bg-danger">Overdue</span>' : ''}</td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
            } else {
                html += '<p class="text-success text-center"><i class="fas fa-check-circle"></i> No pending dues</p>';
            }

            $('#feeDueReportData').html(html);

        } catch (error) {
            console.error('Failed to generate report:', error);
            Utils.showToast('Failed to generate report', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Generate Fee Collection Report
     */
    generateFeeCollectionReport: async function() {
        Utils.showLoader();

        try {
            const filters = Utils.serializeForm($('#feeCollectionReportForm'));
            const response = await $.ajax({
                url: API_CONFIG.getUrlWithQuery(API_CONFIG.ENDPOINTS.FEES.REPORTS.COLLECTION_REPORT, filters),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            reportData = response.data || response;

            const summary = reportData.summary || {};
            let html = `
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card bg-success text-white">
                            <div class="card-body text-center">
                                <h3>QAR ${Utils.formatNumber(summary.total_collection || 0)}</h3>
                                <p class="mb-0">Total Collection</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-primary text-white">
                            <div class="card-body text-center">
                                <h3>${summary.total_receipts || 0}</h3>
                                <p class="mb-0">Total Receipts</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-info text-white">
                            <div class="card-body text-center">
                                <h3>QAR ${Utils.formatNumber(summary.average_per_receipt || 0)}</h3>
                                <p class="mb-0">Average per Receipt</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Method-wise breakdown
            const methodData = reportData.by_method || [];
            if (methodData.length > 0) {
                html += '<h6 class="mt-4 mb-3">Payment Method Breakdown</h6>';
                html += '<div class="row mb-4">';
                methodData.forEach(method => {
                    html += `
                        <div class="col-md-3">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h5>QAR ${Utils.formatNumber(method.total)}</h5>
                                    <p class="mb-0 text-muted">${method.method}</p>
                                </div>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            const records = reportData.results || [];
            if (records.length > 0) {
                html += `
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Receipt No</th>
                                <th>Date</th>
                                <th>Student</th>
                                <th>Amount</th>
                                <th>Method</th>
                                <th>Collected By</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                records.forEach(record => {
                    html += `
                        <tr>
                            <td>${record.receipt_number}</td>
                            <td>${Utils.formatDate(record.collection_date)}</td>
                            <td>${record.student_name}</td>
                            <td class="text-success fw-bold">QAR ${Utils.formatNumber(record.total_amount)}</td>
                            <td>${record.payment_method}</td>
                            <td>${record.collected_by_name || '-'}</td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
            }

            $('#feeCollectionReportData').html(html);

        } catch (error) {
            console.error('Failed to generate report:', error);
            Utils.showToast('Failed to generate report', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Generate Student Report
     */
    generateStudentReport: async function() {
        Utils.showLoader();

        try {
            const filters = Utils.serializeForm($('#studentReportForm'));
            const response = await $.ajax({
                url: API_CONFIG.getUrlWithQuery(API_CONFIG.ENDPOINTS.STUDENTS.LIST, filters),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            reportData = response;

            const count = response.count || 0;
            let html = `
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card bg-primary text-white">
                            <div class="card-body text-center">
                                <h3>${count}</h3>
                                <p class="mb-0">Total Students</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            const records = response.results || [];
            if (records.length > 0) {
                html += `
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Adm No</th>
                                <th>Name</th>
                                <th>Class</th>
                                <th>Division</th>
                                <th>Branch</th>
                                <th>Parent Mobile</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                records.forEach((record, index) => {
                    html += `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${record.admission_number}</td>
                            <td>${record.name}</td>
                            <td>${record.class_name || '-'}</td>
                            <td>${record.division_name || '-'}</td>
                            <td>${record.branch_name || '-'}</td>
                            <td>${record.parent_mobile || '-'}</td>
                            <td>
                                <span class="badge bg-${record.status === 'ACTIVE' ? 'success' : 'secondary'}">
                                    ${record.status}
                                </span>
                            </td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
            } else {
                html += '<p class="text-muted text-center">No students found</p>';
            }

            $('#studentReportData').html(html);

        } catch (error) {
            console.error('Failed to generate report:', error);
            Utils.showToast('Failed to generate report', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Generate Staff Report
     */
    generateStaffReport: async function() {
        Utils.showLoader();

        try {
            const filters = Utils.serializeForm($('#staffReportForm'));
            const response = await $.ajax({
                url: API_CONFIG.getUrlWithQuery(API_CONFIG.ENDPOINTS.STAFFS.LIST, filters),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            reportData = response;

            const count = response.count || 0;
            let html = `
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card bg-primary text-white">
                            <div class="card-body text-center">
                                <h3>${count}</h3>
                                <p class="mb-0">Total Staff</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            const records = response.results || [];
            if (records.length > 0) {
                html += `
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Staff No</th>
                                <th>Name</th>
                                <th>Role</th>
                                <th>Branch</th>
                                <th>Mobile</th>
                                <th>Category</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                records.forEach((record, index) => {
                    html += `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${record.staff_number}</td>
                            <td>${record.name}</td>
                            <td>${record.user_type_display || record.user_type}</td>
                            <td>${record.branch_name || '-'}</td>
                            <td>${record.mobile || '-'}</td>
                            <td>
                                <span class="badge bg-${record.category === 'PERMANENT' ? 'primary' : 'info'}">
                                    ${record.category}
                                </span>
                            </td>
                            <td>
                                <span class="badge bg-${record.status === 'ACTIVE' ? 'success' : 'secondary'}">
                                    ${record.status}
                                </span>
                            </td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
            } else {
                html += '<p class="text-muted text-center">No staff found</p>';
            }

            $('#staffReportData').html(html);

        } catch (error) {
            console.error('Failed to generate report:', error);
            Utils.showToast('Failed to generate report', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Export report
     */
    exportReport: function(reportType) {
        if (!reportData) {
            Utils.showToast('Please generate a report first', 'warning');
            return;
        }

        // Convert report data to CSV
        let csv = '';
        const records = reportData.results || reportData.records || [];

        if (records.length === 0) {
            Utils.showToast('No data to export', 'warning');
            return;
        }

        // Get headers from first record
        const headers = Object.keys(records[0]);
        csv += headers.join(',') + '\n';

        // Add rows
        records.forEach(record => {
            const values = headers.map(header => {
                let value = record[header] || '';
                // Escape commas and quotes
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    value = '"' + value.replace(/"/g, '""') + '"';
                }
                return value;
            });
            csv += values.join(',') + '\n';
        });

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportType}_report_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        Utils.showToast('Report exported successfully', 'success');
    }
};
