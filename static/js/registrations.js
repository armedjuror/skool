/**
 * Registrations Page JavaScript
 * Handles pending student registrations and approval workflows
 */

let registrationsDataTable = null;
let currentStatus = 'PENDING';

$(document).ready(function() {
    Registrations.init();
});

const Registrations = {
    init: function() {
        this.loadFilterOptions();
        this.loadStatusCounts();
        this.initializeDataTable();
        this.setupFilterForm();
        this.setupTabs();
        this.setupModals();
    },

    /**
     * Load filter dropdown options
     */
    loadFilterOptions: async function() {
        try {
            // Load branches
            const branchesResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.BRANCHES),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const branches = branchesResponse.results || branchesResponse.data || [];
            branches.forEach(branch => {
                $('#branchFilter, #approveBranch').append(`<option value="${branch.id}">${branch.name}</option>`);
            });

            // Load classes
            const classesResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.CLASSES),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const classes = classesResponse.results || classesResponse.data || [];
            classes.forEach(cls => {
                $('#classFilter, #approveClass').append(`<option value="${cls.id}">${cls.name}</option>`);
            });

            // Load divisions
            const divisionsResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.DIVISIONS),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const divisions = divisionsResponse.results || divisionsResponse.data || [];
            divisions.forEach(div => {
                $('#approveDivision').append(`<option value="${div.id}">${div.name}</option>`);
            });

        } catch (error) {
            console.error('Failed to load filter options:', error);
        }
    },

    /**
     * Load status counts for badges
     */
    loadStatusCounts: async function() {
        try {
            const statuses = ['PENDING', 'INFO_REQUESTED', 'APPROVED', 'REJECTED'];

            for (const status of statuses) {
                const response = await $.ajax({
                    url: API_CONFIG.getUrlWithQuery(API_CONFIG.ENDPOINTS.PENDING.STUDENTS.LIST, { status }),
                    method: 'GET',
                    headers: API_CONFIG.getHeaders()
                });

                const count = response.count || 0;
                $(`#${status.toLowerCase().replace('_', '')}Badge, #${status.toLowerCase()}Badge`).text(count);

                // Update specific badge IDs
                if (status === 'PENDING') $('#pendingBadge').text(count);
                if (status === 'INFO_REQUESTED') $('#infoRequestedBadge').text(count);
                if (status === 'APPROVED') $('#approvedBadge').text(count);
                if (status === 'REJECTED') $('#rejectedBadge').text(count);
            }
        } catch (error) {
            console.error('Failed to load status counts:', error);
        }
    },

    /**
     * Initialize data table
     */
    initializeDataTable: function() {
        registrationsDataTable = new DataTable({
            container: '#registrationsTable',
            title: 'Pending Registrations',
            apiUrl: API_CONFIG.ENDPOINTS.PENDING.STUDENTS.LIST,
            columns: [
                {
                    key: 'photo',
                    label: 'Photo',
                    sortable: false,
                    render: (row) => {
                        if (row.photo) {
                            return `<img src="${row.photo}" class="avatar-sm" alt="${row.student_name}">`;
                        }
                        return `<div class="avatar-sm bg-secondary text-white d-flex align-items-center justify-content-center rounded-circle">
                                    <i class="fas fa-user"></i>
                                </div>`;
                    }
                },
                {
                    key: 'student_name',
                    label: 'Student Name',
                    sortable: true
                },
                {
                    key: 'parent_mobile',
                    label: 'Parent Mobile',
                    sortable: false
                },
                {
                    key: 'email',
                    label: 'Email',
                    sortable: false
                },
                {
                    key: 'class_name',
                    label: 'Class Requested',
                    sortable: false,
                    render: (row) => row.class_to_admit_name || row.class_name || '-'
                },
                {
                    key: 'branch_name',
                    label: 'Branch',
                    sortable: false,
                    render: (row) => row.interested_branch_name || row.branch_name || '-'
                },
                {
                    key: 'submission_date',
                    label: 'Submitted',
                    sortable: true,
                    render: (row) => Utils.formatDate(row.submission_date)
                },
                {
                    key: 'status',
                    label: 'Status',
                    sortable: true,
                    render: (row) => {
                        const statusClasses = {
                            'PENDING': 'warning',
                            'INFO_REQUESTED': 'info',
                            'APPROVED': 'success',
                            'REJECTED': 'danger'
                        };
                        return `<span class="badge bg-${statusClasses[row.status] || 'secondary'}">${row.status_display || row.status}</span>`;
                    }
                },
                {
                    key: 'actions',
                    label: 'Actions',
                    sortable: false,
                    render: (row) => {
                        let actions = `
                            <div class="action-buttons">
                                <button class="btn-action" onclick="Registrations.viewRegistration('${row.id}')" title="View Details">
                                    <i class="fas fa-eye"></i>
                                </button>`;

                        if (row.status === 'PENDING' || row.status === 'INFO_REQUESTED') {
                            actions += `
                                <button class="btn-action success" onclick="Registrations.showApproveModal('${row.id}', '${row.student_name}')" title="Approve">
                                    <i class="fas fa-check"></i>
                                </button>
                                <button class="btn-action info" onclick="Registrations.showRequestInfoModal('${row.id}', '${row.student_name}')" title="Request Info">
                                    <i class="fas fa-question"></i>
                                </button>
                                <button class="btn-action danger" onclick="Registrations.showRejectModal('${row.id}', '${row.student_name}')" title="Reject">
                                    <i class="fas fa-times"></i>
                                </button>`;
                        }

                        actions += '</div>';
                        return actions;
                    }
                }
            ],
            actions: [
                {
                    name: 'refresh',
                    label: 'Refresh',
                    icon: 'fas fa-sync-alt',
                    class: 'btn-outline-primary',
                    onClick: () => Registrations.refresh()
                }
            ],
            onRowClick: (row) => Registrations.viewRegistration(row.id)
        });

        // Set initial status filter
        registrationsDataTable.setFilters({ status: 'PENDING' });
    },

    /**
     * Setup filter form
     */
    setupFilterForm: function() {
        $('#registrationFilterForm').on('submit', function(e) {
            e.preventDefault();
            const filters = Utils.serializeForm($(this));
            filters.status = currentStatus;
            registrationsDataTable.setFilters(filters);
        });

        $('#clearFilters').on('click', function() {
            $('#registrationFilterForm')[0].reset();
            registrationsDataTable.setFilters({ status: currentStatus });
        });
    },

    /**
     * Setup status tabs
     */
    setupTabs: function() {
        $('#registrationTabs .nav-link').on('click', function(e) {
            e.preventDefault();
            $('#registrationTabs .nav-link').removeClass('active');
            $(this).addClass('active');

            currentStatus = $(this).data('status');
            const filters = Utils.serializeForm($('#registrationFilterForm'));
            filters.status = currentStatus;
            registrationsDataTable.setFilters(filters);
        });
    },

    /**
     * Setup modal forms
     */
    setupModals: function() {
        // Approve form
        $('#approveForm').on('submit', async function(e) {
            e.preventDefault();
            const registrationId = $('#approveRegistrationId').val();
            const formData = Utils.serializeForm($(this));

            await Registrations.approveRegistration(registrationId, formData);
        });

        // Reject form
        $('#rejectForm').on('submit', async function(e) {
            e.preventDefault();
            const registrationId = $('#rejectRegistrationId').val();
            const formData = Utils.serializeForm($(this));

            await Registrations.rejectRegistration(registrationId, formData);
        });

        // Request info form
        $('#requestInfoForm').on('submit', async function(e) {
            e.preventDefault();
            const registrationId = $('#requestInfoRegistrationId').val();
            const formData = Utils.serializeForm($(this));

            await Registrations.requestInfo(registrationId, formData);
        });
    },

    /**
     * View registration details
     */
    viewRegistration: async function(registrationId) {
        Utils.showLoader();

        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.PENDING.STUDENTS.DETAIL, { id: registrationId }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const reg = response.data || response;

            const modalBody = `
                <div class="row">
                    <div class="col-md-3 text-center mb-3">
                        ${reg.photo
                            ? `<img src="${reg.photo}" class="img-fluid rounded" alt="${reg.student_name}">`
                            : `<div class="bg-secondary text-white d-flex align-items-center justify-content-center rounded" style="height: 150px;">
                                   <i class="fas fa-user fa-3x"></i>
                               </div>`
                        }
                        <div class="mt-2">
                            <span class="badge bg-${this.getStatusClass(reg.status)}">${reg.status_display || reg.status}</span>
                        </div>
                    </div>
                    <div class="col-md-9">
                        <div class="detail-group">
                            <h6 class="detail-group-title">Personal Information</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Name:</strong> ${reg.student_name}</p>
                                    <p><strong>Gender:</strong> ${reg.gender}</p>
                                    <p><strong>Date of Birth:</strong> ${Utils.formatDate(reg.dob)}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>ID Type:</strong> ${reg.id_card_type}</p>
                                    <p><strong>ID Number:</strong> ${reg.id_card_number}</p>
                                    <p><strong>Study Type:</strong> ${reg.study_type}</p>
                                </div>
                            </div>
                        </div>

                        <div class="detail-group mt-3">
                            <h6 class="detail-group-title">Family Details</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Father's Name:</strong> ${reg.father_name}</p>
                                    <p><strong>Mother's Name:</strong> ${reg.mother_name}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Parent Mobile:</strong> ${reg.parent_mobile}</p>
                                    <p><strong>Email:</strong> ${reg.email}</p>
                                </div>
                            </div>
                        </div>

                        <div class="detail-group mt-3">
                            <h6 class="detail-group-title">Academic Preference</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Interested Branch:</strong> ${reg.interested_branch_name || '-'}</p>
                                    <p><strong>Class to Admit:</strong> ${reg.class_to_admit_name || '-'}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Previous Madrasa:</strong> ${reg.previous_madrasa || '-'}</p>
                                    <p><strong>TC Number:</strong> ${reg.tc_number || '-'}</p>
                                </div>
                            </div>
                        </div>

                        ${reg.qatar_address && Object.keys(reg.qatar_address).length > 0 ? `
                        <div class="detail-group mt-3">
                            <h6 class="detail-group-title">Qatar Address</h6>
                            <p>${reg.qatar_address.place || ''}, ${reg.qatar_address.landmark || ''}</p>
                            <p>Building: ${reg.qatar_address.building_no || ''}, Street: ${reg.qatar_address.street_no || ''}, Zone: ${reg.qatar_address.zone_no || ''}</p>
                        </div>
                        ` : ''}

                        ${reg.info_request_message ? `
                        <div class="alert alert-info mt-3">
                            <h6><i class="fas fa-info-circle"></i> Information Requested</h6>
                            <p class="mb-0">${reg.info_request_message}</p>
                        </div>
                        ` : ''}

                        ${reg.rejection_reason ? `
                        <div class="alert alert-danger mt-3">
                            <h6><i class="fas fa-times-circle"></i> Rejection Reason</h6>
                            <p class="mb-0">${reg.rejection_reason}</p>
                        </div>
                        ` : ''}

                        <div class="detail-group mt-3">
                            <h6 class="detail-group-title">Submission Details</h6>
                            <p><strong>Submitted:</strong> ${Utils.formatDateTime(reg.submission_date)}</p>
                            ${reg.reviewed_by_name ? `<p><strong>Reviewed By:</strong> ${reg.reviewed_by_name} on ${Utils.formatDateTime(reg.reviewed_at)}</p>` : ''}
                        </div>
                    </div>
                </div>
            `;

            $('#registrationDetailBody').html(modalBody);

            // Setup footer buttons based on status
            let footerButtons = '';
            if (reg.status === 'PENDING' || reg.status === 'INFO_REQUESTED') {
                footerButtons = `
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-info" onclick="Registrations.showRequestInfoModal('${reg.id}', '${reg.student_name}')">
                        <i class="fas fa-question"></i> Request Info
                    </button>
                    <button type="button" class="btn btn-danger" onclick="Registrations.showRejectModal('${reg.id}', '${reg.student_name}')">
                        <i class="fas fa-times"></i> Reject
                    </button>
                    <button type="button" class="btn btn-success" onclick="Registrations.showApproveModal('${reg.id}', '${reg.student_name}')">
                        <i class="fas fa-check"></i> Approve
                    </button>
                `;
            } else {
                footerButtons = `<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>`;
            }
            $('#registrationDetailFooter').html(footerButtons);

            const modal = new bootstrap.Modal('#registrationDetailModal');
            modal.show();

        } catch (error) {
            console.error('Failed to load registration details:', error);
            Utils.showToast('Failed to load registration details', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Show approve modal
     */
    showApproveModal: function(registrationId, studentName) {
        // Close detail modal if open
        const detailModal = bootstrap.Modal.getInstance('#registrationDetailModal');
        if (detailModal) detailModal.hide();

        $('#approveRegistrationId').val(registrationId);
        $('#approveStudentName').val(studentName);

        const modal = new bootstrap.Modal('#approveModal');
        modal.show();
    },

    /**
     * Show reject modal
     */
    showRejectModal: function(registrationId, studentName) {
        const detailModal = bootstrap.Modal.getInstance('#registrationDetailModal');
        if (detailModal) detailModal.hide();

        $('#rejectRegistrationId').val(registrationId);
        $('#rejectStudentName').val(studentName);
        $('#rejectionReason').val('');

        const modal = new bootstrap.Modal('#rejectModal');
        modal.show();
    },

    /**
     * Show request info modal
     */
    showRequestInfoModal: function(registrationId, studentName) {
        const detailModal = bootstrap.Modal.getInstance('#registrationDetailModal');
        if (detailModal) detailModal.hide();

        $('#requestInfoRegistrationId').val(registrationId);
        $('#requestInfoStudentName').val(studentName);
        $('#infoRequestMessage').val('');

        const modal = new bootstrap.Modal('#requestInfoModal');
        modal.show();
    },

    /**
     * Approve registration
     */
    approveRegistration: async function(registrationId, formData) {
        Utils.showLoader();

        try {
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.PENDING.STUDENTS.APPROVE, { id: registrationId }),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(formData)
            });

            Utils.showToast('Registration approved successfully', 'success');
            bootstrap.Modal.getInstance('#approveModal').hide();
            this.refresh();

        } catch (error) {
            console.error('Failed to approve registration:', error);
            const message = error.responseJSON?.message || 'Failed to approve registration';
            Utils.showToast(message, 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Reject registration
     */
    rejectRegistration: async function(registrationId, formData) {
        Utils.showLoader();

        try {
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.PENDING.STUDENTS.REJECT, { id: registrationId }),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(formData)
            });

            Utils.showToast('Registration rejected', 'success');
            bootstrap.Modal.getInstance('#rejectModal').hide();
            this.refresh();

        } catch (error) {
            console.error('Failed to reject registration:', error);
            const message = error.responseJSON?.message || 'Failed to reject registration';
            Utils.showToast(message, 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Request additional info
     */
    requestInfo: async function(registrationId, formData) {
        Utils.showLoader();

        try {
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.PENDING.STUDENTS.REQUEST_INFO, { id: registrationId }),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(formData)
            });

            Utils.showToast('Information request sent', 'success');
            bootstrap.Modal.getInstance('#requestInfoModal').hide();
            this.refresh();

        } catch (error) {
            console.error('Failed to send info request:', error);
            const message = error.responseJSON?.message || 'Failed to send request';
            Utils.showToast(message, 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Get status class for badge
     */
    getStatusClass: function(status) {
        const classes = {
            'PENDING': 'warning',
            'INFO_REQUESTED': 'info',
            'APPROVED': 'success',
            'REJECTED': 'danger'
        };
        return classes[status] || 'secondary';
    },

    /**
     * Refresh table and counts
     */
    refresh: function() {
        registrationsDataTable.refresh();
        this.loadStatusCounts();
    }
};