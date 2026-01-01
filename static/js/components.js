/**
 * Reusable UI Components
 * Modal, DataTable, and other component functions
 */

/**
 * Modal Component
 * Customizable modal with various options
 */
const Modal = {
    instance: null,

    /**
     * Show modal
     * @param {object} options - Modal configuration
     */
    show: function(options) {
        const defaults = {
            title: 'Modal',
            body: '',
            size: 'md', // sm, md, lg, xl
            buttons: [
                {
                    label: 'Close',
                    class: 'btn-secondary',
                    onClick: () => this.hide()
                }
            ],
            closeOnBackdrop: true,
            onShow: null,
            onHide: null
        };

        const config = { ...defaults, ...options };

        // Update modal content
        $('#globalModalTitle').text(config.title);
        $('#globalModalBody').html(config.body);

        // Update modal size
        const $modalDialog = $('#globalModal .modal-dialog');
        $modalDialog.removeClass('modal-sm modal-lg modal-xl');
        if (config.size !== 'md') {
            $modalDialog.addClass(`modal-${config.size}`);
        }

        // Update buttons
        const $footer = $('#globalModalFooter');
        $footer.empty();

        config.buttons.forEach(btn => {
            const $btn = $(`<button type="button" class="btn ${btn.class}">${btn.label}</button>`);
            $btn.on('click', btn.onClick);
            $footer.append($btn);
        });

        // Configure backdrop behavior
        $('#globalModal').modal({
            backdrop: config.closeOnBackdrop ? true : 'static',
            keyboard: config.closeOnBackdrop
        });

        // Show modal
        this.instance = new bootstrap.Modal('#globalModal');
        this.instance.show();

        // Callbacks
        if (config.onShow) {
            $('#globalModal').on('shown.bs.modal', config.onShow);
        }
        if (config.onHide) {
            $('#globalModal').on('hidden.bs.modal', config.onHide);
        }
    },

    /**
     * Hide modal
     */
    hide: function() {
        if (this.instance) {
            this.instance.hide();
        }
    },

    /**
     * Update modal content
     * @param {string} body - New body content
     */
    updateBody: function(body) {
        $('#globalModalBody').html(body);
    },

    /**
     * Show confirmation modal
     * @param {string} message - Confirmation message
     * @param {function} onConfirm - Callback on confirm
     */
    confirm: function(message, onConfirm) {
        this.show({
            title: 'Confirm Action',
            body: `<p class="mb-0">${message}</p>`,
            buttons: [
                {
                    label: 'Cancel',
                    class: 'btn-secondary',
                    onClick: () => this.hide()
                },
                {
                    label: 'Confirm',
                    class: 'btn-primary',
                    onClick: () => {
                        this.hide();
                        onConfirm();
                    }
                }
            ]
        });
    }
};

/**
 * DataTable Component
 * AJAX-based data table with pagination and sorting
 */
class DataTable {
    constructor(options) {
        this.options = {
            container: '#dataTable',
            apiUrl: '',
            columns: [],
            searchable: true,
            sortable: true,
            pageSize: 20,
            onRowClick: null,
            actions: [],
            emptyMessage: 'No data available',
            ...options
        };

        this.currentPage = 1;
        this.totalPages = 1;
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.searchQuery = '';
        this.filters = {};

        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
    }

    render() {
        const html = `
            <div class="table-wrapper">
                <div class="table-header">
                    <h5 class="table-title">${this.options.title || 'Data Table'}</h5>
                    <div class="table-actions">
                        ${this.options.searchable ? `
                            <div class="search-box">
                                <i class="fas fa-search"></i>
                                <input type="text" class="form-control form-control-sm" 
                                       placeholder="Search..." id="tableSearch">
                            </div>
                        ` : ''}
                        ${this.options.actions.map(action => `
                            <button class="btn btn-sm ${action.class}" data-action="${action.name}">
                                <i class="${action.icon}"></i> ${action.label}
                            </button>
                        `).join('')}
                    </div>
                </div>
                <div class="table-responsive">
                    <table class="table" id="dataTableElement">
                        <thead></thead>
                        <tbody></tbody>
                    </table>
                </div>
                <div class="pagination-wrapper">
                    <div class="pagination-info"></div>
                    <ul class="pagination"></ul>
                </div>
            </div>
        `;

        $(this.options.container).html(html);
        this.renderHeaders();
    }

    renderHeaders() {
        const headers = this.options.columns.map(col => {
            const sortable = this.options.sortable && col.sortable !== false;
            return `
                <th class="${sortable ? 'sortable' : ''}" data-column="${col.key}">
                    ${col.label}
                    ${sortable ? '<i class="fas fa-sort ms-1"></i>' : ''}
                </th>
            `;
        }).join('');

        $(`${this.options.container} thead`).html(`<tr>${headers}</tr>`);
    }

    attachEvents() {
        const self = this;

        // Search
        if (this.options.searchable) {
            $(`${this.options.container} #tableSearch`).on('input', Utils.debounce(function() {
                self.searchQuery = $(this).val();
                self.currentPage = 1;
                self.loadData();
            }, 500));
        }

        // Sort
        if (this.options.sortable) {
            $(`${this.options.container} th.sortable`).on('click', function() {
                const column = $(this).data('column');

                if (self.sortColumn === column) {
                    self.sortDirection = self.sortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    self.sortColumn = column;
                    self.sortDirection = 'asc';
                }

                self.loadData();
                self.updateSortIcons();
            });
        }

        // Custom actions
        this.options.actions.forEach(action => {
            $(`${this.options.container} [data-action="${action.name}"]`).on('click', action.onClick);
        });
    }

    updateSortIcons() {
        $(`${this.options.container} th.sortable i`).removeClass('fa-sort-up fa-sort-down').addClass('fa-sort');

        if (this.sortColumn) {
            const icon = this.sortDirection === 'asc' ? 'fa-sort-up' : 'fa-sort-down';
            $(`${this.options.container} th[data-column="${this.sortColumn}"] i`)
                .removeClass('fa-sort')
                .addClass(icon);
        }
    }

    async loadData() {
        Utils.showLoader();

        try {
            const params = {
                page: this.currentPage,
                page_size: this.options.pageSize,
                search: this.searchQuery,
                sort_by: this.sortColumn,
                sort_order: this.sortDirection,
                ...this.filters
            };

            const url = API_CONFIG.getUrlWithQuery(this.options.apiUrl, params);
            const response = await $.ajax({
                url: url,
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            this.renderData(response.results || response.data || []);
            this.renderPagination(response.count || 0);

        } catch (error) {
            console.error('Error loading data:', error);
            Utils.showToast('Failed to load data', 'error');
            this.renderData([]);
        } finally {
            Utils.hideLoader();
        }
    }

    renderData(data) {
        const $tbody = $(`${this.options.container} tbody`);
        $tbody.empty();

        if (data.length === 0) {
            $tbody.html(`
                <tr>
                    <td colspan="${this.options.columns.length}" class="text-center py-5">
                        <div class="empty-state">
                            <i class="fas fa-inbox"></i>
                            <h5>No Data Available</h5>
                            <p>${this.options.emptyMessage}</p>
                        </div>
                    </td>
                </tr>
            `);
            return;
        }

        data.forEach(row => {
            const cells = this.options.columns.map(col => {
                const value = col.render ? col.render(row) : row[col.key];
                return `<td>${value || '-'}</td>`;
            }).join('');

            const $row = $(`<tr>${cells}</tr>`);

            if (this.options.onRowClick) {
                $row.css('cursor', 'pointer');
                $row.on('click', () => this.options.onRowClick(row));
            }

            $tbody.append($row);
        });
    }

    renderPagination(totalCount) {
        this.totalPages = Math.ceil(totalCount / this.options.pageSize);

        // Update info
        const start = (this.currentPage - 1) * this.options.pageSize + 1;
        const end = Math.min(this.currentPage * this.options.pageSize, totalCount);
        $(`${this.options.container} .pagination-info`).text(
            `Showing ${start} to ${end} of ${totalCount} entries`
        );

        // Update pagination
        const $pagination = $(`${this.options.container} .pagination`);
        $pagination.empty();

        // Previous button
        $pagination.append(`
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage - 1}">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `);

        // Page numbers
        const maxVisible = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(this.totalPages, startPage + maxVisible - 1);

        if (endPage - startPage < maxVisible - 1) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            $pagination.append(`
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        }

        // Next button
        $pagination.append(`
            <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage + 1}">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `);

        // Attach pagination events
        const self = this;
        $pagination.find('.page-link').on('click', function(e) {
            e.preventDefault();
            const page = parseInt($(this).data('page'));
            if (page > 0 && page <= self.totalPages && page !== self.currentPage) {
                self.currentPage = page;
                self.loadData();
            }
        });
    }

    setFilters(filters) {
        this.filters = filters;
        this.currentPage = 1;
        this.loadData();
    }

    refresh() {
        this.loadData();
    }
}

/**
 * Form Component
 * AJAX form submission with validation
 */
class AjaxForm {
    constructor(formSelector, options) {
        this.$form = $(formSelector);
        this.options = {
            apiUrl: '',
            method: 'POST',
            onSuccess: null,
            onError: null,
            resetOnSuccess: true,
            ...options
        };

        this.init();
    }

    init() {
        const self = this;
        this.$form.on('submit', function(e) {
            e.preventDefault();
            self.submit();
        });
    }

    async submit() {
        Utils.showLoader();

        const formData = Utils.serializeForm(this.$form);

        try {
            const response = await $.ajax({
                url: this.options.apiUrl,
                method: this.options.method,
                headers: API_CONFIG.getHeaders(),
                data: JSON.stringify(formData)
            });

            Utils.hideLoader();
            Utils.showToast('Operation completed successfully', 'success');

            if (this.options.resetOnSuccess) {
                Utils.resetForm(this.$form);
            }

            if (this.options.onSuccess) {
                this.options.onSuccess(response);
            }

        } catch (error) {
            Utils.hideLoader();

            if (error.responseJSON && error.responseJSON.errors) {
                Utils.showFormErrors(this.$form, error.responseJSON.errors);
            } else {
                const message = error.responseJSON?.message || 'An error occurred';
                Utils.showToast(message, 'error');
            }

            if (this.options.onError) {
                this.options.onError(error);
            }
        }
    }
}

/**
 * Export components for global use
 */
window.Modal = Modal;
window.DataTable = DataTable;
window.AjaxForm = AjaxForm;