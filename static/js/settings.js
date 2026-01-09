$(document).ready(function() {
    SettingsPage.init();
});

const SettingsPage = {
    currentEditId: null,

    // Track which tabs have been loaded
    loadedTabs: {
        academic: false,
        branches: false,
        classes: false,
        users: false,
        system: false
    },

    init: function() {
        this.setupEventListeners();

        // Explicitly initialize the first tab to ensure Bootstrap tabs work properly on first load
        const firstTabEl = document.querySelector('#academic-tab');
        if (firstTabEl) {
            const firstTab = new bootstrap.Tab(firstTabEl);
            firstTab.show();
        }

        // Load initial tab data
        this.loadAcademicYears();
        this.loadedTabs.academic = true;
    },

    setupEventListeners: function() {
        // Academic Year Form
        $('#academicYearForm').on('submit', (e) => {
            e.preventDefault();
            this.createAcademicYear();
        });

        // Branch Form
        $('#branchForm').on('submit', (e) => {
            e.preventDefault();
            this.createBranch();
        });

        // User Form
        $('#userForm').on('submit', (e) => {
            e.preventDefault();
            this.createUser();
        });

        // Add Class Button
        $('#addClassBtn').on('click', () => {
            this.showAddClassModal();
        });

        // Add Division Button
        $('#addDivisionBtn').on('click', () => {
            this.showAddDivisionModal();
        });

        // Edit Academic Year Save
        $('#saveAcademicYearBtn').on('click', () => {
            this.updateAcademicYear();
        });

        // Edit Branch Save
        $('#saveBranchBtn').on('click', () => {
            this.updateBranch();
        });

        // Backup Schedule Form
        $('#backupScheduleForm').on('submit', (e) => {
            e.preventDefault();
            this.saveBackupSchedule();
        });

        // Backup Frequency Change
        $('#backupFrequency').on('change', function() {
            if ($(this).val() !== 'disabled') {
                $('#backupTimeContainer').show();
            } else {
                $('#backupTimeContainer').hide();
            }
        });

        // Backup Now Button
        $('#backupNowBtn').on('click', () => {
            this.backupDatabase();
        });

        // Restore Form
        $('#restoreForm').on('submit', (e) => {
            e.preventDefault();
            this.restoreDatabase();
        });

        // Password Policy Form
        $('#passwordPolicyForm').on('submit', (e) => {
            e.preventDefault();
            this.savePasswordPolicy();
        });

        // Session Timeout Form
        $('#sessionTimeoutForm').on('submit', (e) => {
            e.preventDefault();
            this.saveSessionTimeout();
        });

        // Audit Logs Filters
        $('#logFilterUser, #logFilterAction, #logFilterFrom, #logFilterTo').on('change', () => {
            this.loadAuditLogs();
        });

        // Refresh Logs Button
        $('#refreshLogsBtn').on('click', () => {
            this.loadAuditLogs();
        });

        // User Search
        $('#userSearch').on('input', Utils.debounce(() => {
            this.searchUsers();
        }, 300));

        // Tab Change Events
        $('button[data-bs-toggle="tab"]').on('shown.bs.tab', (e) => {
            const target = $(e.target).attr('data-bs-target');
            this.onTabChange(target);
        });
    },

    onTabChange: function(target) {
        // Load data only on first visit to the tab
        switch(target) {
            case '#academic':
                if (!this.loadedTabs.academic) {
                    this.loadAcademicYears();
                    this.loadedTabs.academic = true;
                }
                break;
            case '#branches':
                if (!this.loadedTabs.branches) {
                    this.loadBranches();
                    this.loadTeachersForDropdown();
                    this.loadedTabs.branches = true;
                }
                break;
            case '#classes':
                if (!this.loadedTabs.classes) {
                    this.loadClasses();
                    this.loadDivisions();
                    this.loadedTabs.classes = true;
                }
                break;
            case '#users':
                if (!this.loadedTabs.users) {
                    this.loadUsers();
                    this.loadedTabs.users = true;
                }
                break;
            case '#system':
                if (!this.loadedTabs.system) {
                    this.loadAuditLogs();
                    this.loadSettings();
                    this.loadedTabs.system = true;
                }
                break;
        }
    },

    // ===== ACADEMIC YEAR FUNCTIONS =====
    loadAcademicYears: async function() {
        Utils.showLoader()
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.ACADEMIC_YEAR.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            this.renderAcademicYears(response.results || response.data || []);
        } catch (error) {
            Utils.showToast('Failed to load academic years', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    renderAcademicYears: function(years) {
        const container = $('#academicYearsContainer');

        if (!years || years.length === 0) {
            container.html(`
                <div class="empty-state text-center py-5">
                    <i class="fas fa-calendar-alt fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No academic years configured yet</p>
                </div>
            `);
            return;
        }

        let html = '<div class="list-group">';
        years.forEach(year => {
            const isActive = year.is_active;
            html += `
                <div class="list-group-item ${isActive ? 'active-year' : ''}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">
                                ${year.name}
                                ${isActive ? '<span class="badge bg-success ms-2">Active</span>' : ''}
                            </h6>
                            <small class="text-muted">
                                ${Utils.formatDate(year.start_date)} - ${Utils.formatDate(year.end_date)}
                            </small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            ${!isActive ? `
                                <button class="btn btn-outline-primary btn-action"
                                        onclick="SettingsPage.activateAcademicYear('${year.id}')">
                                    <i class="fas fa-check"></i>
                                </button>
                            ` : ''}
                            <button class="btn btn-outline-secondary btn-action"
                                    onclick="SettingsPage.editAcademicYear('${year.id}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            ${!isActive ? `
                                <button class="btn btn-outline-danger btn-action"
                                        onclick="SettingsPage.deleteAcademicYear('${year.id}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        container.html(html);
    },

    createAcademicYear: async function() {
        const data = {
            name: $('#academicYearName').val(),
            start_date: $('#academicStartDate').val(),
            end_date: $('#academicEndDate').val(),
            is_active: $('#academicIsActive').is(':checked')
        };

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.ACADEMIC_YEAR.CREATE),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data),
                contentType: 'application/json'
            });

            Utils.showToast('Academic year created successfully', 'success');
            $('#academicYearForm')[0].reset();
            await this.loadAcademicYears();
        } catch (error) {
            Utils.showToast(error.responseJSON?.message || 'Failed to create academic year', 'error');
            Utils.hideLoader();
        }
    },

    editAcademicYear: async function(id) {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.ACADEMIC_YEAR.DETAIL, { id }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const year = response.data || response;

            $('#editAcademicYearId').val(year.id);
            $('#editAcademicYearName').val(year.name);
            $('#editAcademicStartDate').val(year.start_date);
            $('#editAcademicEndDate').val(year.end_date);
            $('#editAcademicIsActive').prop('checked', year.is_active);

            new bootstrap.Modal('#editAcademicYearModal').show();
        } catch (error) {
            Utils.showToast('Failed to load academic year details', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    updateAcademicYear: async function() {
        const id = $('#editAcademicYearId').val();
        const data = {
            name: $('#editAcademicYearName').val(),
            start_date: $('#editAcademicStartDate').val(),
            end_date: $('#editAcademicEndDate').val(),
            is_active: $('#editAcademicIsActive').is(':checked')
        };

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.ACADEMIC_YEAR.UPDATE, { id }),
                method: 'PUT',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data),
                contentType: 'application/json'
            });

            Utils.showToast('Academic year updated successfully', 'success');
            bootstrap.Modal.getInstance('#editAcademicYearModal').hide();
            await this.loadAcademicYears();
        } catch (error) {
            Utils.showToast(error.responseJSON?.message || 'Failed to update academic year', 'error');
            Utils.hideLoader();
        }
    },

    activateAcademicYear: async function(id) {
        Utils.confirm('Set this as the active academic year?', async () => {
            try {
                Utils.showLoader();
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.ACADEMIC_YEAR.ACTIVATE, { id }),
                    method: 'POST',
                    headers: API_CONFIG.getHeaders()
                });
                Utils.showToast('Academic year activated', 'success');
                await this.loadAcademicYears();
            } catch (error) {
                Utils.showToast('Failed to activate academic year', 'error');
                Utils.hideLoader();
            }
        });
    },

    deleteAcademicYear: async function(id) {
        Utils.confirm('Delete this academic year? This action cannot be undone.', async () => {
            try {
                Utils.showLoader();
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.ACADEMIC_YEAR.DELETE, { id }),
                    method: 'DELETE',
                    headers: API_CONFIG.getHeaders()
                });

                Utils.showToast('Academic year deleted', 'success');
                await this.loadAcademicYears();
            } catch (error) {
                Utils.showToast('Failed to delete academic year', 'error');
                Utils.hideLoader();
            }
        });
    },

    // ===== BRANCH FUNCTIONS =====
    loadBranches: async function() {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.BRANCHES.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            this.renderBranches(response.results || response.data || []);
        } catch (error) {
            Utils.showToast('Failed to load branches', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    renderBranches: function(branches) {
        const container = $('#branchesContainer');

        if (!branches || branches.length === 0) {
            container.html(`
                <div class="empty-state text-center py-5">
                    <i class="fas fa-building fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No branches configured yet</p>
                </div>
            `);
            return;
        }

        let html = '<div class="list-group">';
        branches.forEach(branch => {
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${branch.name} - (${branch.code})</h6>
                            ${branch.address ? `<small class="text-muted d-block"><i class="fas fa-map-marker-alt me-1"></i>${branch.address.address_line_2}</small>` : ''}
                            <small class="text-muted d-block"><i class="fas fa-user me-1"></i>Head: ${branch.head_teacher_name || 'Not Assigned'}</small>
                            ${branch.phone ? `<small class="text-muted d-block"><i class="fas fa-phone me-1"></i>${branch.phone}</small>` : ''}
                            ${branch.email ? `<small class="text-muted d-block"><i class="fas fa-envelope me-1"></i><a href="mailto:${branch.email}">${branch.email}</a></small>` : ''}
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-secondary btn-action"
                                    onclick="SettingsPage.editBranch('${branch.id}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-action"
                                    onclick="SettingsPage.deleteBranch('${branch.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        container.html(html);
    },

    loadTeachersForDropdown: async function() {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.TEACHERS.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const teachers = response.results || response.data || [];
            let options = '<option value="">Select Head Teacher</option>';
            teachers.forEach(teacher => {
                options += `<option value="${teacher.id}">${teacher.name}</option>`;
            });

            $('#branchHeadTeacher, #editBranchHeadTeacher').html(options);
        } catch (error) {
            console.error('Failed to load teachers:', error);
        } finally {
            Utils.hideLoader();
        }
    },

    createBranch: async function() {
        const data = {
            name: $('#branchName').val(),
            code: $('#branchCode').val(),
            address: {'address_line_2': $('#branchLocation').val()},
            head_teacher_id: $('#branchHeadTeacher').val() || null,
            phone: $('#branchContact').val(),
            email: $('#branchEmail').val()
        };

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.BRANCHES.CREATE),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data),
                contentType: 'application/json'
            });

            Utils.showToast('Branch created successfully', 'success');
            $('#branchForm')[0].reset();
            await this.loadBranches();
        } catch (error) {
            Utils.showToast(error.responseJSON?.message || 'Failed to create branch', 'error');
            Utils.hideLoader();
        }
    },

    editBranch: async function(id) {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.BRANCHES.DETAIL, { id }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const branch = response.data || response;

            $('#editBranchId').val(branch.id);
            $('#editBranchName').val(branch.name);
            $('#editBranchLocation').val(branch.address.address_line_2 || '');
            $('#editBranchHeadTeacher').val(branch.head_teacher || '');
            $('#editBranchContact').val(branch.phone || '');
            $('#editBranchEmail').val(branch.email || '');

            new bootstrap.Modal('#editBranchModal').show();
        } catch (error) {
            Utils.showToast('Failed to load branch details', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    updateBranch: async function() {
        const id = $('#editBranchId').val();
        const data = {
            name: $('#editBranchName').val(),
            address: {address_line_2: $('#editBranchLocation').val()},
            head_teacher: $('#editBranchHeadTeacher').val() || null,
            phone: $('#editBranchContact').val() || null,
            email: $('#editBranchEmail').val() || null,
        };

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.BRANCHES.UPDATE, { id }),
                method: 'PUT',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data),
                contentType: 'application/json'
            });

            Utils.showToast('Branch updated successfully', 'success');
            bootstrap.Modal.getInstance('#editBranchModal').hide();
            await this.loadBranches();
        } catch (error) {
            Utils.showToast(error.responseJSON?.message || 'Failed to update branch', 'error');
            Utils.hideLoader();
        }
    },

    deleteBranch: async function(id) {
        Utils.confirm('Delete this branch? This action cannot be undone.', async () => {
            try {
                Utils.showLoader();
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.BRANCHES.DELETE, { id }),
                    method: 'DELETE',
                    headers: API_CONFIG.getHeaders()
                });

                Utils.showToast('Branch deleted', 'success');
                await this.loadBranches();
            } catch (error) {
                Utils.showToast('Failed to delete branch', 'error');
                Utils.hideLoader();
            }
        });
    },

    // ===== CLASSES & DIVISIONS FUNCTIONS =====
    loadClasses: async function() {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.CLASSES.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            this.renderClasses(response.results || response.data || []);
        } catch (error) {
            Utils.showToast('Failed to load classes', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    renderClasses: function(classes) {
        const container = $('#classesContainer');

        if (!classes || classes.length === 0) {
            container.html(`
                <div class="empty-state text-center py-4">
                    <i class="fas fa-chalkboard fa-2x text-muted mb-2"></i>
                    <p class="text-muted small">No classes configured yet</p>
                </div>
            `);
            return;
        }

        let html = '<div class="list-group list-group-sm">';
        classes.forEach(cls => {
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center py-2">
                    <span>${cls.name}</span>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary btn-sm"
                                onclick="SettingsPage.editClass('${cls.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm"
                                onclick="SettingsPage.deleteClass('${cls.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        container.html(html);
    },

    loadDivisions: async function() {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DIVISIONS.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            this.renderDivisions(response.results || response.data || []);
        } catch (error) {
            Utils.showToast('Failed to load divisions', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    renderDivisions: function(divisions) {
        const container = $('#divisionsContainer');

        if (!divisions || divisions.length === 0) {
            container.html(`
                <div class="empty-state text-center py-4">
                    <i class="fas fa-list fa-2x text-muted mb-2"></i>
                    <p class="text-muted small">No divisions configured yet</p>
                </div>
            `);
            return;
        }

        let html = '<div class="list-group list-group-sm">';
        divisions.forEach(div => {
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center py-2">
                    <span>${div.name}</span>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary btn-sm"
                                onclick="SettingsPage.editDivision('${div.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm"
                                onclick="SettingsPage.deleteDivision('${div.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        container.html(html);
    },

    showAddClassModal: function() {
        Modal.show({
            title: 'Add Class',
            body: `
                <form id="addClassModalForm">
                    <div class="mb-3">
                        <label for="className" class="form-label">Class Name</label>
                        <input type="text" class="form-control" id="className" 
                               placeholder="e.g., I, II, III, IV..." required>
                    </div>
                    <div class="mb-3">
                        <label for="classLevel" class="form-label">Level</label>
                        <input type="number" class="form-control" id="classLevel" 
                               placeholder="e.g., 1, 2, 3, ... 12" required min="1" max="12">
                    </div>
                </form>
            `,
            buttons: [
                {
                    label: 'Cancel',
                    class: 'btn-secondary',
                    onClick: () => Modal.hide()
                },
                {
                    label: 'Add Class',
                    class: 'btn-primary',
                    onClick: () => this.createClass()
                }
            ]
        });
    },

    createClass: async function() {
        const name = $('#className').val();
        const level = $('#classLevel').val();
        if (!name || !level) return;

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.CLASSES.CREATE),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify({ name: name, level: level }),
                contentType: 'application/json'
            });

            Utils.showToast('Class created successfully', 'success');
            Modal.hide();
            await this.loadClasses();
        } catch (error) {
            Utils.showToast('Failed to create class', 'error');
            Utils.hideLoader();
        }
    },

    editClass: async function(id) {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.CLASSES.DETAIL, { id }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const cls = response.data || response;

            Modal.show({
                title: 'Edit Class',
                body: `
                    <form id="editClassModalForm">
                        <div class="mb-3">
                            <label for="editClassName" class="form-label">Class Name</label>
                            <input type="text" class="form-control" id="editClassName"
                                   value="${cls.name}" required>
                        </div>
                        <div class="mb-3">
                            <label for="editClassLevel" class="form-label">Class Level</label>
                            <input type="number" class="form-control" id="editClassLevel" min="1" max="12"
                                   value="${cls.level}" required>
                        </div>
                    </form>
                `,
                buttons: [
                    {
                        label: 'Cancel',
                        class: 'btn-secondary',
                        onClick: () => Modal.hide()
                    },
                    {
                        label: 'Save Changes',
                        class: 'btn-primary',
                        onClick: () => this.updateClass(id)
                    }
                ]
            });
        } catch (error) {
            Utils.showToast('Failed to load class details', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    updateClass: async function(id) {
        const name = $('#editClassName').val();
        const level = $('#editClassLevel').val();
        if (!name || !level) return;

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.CLASSES.UPDATE, { id }),
                method: 'PUT',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify({ name: name, level: level }),
                contentType: 'application/json'
            });

            Utils.showToast('Class updated successfully', 'success');
            Modal.hide();
            await this.loadClasses();
        } catch (error) {
            Utils.showToast('Failed to update class', 'error');
            Utils.hideLoader();
        }
    },

    deleteClass: async function(id) {
        Utils.confirm('Delete this class? This action cannot be undone.', async () => {
            try {
                Utils.showLoader();
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.CLASSES.DELETE, { id }),
                    method: 'DELETE',
                    headers: API_CONFIG.getHeaders()
                });

                Utils.showToast('Class deleted', 'success');
                await this.loadClasses();
            } catch (error) {
                Utils.showToast('Failed to delete class', 'error');
                Utils.hideLoader();
            }
        });
    },

    showAddDivisionModal: function() {
        Modal.show({
            title: 'Add Division',
            body: `
                <form id="addDivisionModalForm">
                    <div class="mb-3">
                        <label for="divisionName" class="form-label">Division Name</label>
                        <input type="text" class="form-control" id="divisionName" 
                               placeholder="e.g., A, B, C..." required>
                    </div>
                </form>
            `,
            buttons: [
                {
                    label: 'Cancel',
                    class: 'btn-secondary',
                    onClick: () => Modal.hide()
                },
                {
                    label: 'Add Division',
                    class: 'btn-primary',
                    onClick: () => this.createDivision()
                }
            ]
        });
    },

    createDivision: async function() {
        const name = $('#divisionName').val();
        if (!name) return;

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DIVISIONS.CREATE),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify({ name }),
                contentType: 'application/json'
            });

            Utils.showToast('Division created successfully', 'success');
            Modal.hide();
            await this.loadDivisions();
        } catch (error) {
            Utils.showToast('Failed to create division', 'error');
            Utils.hideLoader();
        }
    },

    editDivision: async function(id) {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DIVISIONS.DETAIL, { id }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const div = response.data || response;

            Modal.show({
                title: 'Edit Division',
                body: `
                    <form id="editDivisionModalForm">
                        <div class="mb-3">
                            <label for="editDivisionName" class="form-label">Division Name</label>
                            <input type="text" class="form-control" id="editDivisionName"
                                   value="${div.name}" required>
                        </div>
                    </form>
                `,
                buttons: [
                    {
                        label: 'Cancel',
                        class: 'btn-secondary',
                        onClick: () => Modal.hide()
                    },
                    {
                        label: 'Save Changes',
                        class: 'btn-primary',
                        onClick: () => this.updateDivision(id)
                    }
                ]
            });
        } catch (error) {
            Utils.showToast('Failed to load division details', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    updateDivision: async function(id) {
        const name = $('#editDivisionName').val();
        if (!name) return;

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DIVISIONS.UPDATE, { id }),
                method: 'PUT',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify({ name }),
                contentType: 'application/json'
            });

            Utils.showToast('Division updated successfully', 'success');
            Modal.hide();
            await this.loadDivisions();
        } catch (error) {
            Utils.showToast('Failed to update division', 'error');
            Utils.hideLoader();
        }
    },

    deleteDivision: async function(id) {
        Utils.confirm('Delete this division? This action cannot be undone.', async () => {
            try {
                Utils.showLoader();
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DIVISIONS.DELETE, { id }),
                    method: 'DELETE',
                    headers: API_CONFIG.getHeaders()
                });

                Utils.showToast('Division deleted', 'success');
                await this.loadDivisions();
            } catch (error) {
                Utils.showToast('Failed to delete division', 'error');
                Utils.hideLoader();
            }
        });
    },

    // ===== USER MANAGEMENT FUNCTIONS =====
    loadUsers: async function() {
        try {
            Utils.showLoader();
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.USERS.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            this.renderUsers(response.results || response.data || []);
        } catch (error) {
            Utils.showToast('Failed to load users', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    renderUsers: function(users) {
        const container = $('#usersContainer');

        if (!users || users.length === 0) {
            container.html(`
                <div class="empty-state text-center py-5">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No users found</p>
                </div>
            `);
            return;
        }

        const roleColors = {
            'ADMIN': 'danger',
            'CHIEF_HEAD_TEACHER': 'danger',
            'HEAD_TEACHER': 'primary',
            'TEACHER': 'primary',
            'ACCOUNTANT': 'info',
            'OFFICE_STAFF': 'info',
            'STUDENT': 'secondary',
            'PARENT': 'secondary'
        };

        let html = '<div class="list-group">';
        users.forEach(user => {
            const roleBadge = roleColors[user.user_type] || 'secondary';
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">
                                ${user.first_name+ " " + user.last_name} 
                                <span class="badge bg-${roleBadge} ms-2">${user.user_type}</span>
                            </h6>
                            <small class="text-muted d-block">
                                <i class="fas fa-envelope me-1"></i>${user.email}
                            </small>
                            ${user.branches && user.branches.length > 0 ? `
                                <small class="text-muted d-block">
                                    <i class="fas fa-building me-1"></i>
                                    ${user.branches.map(b => b.name).join(', ')}
                                </small>
                            ` : ''}
                            <small class="text-muted d-block">
                                Last login: ${user.last_login ? Utils.formatDate(user.last_login, true) : 'Never'}
                            </small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-warning btn-action"
                                    onclick="SettingsPage.resetUserPassword('${user.id}')"
                                    title="Reset Password">
                                <i class="fas fa-key"></i>
                            </button>
                            <button class="btn btn-outline-secondary btn-action"
                                    onclick="SettingsPage.editUser('${user.id}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-action"
                                    onclick="SettingsPage.deleteUser('${user.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        container.html(html);
    },

    loadBranchesForDropdown: async function() {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.BRANCHES.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const branches = response.results || response.data || [];
            let options = '';
            branches.forEach(branch => {
                options += `<option value="${branch.id}">${branch.name}</option>`;
            });

            $('#userBranches').html(options);
        } catch (error) {
            console.error('Failed to load branches:', error);
        } finally {
            Utils.hideLoader()
        }
    },

    createUser: async function() {
        const data = {
            first_name: $('#userFirstName').val(),
            last_name: $('#userLastName').val(),
            email: $('#userEmail').val(),
            user_type: $('#userType').val(),
            password: $('#userPassword').val(),
        };

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.USERS.CREATE),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data),
                contentType: 'application/json'
            });

            Utils.showToast('User created successfully', 'success');
            $('#userForm')[0].reset();
            await this.loadUsers();
        } catch (error) {
            Utils.showToast(error.responseJSON?.message || 'Failed to create user', 'error');
            Utils.hideLoader();
        }
    },

    editUser: async function(id) {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.USERS.DETAIL, { id }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const user = response.data || response;

            // Load branches first
            // await this.loadBranchesForDropdown();

            Modal.show({
                title: 'Edit User',
                size: 'lg',
                body: `
                    <form id="editUserModalForm">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="editUserFirstName" class="form-label">First Name</label>
                                <input type="text" class="form-control" id="editUserFirstName"
                                       value="${user.first_name}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label for="editUserLastName" class="form-label">Last Name</label>
                                <input type="text" class="form-control" id="editUserLastName"
                                       value="${user.last_name}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label for="editUserEmail" class="form-label">Email</label>
                                <input type="email" class="form-control" id="editUserEmail"
                                       value="${user.email}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label for="editUserRole" class="form-label">Role</label>
                                <select class="form-select" id="editUserRole" required>
                                    <option value="ADMIN" ${user.user_type === 'ADMIN' ? 'selected' : ''}>Administrator</option>
                                    <option value="CHIEF_HEAD_TEACHER" ${user.user_type === 'CHIEF_HEAD_TEACHER' ? 'selected' : ''}>Chief Head Teacher</option>
                                    <option value="HEAD_TEACHER" ${user.user_type === 'HEAD_TEACHER' ? 'selected' : ''}>Branch Head Teacher</option>
                                    <option value="TEACHER" ${user.user_type === 'TEACHER' ? 'selected' : ''}>Teacher</option>
                                    <option value="ACCOUNTANT" ${user.user_type === 'ACCOUNTANT' ? 'selected' : ''}>Accountant</option>
                                    <option value="OFFICE_STAFF" ${user.user_type === 'OFFICE_STAFF' ? 'selected' : ''}>Office Staff</option>
                                    <option value="STUDENT" ${user.user_type === 'STUDENT' ? 'selected' : ''}>Student</option>
                                    <option value="PARENT" ${user.user_type === 'PARENT' ? 'selected' : ''}>Parent</option>
                                </select>
                            </div>
                        </div>
                    </form>
                `,
                buttons: [
                    {
                        label: 'Cancel',
                        class: 'btn-secondary',
                        onClick: () => Modal.hide()
                    },
                    {
                        label: 'Save Changes',
                        class: 'btn-primary',
                        onClick: () => this.updateUser(id)
                    }
                ]
            });

            // // Set selected branches
            // if (user.branches) {
            //     const branchIds = user.branches.map(b => b.id);
            //     $('#editUserBranches').val(branchIds);
            // }
        } catch (error) {
            Utils.showToast('Failed to load user details', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    updateUser: async function(id) {
        const data = {
            first_name: $('#editUserFirstName').val(),
            last_name: $('#editUserLastName').val(),
            email: $('#editUserEmail').val(),
            user_type: $('#editUserRole').val(),
        };

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.USERS.UPDATE, { id }),
                method: 'PUT',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data),
                contentType: 'application/json'
            });

            Utils.showToast('User updated successfully', 'success');
            Modal.hide();
            await this.loadUsers();
        } catch (error) {
            Utils.showToast(error.responseJSON?.message || 'Failed to update user', 'error');
            Utils.hideLoader();
        }
    },

    resetUserPassword: async function(id) {
        Modal.show({
            title: 'Reset Password',
            body: `
                <form id="resetPasswordForm">
                    <div class="mb-3">
                        <label for="newPassword" class="form-label">New Password</label>
                        <input type="password" class="form-control" id="newPassword" required>
                    </div>
                    <div class="mb-3">
                        <label for="confirmPassword" class="form-label">Confirm Password</label>
                        <input type="password" class="form-control" id="confirmPassword" required>
                    </div>
                </form>
            `,
            buttons: [
                {
                    label: 'Cancel',
                    class: 'btn-secondary',
                    onClick: () => Modal.hide()
                },
                {
                    label: 'Reset Password',
                    class: 'btn-warning',
                    onClick: async () => {
                        const newPassword = $('#newPassword').val();
                        const confirmPassword = $('#confirmPassword').val();

                        if (newPassword !== confirmPassword) {
                            Utils.showToast('Passwords do not match', 'error');
                            return;
                        }

                        try {
                            Utils.showLoader();
                            await $.ajax({
                                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.USERS.RESET_PASSWORD, { id }),
                                method: 'POST',
                                headers: API_CONFIG.getHeaders(),
                                data: JSON.stringify({ password: newPassword }),
                                contentType: 'application/json'
                            });

                            Utils.showToast('Password reset successfully', 'success');
                            Modal.hide();
                        } catch (error) {
                            Utils.showToast('Failed to reset password', 'error');
                        } finally {
                            Utils.hideLoader();
                        }
                    }
                }
            ]
        });
    },

    deleteUser: async function(id) {
        Utils.confirm('Delete this user? This action cannot be undone.', async () => {
            try {
                Utils.showLoader();
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.USERS.DELETE, { id }),
                    method: 'DELETE',
                    headers: API_CONFIG.getHeaders()
                });

                Utils.showToast('User deleted', 'success');
                await this.loadUsers();
            } catch (error) {
                Utils.showToast('Failed to delete user', 'error');
                Utils.hideLoader();
            }
        });
    },

    searchUsers: async function() {
        const query = $('#userSearch').val();

        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.USERS.SEARCH),
                method: 'GET',
                headers: API_CONFIG.getHeaders(),
                data: { q: query }
            });

            this.renderUsers(response.results || response.data || []);
        } catch (error) {
            console.error('Search failed:', error);
        }
    },

    // ===== SYSTEM FUNCTIONS =====
    backupDatabase: async function() {
        Utils.confirm('Create a database backup now?', async () => {
            try {
                Utils.showLoader();
                const response = await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SYSTEM.BACKUP),
                    method: 'POST',
                    headers: API_CONFIG.getHeaders()
                });

                // Download the backup file
                if (response.download_url) {
                    window.location.href = response.download_url;
                }

                Utils.showToast('Backup created successfully', 'success');
            } catch (error) {
                Utils.showToast('Failed to create backup', 'error');
            } finally {
                Utils.hideLoader();
            }
        });
    },

    saveBackupSchedule: async function() {
        const data = {
            frequency: $('#backupFrequency').val(),
            time: $('#backupTime').val()
        };

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SYSTEM.BACKUP_SCHEDULE),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data),
                contentType: 'application/json'
            });

            Utils.showToast('Backup schedule saved', 'success');
        } catch (error) {
            Utils.showToast('Failed to save backup schedule', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    restoreDatabase: async function() {
        const fileInput = $('#restoreFile')[0];
        if (!fileInput.files || !fileInput.files[0]) {
            Utils.showToast('Please select a backup file', 'warning');
            return;
        }

        Utils.confirm(
            'Restore database from backup? This will overwrite all current data. This action cannot be undone!',
            async () => {
                const formData = new FormData();
                formData.append('backup_file', fileInput.files[0]);

                try {
                    Utils.showLoader();
                    await $.ajax({
                        url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SYSTEM.RESTORE),
                        method: 'POST',
                        headers: API_CONFIG.getHeaders(),
                        data: formData,
                        processData: false,
                        contentType: false
                    });

                    Utils.showToast('Database restored successfully. Please refresh the page.', 'success');
                    setTimeout(() => window.location.reload(), 2000);
                } catch (error) {
                    Utils.showToast('Failed to restore database', 'error');
                } finally {
                    Utils.hideLoader();
                }
            }
        );
    },

    savePasswordPolicy: async function() {
        const data = {
            min_length: parseInt($('#minPasswordLength').val()),
            require_uppercase: $('#requireUppercase').is(':checked'),
            require_lowercase: $('#requireLowercase').is(':checked'),
            require_numbers: $('#requireNumbers').is(':checked'),
            require_special: $('#requireSpecialChars').is(':checked')
        };

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SYSTEM.PASSWORD_POLICY),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data),
                contentType: 'application/json'
            });

            Utils.showToast('Password policy saved', 'success');
        } catch (error) {
            Utils.showToast('Failed to save password policy', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    saveSessionTimeout: async function() {
        const data = {
            timeout_minutes: parseInt($('#sessionTimeout').val())
        };

        try {
            Utils.showLoader();
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SYSTEM.SESSION_TIMEOUT),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data),
                contentType: 'application/json'
            });

            Utils.showToast('Session timeout saved', 'success');
        } catch (error) {
            Utils.showToast('Failed to save session timeout', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    loadAuditLogs: async function() {
        Utils.showLoader();
        const filters = {
            user: $('#logFilterUser').val(),
            action: $('#logFilterAction').val(),
            from_date: $('#logFilterFrom').val(),
            to_date: $('#logFilterTo').val()
        };

        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SYSTEM.AUDIT_LOGS),
                method: 'GET',
                headers: API_CONFIG.getHeaders(),
                data: filters
            });

            this.renderAuditLogs(response.results || response.data || []);
        } catch (error) {
            Utils.showToast('Failed to load audit logs', 'error');
        }finally {
            Utils.hideLoader();
        }
    },

    renderAuditLogs: function(logs) {
        const container = $('#auditLogsContainer');

        if (!logs || logs.length === 0) {
            container.html(`
                <div class="empty-state text-center py-4">
                    <i class="fas fa-history fa-2x text-muted mb-2"></i>
                    <p class="text-muted">No audit logs found</p>
                </div>
            `);
            return;
        }

        const actionColors = {
            'create': 'success',
            'update': 'info',
            'delete': 'danger',
            'login': 'primary',
            'logout': 'secondary'
        };

        let html = `
            <table class="table table-sm table-hover">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>User</th>
                        <th>Action</th>
                        <th>Resource</th>
                        <th>Details</th>
                        <th>IP Address</th>
                    </tr>
                </thead>
                <tbody>
        `;

        logs.forEach(log => {
            const actionBadge = actionColors[log.action] || 'secondary';
            html += `
                <tr>
                    <td><small>${Utils.formatDate(log.timestamp, true)}</small></td>
                    <td><small>${log.user_name || 'System'}</small></td>
                    <td><span class="badge bg-${actionBadge}">${log.action}</span></td>
                    <td><small>${log.resource_type || '-'}</small></td>
                    <td><small>${log.details || '-'}</small></td>
                    <td><small>${log.ip_address || '-'}</small></td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        container.html(html);
    },

    loadUsersForAuditFilter: function(users) {
        let options = '<option value="">All Users</option>';
        users.forEach(user => {
            options += `<option value="${user.id}">${user.name}</option>`;
        });
        $('#logFilterUser').html(options);
    },

    loadSettings: async function() {
        Utils.showLoader();
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.SETTINGS),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const settings = response.data || response;

            // Load backup schedule
            if (settings.backup_schedule) {
                $('#backupFrequency').val(settings.backup_schedule.frequency || 'disabled');
                $('#backupTime').val(settings.backup_schedule.time || '');
                if (settings.backup_schedule.frequency !== 'disabled') {
                    $('#backupTimeContainer').show();
                }
            }

            // Load password policy
            if (settings.password_policy) {
                $('#minPasswordLength').val(settings.password_policy.min_length || 8);
                $('#requireUppercase').prop('checked', settings.password_policy.require_uppercase !== false);
                $('#requireLowercase').prop('checked', settings.password_policy.require_lowercase !== false);
                $('#requireNumbers').prop('checked', settings.password_policy.require_numbers !== false);
                $('#requireSpecialChars').prop('checked', settings.password_policy.require_special || false);
            }

            // Load session timeout
            if (settings.session_timeout) {
                $('#sessionTimeout').val(settings.session_timeout.timeout_minutes || 30);
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        } finally {
            Utils.hideLoader();
        }
    }
};