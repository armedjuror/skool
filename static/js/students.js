/**
 * Students Page JavaScript
 */

let studentsDataTable = null;

$(document).ready(function() {
    Students.init();
});

const Students = {
    init: function() {
        this.loadFilterOptions();
        this.initializeDataTable();
        this.setupFilterForm();
    },

    /**
     * Load filter dropdown options
     */
    loadFilterOptions: async function() {
        try {
            // Load branches
            const branchesResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SETTINGS.BRANCHES.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const branches = branchesResponse.results || branchesResponse.data || [];
            branches.forEach(branch => {
                $('#branchFilter').append(`<option value="${branch.id}">${branch.name}</option>`);
            });

            // Load classes
            const classesResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SETTINGS.CLASSES.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const classes = classesResponse.results || classesResponse.data || [];
            classes.forEach(cls => {
                $('#classFilter').append(`<option value="${cls.id}">${cls.name}</option>`);
            });

            // Load divisions
            const divisionsResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SETTINGS.DIVISIONS.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const divisions = divisionsResponse.results || divisionsResponse.data || [];
            divisions.forEach(div => {
                $('#divisionFilter').append(`<option value="${div.id}">${div.name}</option>`);
            });

        } catch (error) {
            console.error('Failed to load filter options:', error);
        }
    },

    /**
     * Initialize data table
     */
    initializeDataTable: function() {
        studentsDataTable = new DataTable({
            container: '#studentsTable',
            title: 'Students List',
            apiUrl: API_CONFIG.ENDPOINTS.STUDENTS.SEARCH,
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
                    key: 'admission_number',
                    label: 'Admission No',
                    sortable: true
                },
                {
                    key: 'name',
                    label: 'Student Name',
                    sortable: true
                },
                {
                    key: 'class_division',
                    label: 'Class/Division',
                    sortable: false,
                    render: (row) => `${row.class_name} - ${row.division_name}`
                },
                {
                    key: 'branch',
                    label: 'Branch',
                    sortable: true,
                    render: (row) => row.branch_name
                },
                {
                    key: 'parent_mobile',
                    label: 'Parent Mobile',
                    sortable: false
                },
                {
                    key: 'status',
                    label: 'Status',
                    sortable: true,
                    render: (row) => {
                        const statusClass = row.status === 'active' ? 'success' : 'secondary';
                        const statusText = row.status === 'active' ? 'Active' : 'Inactive';
                        return `<span class="badge badge-${statusClass}">${statusText}</span>`;
                    }
                },
                {
                    key: 'actions',
                    label: 'Actions',
                    sortable: false,
                    render: (row) => `
                        <div class="action-buttons">
                            <button class="btn-action" onclick="Students.viewStudent(${row.id})" title="View">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn-action" onclick="Students.editStudent(${row.id})" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-action danger" onclick="Students.deleteStudent(${row.id})" title="Delete">
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
                    onClick: () => Students.exportStudents()
                },
                {
                    name: 'add',
                    label: 'Add Student',
                    icon: 'fas fa-plus',
                    class: 'btn-primary',
                    onClick: () => Students.addStudent()
                }
            ],
            onRowClick: (row) => Students.viewStudent(row.id)
        });

        // Initial load
        studentsDataTable.loadData();
    },

    /**
     * Setup filter form
     */
    setupFilterForm: function() {
        $('#studentFilterForm').on('submit', function(e) {
            e.preventDefault();
            const filters = Utils.serializeForm($(this));
            studentsDataTable.setFilters(filters);
        });

        $('#clearFilters').on('click', function() {
            $('#studentFilterForm')[0].reset();
            studentsDataTable.setFilters({});
        });
    },

    /**
     * View student details
     */
    viewStudent: async function(studentId) {
        Utils.showLoader();

        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.STUDENTS.DETAIL, { id: studentId }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const student = response.data || response;

            const modalBody = `
                <div class="row">
                    <div class="col-md-3 text-center mb-3">
                        ${student.photo_url 
                            ? `<img src="${student.photo_url}" class="img-fluid rounded" alt="${student.name}">`
                            : `<div class="bg-secondary text-white d-flex align-items-center justify-content-center rounded" style="height: 200px;">
                                   <i class="fas fa-user fa-4x"></i>
                               </div>`
                        }
                    </div>
                    <div class="col-md-9">
                        <div class="detail-group">
                            <h6 class="detail-group-title">Personal Information</h6>
                            <div class="detail-row">
                                <div class="detail-label">Admission Number</div>
                                <div class="detail-value"><strong>${student.admission_number}</strong></div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Full Name</div>
                                <div class="detail-value">${student.name}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Gender</div>
                                <div class="detail-value">${student.gender}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Date of Birth</div>
                                <div class="detail-value">${Utils.formatDate(student.dob)} (Age: ${student.age})</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">ID Type</div>
                                <div class="detail-value">${student.id_type}: ${student.id_number}</div>
                            </div>
                        </div>
                        
                        <div class="detail-group">
                            <h6 class="detail-group-title">Academic Details</h6>
                            <div class="detail-row">
                                <div class="detail-label">Branch</div>
                                <div class="detail-value">${student.branch_name}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Class / Division</div>
                                <div class="detail-value">${student.class_name} - ${student.division_name}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Class Teacher</div>
                                <div class="detail-value">${student.teacher_name || '-'}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Status</div>
                                <div class="detail-value">
                                    <span class="badge badge-${student.status === 'active' ? 'success' : 'secondary'}">
                                        ${student.status === 'active' ? 'Active' : 'Inactive'}
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="detail-group">
                            <h6 class="detail-group-title">Contact Information</h6>
                            <div class="detail-row">
                                <div class="detail-label">Father's Name</div>
                                <div class="detail-value">${student.father_name}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Parent Mobile</div>
                                <div class="detail-value">${student.parent_mobile}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Email</div>
                                <div class="detail-value">${student.email || '-'}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            Modal.show({
                title: `Student Details - ${student.name}`,
                body: modalBody,
                size: 'lg',
                buttons: [
                    {
                        label: 'Edit',
                        class: 'btn-primary',
                        onClick: () => {
                            Modal.hide();
                            Students.editStudent(studentId);
                        }
                    },
                    {
                        label: 'Close',
                        class: 'btn-secondary',
                        onClick: () => Modal.hide()
                    }
                ]
            });

        } catch (error) {
            console.error('Failed to load student details:', error);
            Utils.showToast('Failed to load student details', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Add new student
     */
    addStudent: function() {
        // Navigate to registration page or open add form
        window.location.href = '/registrations';
    },

    /**
     * Edit student
     */
    editStudent: function(studentId) {
        Utils.showToast('Edit functionality will be implemented', 'info');
        // Implementation would show edit form modal
    },

    /**
     * Delete student
     */
    deleteStudent: function(studentId) {
        Utils.confirm('Are you sure you want to delete this student? This action cannot be undone.', async () => {
            Utils.showLoader();

            try {
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.STUDENTS.DELETE, { id: studentId }),
                    method: 'DELETE',
                    headers: API_CONFIG.getHeaders()
                });

                Utils.hideLoader();
                Utils.showToast('Student deleted successfully', 'success');
                studentsDataTable.refresh();

            } catch (error) {
                Utils.hideLoader();
                console.error('Failed to delete student:', error);
                Utils.showToast('Failed to delete student', 'error');
            }
        });
    },

    /**
     * Export students
     */
    exportStudents: async function() {
        Utils.showLoader();

        try {
            const filters = Utils.serializeForm($('#studentFilterForm'));
            const url = API_CONFIG.getUrlWithQuery(API_CONFIG.ENDPOINTS.STUDENTS.EXPORT, filters);

            const response = await $.ajax({
                url: url,
                method: 'GET',
                headers: API_CONFIG.getHeaders(),
                xhrFields: {
                    responseType: 'blob'
                }
            });

            Utils.downloadFile(response, `students_export_${new Date().getTime()}.xlsx`);
            Utils.showToast('Export completed successfully', 'success');

        } catch (error) {
            console.error('Failed to export students:', error);
            Utils.showToast('Failed to export students', 'error');
        } finally {
            Utils.hideLoader();
        }
    }
};