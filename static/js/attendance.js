/**
 * Attendance Module JavaScript
 * Handles attendance marking, calendar management, and leave requests
 */

let studentAttDataTable = null;
let staffAttDataTable = null;
let leaveRequestsDataTable = null;
let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let calendarData = {};
let currentLeaveId = null;
let leaveStatus = 'PENDING';

$(document).ready(function() {
    Attendance.init();
});

const Attendance = {
    init: function() {
        this.loadStats();
        this.loadFilterOptions();
        this.setupMarkAttendanceForm();
        this.setupTabHandlers();
        this.setupLeaveStatusTabs();
        this.setupForms();

        // Set default date to today
        $('#attendanceDate').val(new Date().toISOString().split('T')[0]);
    },

    /**
     * Load attendance statistics
     */
    loadStats: async function() {
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DASHBOARD.STATS),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const attendance = response.data?.attendance?.today || {};
            $('#studentsPresentToday').text(attendance.students_present || 0);
            $('#studentsAbsentToday').text((attendance.students_total || 0) - (attendance.students_present || 0));
            $('#staffPresentToday').text(attendance.staff_present || 0);
            $('#pendingLeaves').text(0); // Will be updated from leave requests API

        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    },

    /**
     * Load filter options
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
            const branchSelects = $('#attendanceBranch, #studentAttBranch, #staffAttBranch, #calendarBranch');
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
            const classSelects = $('#attendanceClass, #studentAttClass');
            classes.forEach(cls => {
                classSelects.each(function() {
                    $(this).append(`<option value="${cls.id}">${cls.name}</option>`);
                });
            });

            // Load divisions
            const divisionsResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.DIVISIONS),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const divisions = divisionsResponse.results || [];
            divisions.forEach(div => {
                $('#attendanceDivision').append(`<option value="${div.id}">${div.name}</option>`);
            });

        } catch (error) {
            console.error('Failed to load filter options:', error);
        }
    },

    /**
     * Setup mark attendance form
     */
    setupMarkAttendanceForm: function() {
        // Toggle class/division fields based on type
        $('#attendanceType').on('change', function() {
            const isStudent = $(this).val() === 'STUDENT';
            $('#classFilterDiv, #divisionFilterDiv').toggle(isStudent);
            $('#attendanceClass, #attendanceDivision').prop('required', isStudent);
        });

        // Form submission
        $('#markAttendanceForm').on('submit', async function(e) {
            e.preventDefault();
            await Attendance.loadAttendanceList();
        });
    },

    /**
     * Load attendance list for marking
     */
    loadAttendanceList: async function() {
        Utils.showLoader();

        try {
            const type = $('#attendanceType').val();
            const date = $('#attendanceDate').val();
            const branch = $('#attendanceBranch').val();

            let url, params = { date, branch };

            if (type === 'STUDENT') {
                params.class = $('#attendanceClass').val();
                params.division = $('#attendanceDivision').val();
                url = API_CONFIG.ENDPOINTS.ATTENDANCE.STUDENT.LIST;
            } else {
                url = API_CONFIG.ENDPOINTS.ATTENDANCE.STAFF.LIST;
            }

            const response = await $.ajax({
                url: API_CONFIG.getUrlWithQuery(url, params),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const records = response.data || response.results || [];
            this.renderAttendanceList(records, type, date);

        } catch (error) {
            console.error('Failed to load attendance list:', error);
            Utils.showToast('Failed to load attendance list', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Render attendance list
     */
    renderAttendanceList: function(records, type, date) {
        if (records.length === 0) {
            $('#attendanceList').html(`
                <div class="text-center text-muted py-5">
                    <i class="fas fa-users fa-3x mb-3"></i>
                    <p>No ${type.toLowerCase()}s found for the selected criteria</p>
                </div>
            `);
            return;
        }

        let html = `
            <div class="d-flex justify-content-between mb-3">
                <div>
                    <button type="button" class="btn btn-success btn-sm me-2" onclick="Attendance.markAll('PRESENT')">
                        <i class="fas fa-check-double"></i> Mark All Present
                    </button>
                    <button type="button" class="btn btn-danger btn-sm" onclick="Attendance.markAll('ABSENT')">
                        <i class="fas fa-times"></i> Mark All Absent
                    </button>
                </div>
                <button type="button" class="btn btn-primary" onclick="Attendance.saveAttendance()">
                    <i class="fas fa-save"></i> Save Attendance
                </button>
            </div>
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Photo</th>
                        <th>${type === 'STUDENT' ? 'Adm No' : 'Staff No'}</th>
                        <th>Name</th>
                        ${type === 'STUDENT' ? '<th>Class</th>' : '<th>Role</th>'}
                        <th class="text-center">Present</th>
                        <th class="text-center">Absent</th>
                        <th class="text-center">Late</th>
                        <th>Remarks</th>
                    </tr>
                </thead>
                <tbody>
        `;

        records.forEach((record, index) => {
            const id = type === 'STUDENT' ? record.student_id || record.id : record.staff_id || record.id;
            const status = record.status || '';

            html += `
                <tr data-id="${id}" data-type="${type}">
                    <td>${index + 1}</td>
                    <td>
                        ${record.photo_url
                            ? `<img src="${record.photo_url}" class="avatar-sm rounded-circle">`
                            : `<div class="avatar-sm bg-secondary text-white d-flex align-items-center justify-content-center rounded-circle">
                                   <i class="fas fa-user"></i>
                               </div>`
                        }
                    </td>
                    <td>${record.admission_number || record.staff_number || '-'}</td>
                    <td>${record.name}</td>
                    <td>${type === 'STUDENT' ? `${record.class_name || ''} ${record.division_name || ''}` : record.user_type_display || record.user_type || ''}</td>
                    <td class="text-center">
                        <input type="radio" class="form-check-input attendance-status" name="status_${id}" value="PRESENT" ${status === 'PRESENT' ? 'checked' : ''}>
                    </td>
                    <td class="text-center">
                        <input type="radio" class="form-check-input attendance-status" name="status_${id}" value="ABSENT" ${status === 'ABSENT' ? 'checked' : ''}>
                    </td>
                    <td class="text-center">
                        <input type="radio" class="form-check-input attendance-status" name="status_${id}" value="LATE" ${status === 'LATE' ? 'checked' : ''}>
                    </td>
                    <td>
                        <input type="text" class="form-control form-control-sm remarks-input" value="${record.remarks || ''}" placeholder="Remarks...">
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        $('#attendanceList').html(html);
    },

    /**
     * Mark all as present/absent
     */
    markAll: function(status) {
        $(`.attendance-status[value="${status}"]`).prop('checked', true);
    },

    /**
     * Save attendance
     */
    saveAttendance: async function() {
        Utils.showLoader();

        try {
            const type = $('#attendanceType').val();
            const date = $('#attendanceDate').val();
            const branch = $('#attendanceBranch').val();
            const records = [];

            $('#attendanceList tbody tr').each(function() {
                const id = $(this).data('id');
                const status = $(`input[name="status_${id}"]:checked`).val();
                const remarks = $(this).find('.remarks-input').val();

                if (status) {
                    records.push({
                        id: id,
                        status: status,
                        remarks: remarks
                    });
                }
            });

            if (records.length === 0) {
                Utils.showToast('Please mark attendance for at least one person', 'warning');
                Utils.hideLoader();
                return;
            }

            const url = type === 'STUDENT'
                ? API_CONFIG.ENDPOINTS.ATTENDANCE.STUDENT.MARK
                : API_CONFIG.ENDPOINTS.ATTENDANCE.STAFF.MARK;

            const data = {
                date: date,
                branch: branch,
                records: records
            };

            if (type === 'STUDENT') {
                data.class_id = $('#attendanceClass').val();
                data.division_id = $('#attendanceDivision').val();
            }

            await $.ajax({
                url: API_CONFIG.getUrl(url),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data)
            });

            Utils.showToast('Attendance saved successfully!', 'success');
            this.loadStats();

        } catch (error) {
            console.error('Failed to save attendance:', error);
            const message = error.responseJSON?.message || 'Failed to save attendance';
            Utils.showToast(message, 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Setup tab handlers
     */
    setupTabHandlers: function() {
        $('a[data-bs-toggle="tab"]').on('shown.bs.tab', (e) => {
            const target = $(e.target).attr('href');

            switch(target) {
                case '#studentAttendance':
                    if (!studentAttDataTable) this.initStudentAttTable();
                    break;
                case '#staffAttendance':
                    if (!staffAttDataTable) this.initStaffAttTable();
                    break;
                case '#workingCalendar':
                    this.renderCalendar();
                    break;
                case '#leaveRequests':
                    if (!leaveRequestsDataTable) this.initLeaveRequestsTable();
                    break;
            }
        });
    },

    /**
     * Initialize student attendance table
     */
    initStudentAttTable: function() {
        studentAttDataTable = new DataTable({
            container: '#studentAttendanceTable',
            title: 'Student Attendance Records',
            apiUrl: API_CONFIG.ENDPOINTS.ATTENDANCE.STUDENT.LIST,
            columns: [
                { key: 'date', label: 'Date', sortable: true, render: (row) => Utils.formatDate(row.date) },
                { key: 'admission_number', label: 'Adm No', sortable: true },
                { key: 'name', label: 'Student Name', sortable: true },
                { key: 'class_name', label: 'Class', sortable: false },
                { key: 'branch_name', label: 'Branch', sortable: false },
                {
                    key: 'status',
                    label: 'Status',
                    sortable: true,
                    render: (row) => {
                        const classes = { 'PRESENT': 'success', 'ABSENT': 'danger', 'LATE': 'warning' };
                        return `<span class="badge bg-${classes[row.status] || 'secondary'}">${row.status}</span>`;
                    }
                },
                { key: 'remarks', label: 'Remarks', sortable: false }
            ],
            actions: [
                {
                    name: 'export',
                    label: 'Export',
                    icon: 'fas fa-download',
                    class: 'btn-outline-primary',
                    onClick: () => Utils.showToast('Export functionality', 'info')
                }
            ]
        });

        studentAttDataTable.loadData();

        // Filter form
        $('#studentAttendanceFilterForm').on('submit', function(e) {
            e.preventDefault();
            studentAttDataTable.setFilters(Utils.serializeForm($(this)));
        });

        $('#clearStudentAttFilters').on('click', function() {
            $('#studentAttendanceFilterForm')[0].reset();
            studentAttDataTable.setFilters({});
        });
    },

    /**
     * Initialize staff attendance table
     */
    initStaffAttTable: function() {
        staffAttDataTable = new DataTable({
            container: '#staffAttendanceTable',
            title: 'Staff Attendance Records',
            apiUrl: API_CONFIG.ENDPOINTS.ATTENDANCE.STAFF.LIST,
            columns: [
                { key: 'date', label: 'Date', sortable: true, render: (row) => Utils.formatDate(row.date) },
                { key: 'staff_number', label: 'Staff No', sortable: true },
                { key: 'name', label: 'Staff Name', sortable: true },
                { key: 'user_type', label: 'Role', sortable: false },
                { key: 'branch_name', label: 'Branch', sortable: false },
                {
                    key: 'status',
                    label: 'Status',
                    sortable: true,
                    render: (row) => {
                        const classes = { 'PRESENT': 'success', 'ABSENT': 'danger', 'LATE': 'warning', 'ON_LEAVE': 'info' };
                        return `<span class="badge bg-${classes[row.status] || 'secondary'}">${row.status}</span>`;
                    }
                },
                { key: 'check_in_time', label: 'Check In', sortable: false },
                { key: 'check_out_time', label: 'Check Out', sortable: false }
            ],
            actions: [
                {
                    name: 'export',
                    label: 'Export',
                    icon: 'fas fa-download',
                    class: 'btn-outline-primary',
                    onClick: () => Utils.showToast('Export functionality', 'info')
                }
            ]
        });

        staffAttDataTable.loadData();

        // Filter form
        $('#staffAttendanceFilterForm').on('submit', function(e) {
            e.preventDefault();
            staffAttDataTable.setFilters(Utils.serializeForm($(this)));
        });

        $('#clearStaffAttFilters').on('click', function() {
            $('#staffAttendanceFilterForm')[0].reset();
            staffAttDataTable.setFilters({});
        });
    },

    /**
     * Calendar Navigation
     */
    previousMonth: function() {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        this.renderCalendar();
    },

    nextMonth: function() {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        this.renderCalendar();
    },

    /**
     * Render calendar
     */
    renderCalendar: async function() {
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

        $('#currentMonthYear').text(`${monthNames[currentMonth]} ${currentYear}`);

        // Load calendar data from API
        const branch = $('#calendarBranch').val();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrlWithQuery('/api/attendance/calendar/', {
                    year: currentYear,
                    month: currentMonth + 1,
                    branch: branch
                }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });
            calendarData = response.data || {};
        } catch (error) {
            calendarData = {};
        }

        let html = '';

        // Header row
        dayNames.forEach(day => {
            html += `<div class="calendar-header">${day}</div>`;
        });

        // Get first day of month and total days
        const firstDay = new Date(currentYear, currentMonth, 1).getDay();
        const totalDays = new Date(currentYear, currentMonth + 1, 0).getDate();
        const today = new Date();

        // Empty cells for days before first day
        for (let i = 0; i < firstDay; i++) {
            html += '<div class="calendar-day"></div>';
        }

        // Days of the month
        for (let day = 1; day <= totalDays; day++) {
            const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayOfWeek = new Date(currentYear, currentMonth, day).getDay();
            const isWeekend = dayOfWeek === 5; // Friday is weekend in Qatar
            const isToday = today.getDate() === day && today.getMonth() === currentMonth && today.getFullYear() === currentYear;

            const dayData = calendarData[dateStr] || {};
            let dayClass = 'working';
            let dayLabel = '';

            if (isWeekend) {
                dayClass = 'weekend';
                dayLabel = 'Weekend';
            }
            if (dayData.is_holiday) {
                dayClass = 'holiday';
                dayLabel = dayData.holiday_reason || 'Holiday';
            }
            if (dayData.is_working_day === true) {
                dayClass = 'working';
                dayLabel = 'Working Day';
            }

            html += `
                <div class="calendar-day ${dayClass} ${isToday ? 'today' : ''}"
                     onclick="Attendance.showHolidayModal('${dateStr}')"
                     title="${dayLabel}">
                    <div class="day-number">${day}</div>
                    ${dayLabel ? `<div class="day-label">${dayLabel}</div>` : ''}
                </div>
            `;
        }

        $('#calendarContainer').html(html);

        // Refresh when branch changes
        $('#calendarBranch').off('change').on('change', () => this.renderCalendar());
    },

    /**
     * Show holiday modal
     */
    showHolidayModal: function(dateStr) {
        $('#holidayDate').val(dateStr);
        $('#holidayDateDisplay').val(Utils.formatDate(dateStr));

        const dayData = calendarData[dateStr] || {};
        $('#holidayReason').val(dayData.holiday_reason || '');
        $('#isWorkingDay').prop('checked', dayData.is_working_day || false);

        const modal = new bootstrap.Modal('#holidayModal');
        modal.show();
    },

    /**
     * Setup leave status tabs
     */
    setupLeaveStatusTabs: function() {
        $('#leaveStatusTabs .nav-link').on('click', function(e) {
            e.preventDefault();
            $('#leaveStatusTabs .nav-link').removeClass('active');
            $(this).addClass('active');
            leaveStatus = $(this).data('status');
            if (leaveRequestsDataTable) {
                leaveRequestsDataTable.setFilters({ status: leaveStatus });
            }
        });
    },

    /**
     * Initialize leave requests table
     */
    initLeaveRequestsTable: function() {
        leaveRequestsDataTable = new DataTable({
            container: '#leaveRequestsTable',
            title: 'Leave Requests',
            apiUrl: '/api/attendance/leave-requests/',
            columns: [
                { key: 'staff_name', label: 'Staff Name', sortable: true },
                { key: 'leave_type', label: 'Type', sortable: true },
                { key: 'from_date', label: 'From', sortable: true, render: (row) => Utils.formatDate(row.from_date) },
                { key: 'to_date', label: 'To', sortable: true, render: (row) => Utils.formatDate(row.to_date) },
                { key: 'days', label: 'Days', sortable: false },
                { key: 'reason', label: 'Reason', sortable: false },
                {
                    key: 'status',
                    label: 'Status',
                    sortable: true,
                    render: (row) => {
                        const classes = { 'PENDING': 'warning', 'APPROVED': 'success', 'REJECTED': 'danger' };
                        return `<span class="badge bg-${classes[row.status] || 'secondary'}">${row.status}</span>`;
                    }
                },
                {
                    key: 'actions',
                    label: 'Actions',
                    sortable: false,
                    render: (row) => {
                        if (row.status === 'PENDING') {
                            return `
                                <button class="btn btn-sm btn-outline-primary" onclick="Attendance.reviewLeave('${row.id}')">
                                    <i class="fas fa-eye"></i> Review
                                </button>
                            `;
                        }
                        return '-';
                    }
                }
            ],
            actions: []
        });

        leaveRequestsDataTable.setFilters({ status: 'PENDING' });
    },

    /**
     * Setup forms
     */
    setupForms: function() {
        // Holiday form
        $('#holidayForm').on('submit', async function(e) {
            e.preventDefault();
            await Attendance.saveHoliday();
        });

        // Leave request form
        $('#leaveRequestForm').on('submit', async function(e) {
            e.preventDefault();
            await Attendance.submitLeaveRequest();
        });
    },

    /**
     * Save holiday
     */
    saveHoliday: async function() {
        Utils.showLoader();

        try {
            const data = {
                date: $('#holidayDate').val(),
                holiday_reason: $('#holidayReason').val(),
                is_working_day: $('#isWorkingDay').is(':checked'),
                branch: $('#calendarBranch').val()
            };

            await $.ajax({
                url: API_CONFIG.getUrl('/api/attendance/calendar/'),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data)
            });

            Utils.showToast('Calendar updated successfully', 'success');
            bootstrap.Modal.getInstance('#holidayModal').hide();
            this.renderCalendar();

        } catch (error) {
            console.error('Failed to save holiday:', error);
            Utils.showToast('Failed to update calendar', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Show leave request modal
     */
    showLeaveRequestModal: function() {
        $('#leaveRequestForm')[0].reset();
        const modal = new bootstrap.Modal('#leaveRequestModal');
        modal.show();
    },

    /**
     * Submit leave request
     */
    submitLeaveRequest: async function() {
        Utils.showLoader();

        try {
            const data = Utils.serializeForm($('#leaveRequestForm'));

            await $.ajax({
                url: API_CONFIG.getUrl('/api/attendance/leave-requests/'),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data)
            });

            Utils.showToast('Leave request submitted successfully', 'success');
            bootstrap.Modal.getInstance('#leaveRequestModal').hide();
            if (leaveRequestsDataTable) leaveRequestsDataTable.refresh();

        } catch (error) {
            console.error('Failed to submit leave request:', error);
            Utils.showToast('Failed to submit leave request', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Review leave request
     */
    reviewLeave: async function(leaveId) {
        Utils.showLoader();
        currentLeaveId = leaveId;

        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(`/api/attendance/leave-requests/${leaveId}/`),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const leave = response.data || response;

            const html = `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Staff:</strong> ${leave.staff_name}</p>
                        <p><strong>Leave Type:</strong> ${leave.leave_type}</p>
                        <p><strong>From:</strong> ${Utils.formatDate(leave.from_date)}</p>
                        <p><strong>To:</strong> ${Utils.formatDate(leave.to_date)}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Days:</strong> ${leave.days}</p>
                        <p><strong>Applied On:</strong> ${Utils.formatDateTime(leave.created_at)}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p><strong>Reason:</strong></p>
                    <p class="bg-light p-2 rounded">${leave.reason}</p>
                </div>
                <div class="mt-3">
                    <label class="form-label">Reviewer Comments</label>
                    <textarea class="form-control" id="reviewerComments" rows="2"></textarea>
                </div>
            `;

            $('#reviewLeaveBody').html(html);

            $('#approveLeaveBtn').off('click').on('click', () => Attendance.processLeave('APPROVED'));
            $('#rejectLeaveBtn').off('click').on('click', () => Attendance.processLeave('REJECTED'));

            const modal = new bootstrap.Modal('#reviewLeaveModal');
            modal.show();

        } catch (error) {
            console.error('Failed to load leave request:', error);
            Utils.showToast('Failed to load leave request', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Process leave request (approve/reject)
     */
    processLeave: async function(status) {
        Utils.showLoader();

        try {
            const data = {
                status: status,
                reviewer_comments: $('#reviewerComments').val()
            };

            await $.ajax({
                url: API_CONFIG.getUrl(`/api/attendance/leave-requests/${currentLeaveId}/review/`),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data)
            });

            Utils.showToast(`Leave request ${status.toLowerCase()}`, 'success');
            bootstrap.Modal.getInstance('#reviewLeaveModal').hide();
            if (leaveRequestsDataTable) leaveRequestsDataTable.refresh();

        } catch (error) {
            console.error('Failed to process leave request:', error);
            Utils.showToast('Failed to process leave request', 'error');
        } finally {
            Utils.hideLoader();
        }
    }
};
