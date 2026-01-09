/**
 * Fee Management Page JavaScript
 * Handles fee types, structures, collection, and dues management
 */

let duesDataTable = null;
let feeTypesDataTable = null;
let feeStructureDataTable = null;
let collectionsDataTable = null;
let selectedStudent = null;

$(document).ready(function() {
    Fees.init();
});

const Fees = {
    init: function() {
        this.loadStats();
        this.loadFilterOptions();
        this.setupStudentSearch();
        this.setupTabHandlers();
        this.setupForms();
    },

    /**
     * Load fee statistics
     */
    loadStats: async function() {
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DASHBOARD.STATS),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const fees = response.data?.fees || {};
            $('#monthCollection').text('QAR ' + Utils.formatNumber(fees.this_month_collection || 0));
            $('#totalDues').text('QAR ' + Utils.formatNumber(fees.pending_dues || 0));
            $('#studentsWithDues').text(fees.total_students_with_dues || 0);

            // Load fee types count
            const feeTypesResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.MONTHLY.LIST),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });
            $('#activeFeeTypes').text(feeTypesResponse.count || 0);

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
            branches.forEach(branch => {
                $('#duesBranchFilter, #structureBranch').append(`<option value="${branch.id}">${branch.name}</option>`);
            });

            // Load classes
            const classesResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.CLASSES),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const classes = classesResponse.results || [];
            classes.forEach(cls => {
                $('#duesClassFilter, #structureClass').append(`<option value="${cls.id}">${cls.name}</option>`);
            });

        } catch (error) {
            console.error('Failed to load filter options:', error);
        }
    },

    /**
     * Setup student search
     */
    setupStudentSearch: function() {
        let searchTimeout;
        $('#studentSearch').on('input', function() {
            clearTimeout(searchTimeout);
            const query = $(this).val();

            if (query.length < 2) {
                $('#studentSearchResults').html('');
                return;
            }

            searchTimeout = setTimeout(async () => {
                try {
                    const response = await $.ajax({
                        url: API_CONFIG.getUrlWithQuery(API_CONFIG.ENDPOINTS.STUDENTS.LIST, { search: query }),
                        method: 'GET',
                        headers: API_CONFIG.getHeaders()
                    });

                    const students = response.results || [];
                    let html = '';

                    if (students.length === 0) {
                        html = '<div class="list-group-item text-muted">No students found</div>';
                    } else {
                        students.forEach(student => {
                            html += `
                                <a href="#" class="list-group-item list-group-item-action" onclick="Fees.selectStudent('${student.id}')">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <strong>${student.name}</strong>
                                            <small class="d-block text-muted">${student.admission_number}</small>
                                        </div>
                                        <div class="text-end">
                                            <small class="text-muted">${student.class_name || ''} ${student.division_name || ''}</small>
                                            <small class="d-block text-muted">${student.branch_name || ''}</small>
                                        </div>
                                    </div>
                                </a>
                            `;
                        });
                    }

                    $('#studentSearchResults').html(html);

                } catch (error) {
                    console.error('Search failed:', error);
                }
            }, 300);
        });
    },

    /**
     * Select student for fee collection
     */
    selectStudent: async function(studentId) {
        Utils.showLoader();

        try {
            // Get student details
            const studentResponse = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.STUDENTS.DETAIL, { id: studentId }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            selectedStudent = studentResponse.data || studentResponse;

            // Get student fee dues
            const duesResponse = await $.ajax({
                url: API_CONFIG.getUrlWithQuery(API_CONFIG.ENDPOINTS.FEES.STUDENT.FEE_DETAILS, { id: studentId }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const dues = duesResponse.data?.dues || duesResponse.dues || [];

            // Build collection form
            let duesHtml = '';
            let totalDue = 0;

            if (dues.length > 0) {
                duesHtml = `
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th><input type="checkbox" id="selectAllDues"></th>
                                <th>Fee Type</th>
                                <th>Month</th>
                                <th>Total</th>
                                <th>Paid</th>
                                <th>Due</th>
                                <th>Pay Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                dues.forEach((due, index) => {
                    if (due.due_amount > 0) {
                        totalDue += parseFloat(due.due_amount);
                        duesHtml += `
                            <tr>
                                <td><input type="checkbox" class="due-checkbox" data-index="${index}" data-due="${due.due_amount}"></td>
                                <td>${due.fee_type_name}</td>
                                <td>${due.month ? `${due.month}/${due.year}` : '-'}</td>
                                <td>QAR ${Utils.formatNumber(due.total_amount)}</td>
                                <td>QAR ${Utils.formatNumber(due.paid_amount)}</td>
                                <td class="text-danger">QAR ${Utils.formatNumber(due.due_amount)}</td>
                                <td>
                                    <input type="number" step="0.01" class="form-control form-control-sm pay-amount"
                                           data-index="${index}" data-max="${due.due_amount}"
                                           value="${due.due_amount}" style="width: 100px;">
                                </td>
                            </tr>
                        `;
                    }
                });

                duesHtml += '</tbody></table>';
            } else {
                duesHtml = '<p class="text-success"><i class="fas fa-check-circle"></i> No pending dues</p>';
            }

            const formHtml = `
                <div class="row mb-3">
                    <div class="col-md-6">
                        <h6 class="text-primary">${selectedStudent.name}</h6>
                        <small class="text-muted">
                            ${selectedStudent.admission_number} | ${selectedStudent.class_name || ''} ${selectedStudent.division_name || ''} | ${selectedStudent.branch_name || ''}
                        </small>
                    </div>
                    <div class="col-md-6 text-end">
                        <h5>Total Due: <span class="text-danger" id="totalDueAmount">QAR ${Utils.formatNumber(totalDue)}</span></h5>
                    </div>
                </div>
                <hr>
                <h6>Pending Dues</h6>
                ${duesHtml}
                ${dues.length > 0 && totalDue > 0 ? `
                <hr>
                <div class="row">
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Payment Method *</label>
                        <select class="form-select" id="paymentMethod" required>
                            <option value="CASH">Cash</option>
                            <option value="CARD">Card</option>
                            <option value="BANK_TRANSFER">Bank Transfer</option>
                            <option value="CHEQUE">Cheque</option>
                        </select>
                    </div>
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Reference Number</label>
                        <input type="text" class="form-control" id="referenceNumber" placeholder="Transaction ID, Cheque No...">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Total to Pay</label>
                        <h4 class="text-success" id="totalToPay">QAR 0</h4>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Remarks</label>
                    <textarea class="form-control" id="collectionRemarks" rows="2"></textarea>
                </div>
                <button type="button" class="btn btn-success btn-lg w-100" onclick="Fees.collectFee()">
                    <i class="fas fa-check"></i> Collect Fee
                </button>
                ` : ''}
            `;

            $('#feeCollectionForm').html(formHtml);
            $('#studentSearchResults').html('');
            $('#studentSearch').val('');

            // Setup checkboxes
            this.setupCollectionForm();

        } catch (error) {
            console.error('Failed to load student:', error);
            Utils.showToast('Failed to load student details', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Setup collection form handlers
     */
    setupCollectionForm: function() {
        // Select all checkbox
        $('#selectAllDues').on('change', function() {
            $('.due-checkbox').prop('checked', $(this).is(':checked')).trigger('change');
        });

        // Individual checkboxes
        $('.due-checkbox').on('change', function() {
            Fees.calculateTotal();
        });

        // Pay amount inputs
        $('.pay-amount').on('input', function() {
            const max = parseFloat($(this).data('max'));
            const val = parseFloat($(this).val()) || 0;
            if (val > max) $(this).val(max);
            Fees.calculateTotal();
        });

        // Initially check all and calculate
        $('#selectAllDues').prop('checked', true).trigger('change');
    },

    /**
     * Calculate total to pay
     */
    calculateTotal: function() {
        let total = 0;
        $('.due-checkbox:checked').each(function() {
            const index = $(this).data('index');
            const amount = parseFloat($(`.pay-amount[data-index="${index}"]`).val()) || 0;
            total += amount;
        });
        $('#totalToPay').text('QAR ' + Utils.formatNumber(total));
    },

    /**
     * Collect fee
     */
    collectFee: async function() {
        const items = [];

        $('.due-checkbox:checked').each(function() {
            const index = $(this).data('index');
            const amount = parseFloat($(`.pay-amount[data-index="${index}"]`).val()) || 0;
            if (amount > 0) {
                items.push({
                    index: index,
                    amount: amount
                });
            }
        });

        if (items.length === 0) {
            Utils.showToast('Please select at least one fee to collect', 'warning');
            return;
        }

        Utils.showLoader();

        try {
            const data = {
                student_id: selectedStudent.id,
                payment_method: $('#paymentMethod').val(),
                reference_number: $('#referenceNumber').val(),
                remarks: $('#collectionRemarks').val(),
                items: items
            };

            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.COLLECTION.COLLECT),
                method: 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data)
            });

            Utils.showToast('Fee collected successfully!', 'success');

            // Show receipt
            if (response.data?.receipt_number) {
                Fees.showReceipt(response.data.receipt_id || response.data.id);
            }

            // Refresh student data
            Fees.selectStudent(selectedStudent.id);
            Fees.loadStats();

        } catch (error) {
            console.error('Failed to collect fee:', error);
            const message = error.responseJSON?.message || 'Failed to collect fee';
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
                case '#feeDues':
                    if (!duesDataTable) this.initDuesTable();
                    break;
                case '#feeTypes':
                    if (!feeTypesDataTable) this.initFeeTypesTable();
                    break;
                case '#feeStructure':
                    if (!feeStructureDataTable) this.initFeeStructureTable();
                    break;
                case '#collectionHistory':
                    if (!collectionsDataTable) this.initCollectionsTable();
                    break;
            }
        });
    },

    /**
     * Initialize dues table
     */
    initDuesTable: function() {
        duesDataTable = new DataTable({
            container: '#duesTable',
            title: 'Fee Dues',
            apiUrl: API_CONFIG.ENDPOINTS.FEES.REPORTS.DUE_REPORT,
            columns: [
                { key: 'admission_number', label: 'Adm No', sortable: true },
                { key: 'student_name', label: 'Student', sortable: true },
                { key: 'class_name', label: 'Class', sortable: false },
                { key: 'branch_name', label: 'Branch', sortable: false },
                { key: 'fee_type_name', label: 'Fee Type', sortable: false },
                {
                    key: 'due_amount',
                    label: 'Due Amount',
                    sortable: true,
                    render: (row) => `<span class="text-danger">QAR ${Utils.formatNumber(row.due_amount)}</span>`
                },
                {
                    key: 'due_date',
                    label: 'Due Date',
                    sortable: true,
                    render: (row) => Utils.formatDate(row.due_date)
                },
                {
                    key: 'actions',
                    label: 'Actions',
                    sortable: false,
                    render: (row) => `
                        <button class="btn btn-sm btn-primary" onclick="Fees.selectStudent('${row.student_id}')">
                            <i class="fas fa-money-bill"></i> Collect
                        </button>
                    `
                }
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

        duesDataTable.loadData();

        // Filter form
        $('#duesFilterForm').on('submit', function(e) {
            e.preventDefault();
            duesDataTable.setFilters(Utils.serializeForm($(this)));
        });

        $('#clearDuesFilters').on('click', function() {
            $('#duesFilterForm')[0].reset();
            duesDataTable.setFilters({});
        });
    },

    /**
     * Initialize fee types table
     */
    initFeeTypesTable: function() {
        feeTypesDataTable = new DataTable({
            container: '#feeTypesTable',
            title: 'Fee Types',
            apiUrl: API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.MONTHLY.LIST,
            columns: [
                { key: 'name', label: 'Name', sortable: true },
                { key: 'category', label: 'Category', sortable: true },
                { key: 'charge_trigger', label: 'Charge Trigger', sortable: false },
                {
                    key: 'is_recurring',
                    label: 'Recurring',
                    sortable: false,
                    render: (row) => row.is_recurring ? '<span class="badge bg-success">Yes</span>' : '<span class="badge bg-secondary">No</span>'
                },
                {
                    key: 'is_active',
                    label: 'Status',
                    sortable: false,
                    render: (row) => row.is_active !== false ? '<span class="badge bg-success">Active</span>' : '<span class="badge bg-secondary">Inactive</span>'
                },
                {
                    key: 'actions',
                    label: 'Actions',
                    sortable: false,
                    render: (row) => `
                        <div class="action-buttons">
                            <button class="btn-action" onclick="Fees.editFeeType('${row.id}')" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-action danger" onclick="Fees.deleteFeeType('${row.id}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `
                }
            ],
            actions: [
                {
                    name: 'add',
                    label: 'Add Fee Type',
                    icon: 'fas fa-plus',
                    class: 'btn-primary',
                    onClick: () => Fees.showFeeTypeModal()
                }
            ]
        });

        feeTypesDataTable.loadData();
    },

    /**
     * Initialize fee structure table
     */
    initFeeStructureTable: function() {
        feeStructureDataTable = new DataTable({
            container: '#feeStructureTable',
            title: 'Fee Structure',
            apiUrl: API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.ADDITIONAL.LIST,
            columns: [
                { key: 'fee_type_name', label: 'Fee Type', sortable: true },
                { key: 'branch_name', label: 'Branch', sortable: true, render: (row) => row.branch_name || 'All' },
                { key: 'class_name', label: 'Class', sortable: true, render: (row) => row.class_name || 'All' },
                {
                    key: 'amount',
                    label: 'Amount',
                    sortable: true,
                    render: (row) => `QAR ${Utils.formatNumber(row.amount)}`
                },
                { key: 'applicable_to', label: 'Applicable To', sortable: false },
                {
                    key: 'effective_from',
                    label: 'Effective Period',
                    sortable: false,
                    render: (row) => `${Utils.formatDate(row.effective_from)} - ${Utils.formatDate(row.effective_to)}`
                },
                {
                    key: 'actions',
                    label: 'Actions',
                    sortable: false,
                    render: (row) => `
                        <div class="action-buttons">
                            <button class="btn-action" onclick="Fees.editFeeStructure('${row.id}')" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-action danger" onclick="Fees.deleteFeeStructure('${row.id}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `
                }
            ],
            actions: [
                {
                    name: 'add',
                    label: 'Add Structure',
                    icon: 'fas fa-plus',
                    class: 'btn-primary',
                    onClick: () => Fees.showFeeStructureModal()
                }
            ]
        });

        feeStructureDataTable.loadData();
    },

    /**
     * Initialize collections table
     */
    initCollectionsTable: function() {
        collectionsDataTable = new DataTable({
            container: '#collectionsTable',
            title: 'Collection History',
            apiUrl: API_CONFIG.ENDPOINTS.FEES.REPORTS.COLLECTION_REPORT,
            columns: [
                { key: 'receipt_number', label: 'Receipt No', sortable: true },
                { key: 'student_name', label: 'Student', sortable: true },
                { key: 'collection_date', label: 'Date', sortable: true, render: (row) => Utils.formatDate(row.collection_date) },
                {
                    key: 'total_amount',
                    label: 'Amount',
                    sortable: true,
                    render: (row) => `<span class="text-success">QAR ${Utils.formatNumber(row.total_amount)}</span>`
                },
                { key: 'payment_method', label: 'Method', sortable: false },
                { key: 'collected_by_name', label: 'Collected By', sortable: false },
                {
                    key: 'status',
                    label: 'Status',
                    sortable: false,
                    render: (row) => {
                        const classes = { 'APPROVED': 'success', 'PENDING': 'warning', 'CANCELLED': 'danger' };
                        return `<span class="badge bg-${classes[row.status] || 'secondary'}">${row.status}</span>`;
                    }
                },
                {
                    key: 'actions',
                    label: 'Actions',
                    sortable: false,
                    render: (row) => `
                        <button class="btn btn-sm btn-outline-primary" onclick="Fees.showReceipt('${row.id}')">
                            <i class="fas fa-receipt"></i> Receipt
                        </button>
                    `
                }
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

        collectionsDataTable.loadData();

        // Filter form
        $('#collectionsFilterForm').on('submit', function(e) {
            e.preventDefault();
            collectionsDataTable.setFilters(Utils.serializeForm($(this)));
        });

        $('#clearCollectionsFilters').on('click', function() {
            $('#collectionsFilterForm')[0].reset();
            collectionsDataTable.setFilters({});
        });
    },

    /**
     * Setup forms
     */
    setupForms: function() {
        // Fee type form
        $('#feeTypeForm').on('submit', async function(e) {
            e.preventDefault();
            await Fees.saveFeeType();
        });

        // Fee structure form
        $('#feeStructureForm').on('submit', async function(e) {
            e.preventDefault();
            await Fees.saveFeeStructure();
        });
    },

    /**
     * Show fee type modal
     */
    showFeeTypeModal: function(feeType = null) {
        $('#feeTypeModalTitle').text(feeType ? 'Edit Fee Type' : 'Add Fee Type');
        $('#feeTypeForm')[0].reset();
        $('#feeTypeId').val(feeType?.id || '');

        if (feeType) {
            $('#feeTypeName').val(feeType.name);
            $('#feeTypeCategory').val(feeType.category);
            $('#feeTypeChargeTrigger').val(feeType.charge_trigger);
            $('#feeTypeDescription').val(feeType.description);
            $('#feeTypeIsRecurring').prop('checked', feeType.is_recurring);
        }

        const modal = new bootstrap.Modal('#feeTypeModal');
        modal.show();
    },

    /**
     * Save fee type
     */
    saveFeeType: async function() {
        Utils.showLoader();

        try {
            const data = Utils.serializeForm($('#feeTypeForm'));
            data.is_recurring = $('#feeTypeIsRecurring').is(':checked');

            const id = $('#feeTypeId').val();
            const url = id
                ? API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.MONTHLY.UPDATE, { id })
                : API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.MONTHLY.CREATE);

            await $.ajax({
                url: url,
                method: id ? 'PUT' : 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data)
            });

            Utils.showToast(`Fee type ${id ? 'updated' : 'created'} successfully`, 'success');
            bootstrap.Modal.getInstance('#feeTypeModal').hide();
            feeTypesDataTable.refresh();

        } catch (error) {
            console.error('Failed to save fee type:', error);
            Utils.showToast('Failed to save fee type', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Show fee structure modal
     */
    showFeeStructureModal: async function(structure = null) {
        // Load fee types
        const feeTypesResponse = await $.ajax({
            url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.MONTHLY.LIST),
            method: 'GET',
            headers: API_CONFIG.getHeaders()
        });

        const feeTypes = feeTypesResponse.results || [];
        $('#structureFeeType').html('<option value="">Select Fee Type</option>');
        feeTypes.forEach(ft => {
            $('#structureFeeType').append(`<option value="${ft.id}">${ft.name}</option>`);
        });

        $('#feeStructureModalTitle').text(structure ? 'Edit Fee Structure' : 'Add Fee Structure');
        $('#feeStructureForm')[0].reset();
        $('#feeStructureId').val(structure?.id || '');

        if (structure) {
            $('#structureFeeType').val(structure.fee_type_id);
            $('#structureBranch').val(structure.branch_id);
            $('#structureClass').val(structure.class_level_id);
            $('#structureAmount').val(structure.amount);
            $('#structureApplicableTo').val(structure.applicable_to);
            $('#structureEffectiveFrom').val(structure.effective_from);
            $('#structureEffectiveTo').val(structure.effective_to);
        }

        const modal = new bootstrap.Modal('#feeStructureModal');
        modal.show();
    },

    /**
     * Save fee structure
     */
    saveFeeStructure: async function() {
        Utils.showLoader();

        try {
            const data = Utils.serializeForm($('#feeStructureForm'));
            const id = $('#feeStructureId').val();
            const url = id
                ? API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.ADDITIONAL.UPDATE, { id })
                : API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.ADDITIONAL.CREATE);

            await $.ajax({
                url: url,
                method: id ? 'PUT' : 'POST',
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(data)
            });

            Utils.showToast(`Fee structure ${id ? 'updated' : 'created'} successfully`, 'success');
            bootstrap.Modal.getInstance('#feeStructureModal').hide();
            feeStructureDataTable.refresh();

        } catch (error) {
            console.error('Failed to save fee structure:', error);
            Utils.showToast('Failed to save fee structure', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Show receipt
     */
    showReceipt: async function(collectionId) {
        Utils.showLoader();

        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.COLLECTION.RECEIPT, { id: collectionId }),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const receipt = response.data || response;

            const receiptHtml = `
                <div class="receipt-container" id="receiptPrintArea">
                    <div class="text-center mb-4">
                        <h4>Kerala Islamic Centre</h4>
                        <h5>Madrassa Fee Receipt</h5>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <p><strong>Receipt No:</strong> ${receipt.receipt_number}</p>
                            <p><strong>Date:</strong> ${Utils.formatDate(receipt.collection_date)}</p>
                        </div>
                        <div class="col-6 text-end">
                            <p><strong>Student:</strong> ${receipt.student_name}</p>
                            <p><strong>Admission No:</strong> ${receipt.admission_number}</p>
                        </div>
                    </div>
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Fee Type</th>
                                <th>Period</th>
                                <th class="text-end">Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${(receipt.items || []).map(item => `
                                <tr>
                                    <td>${item.fee_type_name}</td>
                                    <td>${item.month ? `${item.month}/${item.year}` : '-'}</td>
                                    <td class="text-end">QAR ${Utils.formatNumber(item.amount)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                        <tfoot>
                            <tr>
                                <th colspan="2">Total</th>
                                <th class="text-end">QAR ${Utils.formatNumber(receipt.total_amount)}</th>
                            </tr>
                        </tfoot>
                    </table>
                    <div class="row">
                        <div class="col-6">
                            <p><strong>Payment Method:</strong> ${receipt.payment_method}</p>
                            ${receipt.reference_number ? `<p><strong>Reference:</strong> ${receipt.reference_number}</p>` : ''}
                        </div>
                        <div class="col-6 text-end">
                            <p><strong>Collected By:</strong> ${receipt.collected_by_name || '-'}</p>
                        </div>
                    </div>
                </div>
            `;

            $('#receiptContent').html(receiptHtml);
            const modal = new bootstrap.Modal('#receiptModal');
            modal.show();

        } catch (error) {
            console.error('Failed to load receipt:', error);
            Utils.showToast('Failed to load receipt', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    /**
     * Print receipt
     */
    printReceipt: function() {
        const content = $('#receiptPrintArea').html();
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
            <head>
                <title>Fee Receipt</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { padding: 20px; }
                    @media print { body { padding: 0; } }
                </style>
            </head>
            <body>${content}</body>
            </html>
        `);
        printWindow.document.close();
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 250);
    },

    /**
     * Edit/Delete methods
     */
    editFeeType: async function(id) {
        const response = await $.ajax({
            url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.MONTHLY.UPDATE, { id }),
            method: 'GET',
            headers: API_CONFIG.getHeaders()
        });
        this.showFeeTypeModal(response.data || response);
    },

    deleteFeeType: function(id) {
        Utils.confirm('Are you sure you want to delete this fee type?', async () => {
            try {
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.MONTHLY.DELETE, { id }),
                    method: 'DELETE',
                    headers: API_CONFIG.getHeaders()
                });
                Utils.showToast('Fee type deleted', 'success');
                feeTypesDataTable.refresh();
            } catch (error) {
                Utils.showToast('Failed to delete fee type', 'error');
            }
        });
    },

    editFeeStructure: async function(id) {
        const response = await $.ajax({
            url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.ADDITIONAL.UPDATE, { id }),
            method: 'GET',
            headers: API_CONFIG.getHeaders()
        });
        this.showFeeStructureModal(response.data || response);
    },

    deleteFeeStructure: function(id) {
        Utils.confirm('Are you sure you want to delete this fee structure?', async () => {
            try {
                await $.ajax({
                    url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.FEES.CONFIGURATION.ADDITIONAL.DELETE, { id }),
                    method: 'DELETE',
                    headers: API_CONFIG.getHeaders()
                });
                Utils.showToast('Fee structure deleted', 'success');
                feeStructureDataTable.refresh();
            } catch (error) {
                Utils.showToast('Failed to delete fee structure', 'error');
            }
        });
    }
};
