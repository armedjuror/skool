/**
 * Staff Management Page JavaScript
 * Handles staff CRUD operations
 */

let staffDataTable = null;
let currentStaffId = null;

$(document).ready(function() {
    Staff.init();
});

const Staff = {
    init: function() {
        this.loadFilterOptions();
        this.initializeDataTable();
        this.setupFilterForm();
        this.setupStaffForm();
    },

    /**
     * Load filter dropdown options
     */
    loadFilterOptions: async function() {
        try {
            const branchesResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.BRANCHES),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const branches = branchesResponse.results || branchesResponse.data || [];
            branches.forEach(branch => {
                $('#branchFilter, #branch').append(`<option value="${branch.id}">${branch.name}</option>`);
            });

        } catch (error) {
            console.error('Failed to load filter options:', error);
        }
    },

    /**
     * Initialize data table
     */
    initializeDataTable: function() {
        staffDataTable = new DataTable({
            container: '#staffTable',
            title: 'Staff List',
            apiUrl: API_CONFIG.ENDPOINTS.STAFFS.LIST,
            columns: [
                {
                    key: 'photo',
                    label: 'Photo',
                    sortable: false,
                    render: (row) => {
                        if (row.photo_url) {
                            return `<img src="${row.photo_url}" class="avatar-sm" alt="${row.name}">`;
                        }
                        return `<div class="avatar-sm bg-secondary text-white d-flex align-items-center justify-content-center rounded-circle">
                                    <i class="fas fa-user"></i>
                                </div>`;
                    }
                },
                {
                    key: 'staff_number',
                    label: 'Staff No',
                    sortable: true
                },
                {
                    key: 'name',
                    label: 'Name',
                    sortable: true
                },
                {
                    key: 'user_type',
                    label: 'Role',
                    sortable: true,
                    render: (row) => row.user_type_display || row.user_type
                },
                {
                    key: 'branch',
                    label: 'Branch',
                    sortable: true,
                    render: (row) => row.branch_name || '-'
                },
                {
                    key: 'mobile',
                    label: 'Mobile',
                    sortable: false
                },
                {
                    key: 'category',
                    label: 'Category',
                    sortable: true,
                    render: (row) => {
                        const categoryClass = row.category === 'PERMANENT' ? 'primary' : 'info';
                        return `<span class="badge bg-${categoryClass}">${row.category}</span>`;
                    }
                },
                {
                    key: 'status',
                    label: 'Status',
                    sortable: true,
                    render: (row) => {
                        const statusClass = row.status === 'ACTIVE' ? 'success' : 'secondary';
                        return `<span class="badge bg-${statusClass}">${row.status}</span>`;
                    }
                },
                {
                    key: 'actions',
                    label: 'Actions',
                    sortable: false,
                    render: (row) => `
                        <div class="action-buttons">
                            <button class="btn-action" onclick="Staff.viewStaff('${row.id}')" title="View">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn-action" onclick="Staff.editStaff('${row.id}')" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-action danger" onclick="Staff.deleteStaff('${row.id}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `
                }
            ],
            actions: [
                {
                    name: 'export',
                    label: 'Export',
                    icon: 'fas fa-download',
                    class: 'btn-outline-primary',
                    onClick: () => Staff.exportStaff()
                },
                {
                    name: 'add',
                    label: 'Add Staff',
                    icon: 'fas fa-plus',
                    class: 'btn-primary',
                    onClick: () => Staff.showAddModal()
                }
            ],
            onRowClick: (row) => Staff.viewStaff(row.id)
        });

        staffDataTable.loadData();
    },

    /**
     * Setup filter form
     */
    setupFilterForm: function() {
        $('#staffFilterForm').on('submit', function(e) {
            e.preventDefault();
            const filters = Utils.serializeForm($(this));
            staffDataTable.setFilters(filters);
        });

        $('#clearFilters').on('click', function() {
            $('#staffFilterForm')[0].reset();
            staffDataTable.setFilters({});
        });
    },

    /**
     * Setup staff form
     */
    setupStaffForm: function() {
        $('#staffForm').on('submit', async function(e) {
            e.preventDefault();
            await Staff.saveStaff();
        });
    },

    /**
     * Show add staff modal
     */
    showAddModal: function() {
        currentStaffId = null;
        $('#staffModalTitle').text('Add Staff Member');
        $('#staffFormSubmit').html('<i class="fas fa-save"></i> Save Staff');
        $('#staffForm')[0].reset();
        $('#staffId').val('');

        // Switch to first tab
        $('#staffFormTabs a:first').tab('show');

        const modal = new bootstrap.Modal('#staffModal');
        modal.show();
    },

    /**
     * View staff details
     */
    viewStaff: async function(staffId) {
        Utils.showLoader();

        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.STAFFS.DETAIL, { id: staffId }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const staff = response.data || response;
            currentStaffId = staff.id;

            const modalBody = `
                <div class="row">
                    <div class="col-md-3 text-center mb-3">
                        ${staff.photo_url
                            ? `<img src="${staff.photo_url}" class="img-fluid rounded" alt="${staff.name}">`
                            : `<div class="bg-secondary text-white d-flex align-items-center justify-content-center rounded" style="height: 150px;">
                                   <i class="fas fa-user fa-3x"></i>
                               </div>`
                        }
                        <div class="mt-2">
                            <span class="badge bg-${staff.status === 'ACTIVE' ? 'success' : 'secondary'}">${staff.status}</span>
                        </div>
                    </div>
                    <div class="col-md-9">
                        <div class="detail-group">
                            <h6 class="detail-group-title">Personal Information</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Staff Number:</strong> ${staff.staff_number}</p>
                                    <p><strong>Full Name:</strong> ${staff.name}</p>
                                    <p><strong>Email:</strong> ${staff.email}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Gender:</strong> ${staff.gender}</p>
                                    <p><strong>Date of Birth:</strong> ${Utils.formatDate(staff.dob)}</p>
                                    <p><strong>Mobile:</strong> ${staff.mobile}</p>
                                </div>
                            </div>
                        </div>

                        <div class="detail-group mt-3">
                            <h6 class="detail-group-title">Employment Details</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Role:</strong> ${staff.user_type_display || staff.user_type}</p>
                                    <p><strong>Branch:</strong> ${staff.branch_name || '-'}</p>
                                    <p><strong>Category:</strong> ${staff.category}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Monthly Salary:</strong> ${Utils.formatCurrency(staff.monthly_salary)}</p>
                                    <p><strong>Status:</strong> ${staff.status}</p>
                                </div>
                            </div>
                        </div>

                        ${staff.religious_academic_details || staff.academic_details ? `
                        <div class="detail-group mt-3">
                            <h6 class="detail-group-title">Academic Details</h6>
                            ${staff.religious_academic_details ? `<p><strong>Religious:</strong> ${staff.religious_academic_details}</p>` : ''}
                            ${staff.academic_details ? `<p><strong>Academic:</strong> ${staff.academic_details}</p>` : ''}
                            ${staff.previous_madrasa ? `<p><strong>Previous Madrasa:</strong> ${staff.previous_madrasa}</p>` : ''}
                        </div>
                        ` : ''}

                        ${staff.notes ? `
                        <div class="detail-group mt-3">
                            <h6 class="detail-group-title">Notes</h6>
                            <p>${staff.notes}</p>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;

            $('#staffDetailBody').html(modalBody);
            $('#editStaffBtn').off('click').on('click', () => {
                bootstrap.Modal.getInstance('#staffDetailModal').hide();
                Staff.editStaff(staffId);
            });

            const modal = new bootstrap.Modal('#staffDetailModal');
            modal.show();

        } catch (error) {
            console.error('Failed to load staff details:', error);
            Utils.showToast('Failed to load staff details', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Edit staff
     */
    editStaff: async function(staffId) {
        Utils.showLoader();

        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.STAFFS.DETAIL, { id: staffId }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const staff = response.data || response;
            currentStaffId = staff.id;

            $('#staffModalTitle').text('Edit Staff Member');
            $('#staffFormSubmit').html('<i class="fas fa-save"></i> Update Staff');
            $('#staffId').val(staff.id);

            // Populate form fields
            $('#fullName').val(staff.name);
            $('#email').val(staff.email);
            $('#gender').val(staff.gender);
            $('#dob').val(staff.dob);
            $('#userType').val(staff.user_type);
            $('#idCardType').val(staff.id_card_type);
            $('#idCardNumber').val(staff.id_card_number);
            $('#mobile').val(staff.mobile);
            $('#whatsapp').val(staff.whatsapp);
            $('#branch').val(staff.branch_id);
            $('#category').val(staff.category);
            $('#staffStatus').val(staff.status);
            $('#monthlySalary').val(staff.monthly_salary);
            $('#aadharNumber').val(staff.aadhar_number);
            $('#religiousAcademicDetails').val(staff.religious_academic_details);
            $('#academicDetails').val(staff.academic_details);
            $('#previousMadrasa').val(staff.previous_madrasa);
            $('#msrNumber').val(staff.msr_number);
            $('#notes').val(staff.notes);

            // Address fields
            if (staff.qatar_address) {
                $('#qatarPlace').val(staff.qatar_address.place);
                $('#qatarBuildingNo').val(staff.qatar_address.building_no);
                $('#qatarStreetNo').val(staff.qatar_address.street_no);
                $('#qatarZoneNo').val(staff.qatar_address.zone_no);
                $('#qatarLandmark').val(staff.qatar_address.landmark);
            }

            if (staff.india_address) {
                $('#indiaState').val(staff.india_address.state);
                $('#indiaDistrict').val(staff.india_address.district);
                $('#indiaPanchayath').val(staff.india_address.panchayath);
                $('#indiaPlace').val(staff.india_address.place);
                $('#indiaHouseName').val(staff.india_address.house_name);
            }

            // Allowances
            if (staff.other_allowances) {
                $('#transportAllowance').val(staff.other_allowances.transport || 0);
                $('#foodAllowance').val(staff.other_allowances.food || 0);
                $('#mobileAllowance').val(staff.other_allowances.mobile || 0);
            }

            // Switch to first tab
            $('#staffFormTabs a:first').tab('show');

            const modal = new bootstrap.Modal('#staffModal');
            modal.show();

        } catch (error) {
            console.error('Failed to load staff for editing:', error);
            Utils.showToast('Failed to load staff data', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Save staff (create or update)
     */
    saveStaff: async function() {
        Utils.showLoader();

        try {
            const formData = Utils.serializeForm($('#staffForm'));
            const staffId = $('#staffId').val();

            // Build allowances object
            formData.other_allowances = {
                transport: parseFloat($('#transportAllowance').val()) || 0,
                food: parseFloat($('#foodAllowance').val()) || 0,
                mobile: parseFloat($('#mobileAllowance').val()) || 0
            };

            // Build address objects
            formData.qatar_address = {
                place: $('#qatarPlace').val(),
                building_no: $('#qatarBuildingNo').val(),
                street_no: $('#qatarStreetNo').val(),
                zone_no: $('#qatarZoneNo').val(),
                landmark: $('#qatarLandmark').val()
            };

            formData.india_address = {
                state: $('#indiaState').val(),
                district: $('#indiaDistrict').val(),
                panchayath: $('#indiaPanchayath').val(),
                place: $('#indiaPlace').val(),
                house_name: $('#indiaHouseName').val()
            };

            let url, method;
            if (staffId) {
                url = API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.STAFFS.UPDATE, { id: staffId });
                method = 'PUT';
            } else {
                url = API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.STAFFS.CREATE);
                method = 'POST';
            }

            await $.ajax({
                url: url,
                method: method,
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(formData)
            });

            Utils.showToast(`Staff ${staffId ? 'updated' : 'created'} successfully`, 'success');
            bootstrap.Modal.getInstance('#staffModal').hide();
            staffDataTable.refresh();

        } catch (error) {
            console.error('Failed to save staff:', error);
            const message = error.responseJSON?.message || 'Failed to save staff';
            Utils.showToast(message, 'error');

            if (error.responseJSON?.errors) {
                Utils.showFormErrors($('#staffForm'), error.responseJSON.errors);
            }
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Delete staff
     */
    deleteStaff: function(staffId) {
        Utils.confirm('Are you sure you want to delete this staff member? This will deactivate their account.', async () => {
            Utils.showLoader();

            try {
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.STAFFS.DELETE, { id: staffId }),
                    method: 'DELETE',
                    headers: API_CONFIG.getHeaders()
                });

                Utils.showToast('Staff member deleted successfully', 'success');
                staffDataTable.refresh();

            } catch (error) {
                console.error('Failed to delete staff:', error);
                Utils.showToast('Failed to delete staff member', 'error');
            } finally {
                Utils.hideLoader();
            }
        });
    },

    /**
     * Export staff list
     */
    exportStaff: async function() {
        Utils.showToast('Export functionality will be implemented', 'info');
    }
};
