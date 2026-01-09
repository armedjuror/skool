/**
 * Layout JavaScript
 * Handles sidebar, navigation, and layout interactions
 */

$(document).ready(function() {
    // Initialize layout
    Layout.init();
});

const Layout = {
    init: function() {
        // this.loadUserInfo();
        this.setupSidebarToggle();
        this.setupNavigation();
        this.setupLogout();
        this.updatePendingCount();
        this.filterMenuByRole();
    },

    /**
     * Load user information
     */
    // loadUserInfo: async function() {
    //     try {
    //         const response = await $.ajax({
    //             url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.AUTH.GET_USER_INFO),
    //             method: 'GET',
    //             headers: API_CONFIG.getHeaders()
    //         });
    //
    //         $('#userName').text(response.name || 'User');
    //         $('#userRole').text(response.role_display || response.role || 'User');
    //
    //         // Store user info
    //         Utils.storage.set('user_role', response.role);
    //         Utils.storage.set('user_name', response.name);
    //         Utils.storage.set('user_id', response.id);
    //
    //     } catch (error) {
    //         console.error('Failed to load user info:', error);
    //
    //         // If unauthorized, redirect to login
    //         if (error.status === 401) {
    //             const orgCode = Utils.storage.get('org_code');
    //             Utils.storage.clear();  // Clear invalid session data
    //             window.location.href = orgCode ? `/${orgCode}/login/` : '/';
    //         }
    //     }
    // },

    /**
     * Setup sidebar toggle for mobile
     */
    setupSidebarToggle: function() {
        $('#mobileSidebarToggle, #sidebarToggle').on('click', function() {
            $('#sidebar').toggleClass('active');
            $('#sidebarOverlay').toggleClass('active');
        });

        $('#sidebarOverlay').on('click', function() {
            $('#sidebar').removeClass('active');
            $(this).removeClass('active');
        });

        // Close sidebar on window resize
        $(window).on('resize', function() {
            if ($(window).width() > 991) {
                $('#sidebar').removeClass('active');
                $('#sidebarOverlay').removeClass('active');
            }
        });
    },

    /**
     * Setup navigation active states
     */
    setupNavigation: function() {
        // Get current page from URL
        const currentPath = window.location.pathname;

        // Remove active class from all links
        $('.nav-link').removeClass('active');

        // Add active class to current page
        $(`.nav-link[href="${currentPath}"]`).addClass('active');

        // Handle navigation clicks
        $('.nav-link').on('click', function(e) {
            // Don't prevent default - let normal navigation work
            // But update active state
            $('.nav-link').removeClass('active');
            $(this).addClass('active');

            // Close mobile sidebar
            if ($(window).width() <= 991) {
                $('#sidebar').removeClass('active');
                $('#sidebarOverlay').removeClass('active');
            }
        });
    },

    /**
     * Setup logout functionality
     */
    setupLogout: function() {
        $('#logoutBtn').on('click', async function() {
            Utils.confirm('Are you sure you want to logout?', async function() {
                Utils.showLoader();

                // Get org_code before clearing storage
                const orgCode = Utils.storage.get('org_code');

                try {
                    await $.ajax({
                        url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.AUTH.LOGOUT),
                        method: 'POST',
                        headers: API_CONFIG.getHeaders()
                    });
                } catch (error) {
                    console.error('Logout error:', error);
                } finally {
                    // Clear local storage (this removes token + all user data)
                    Utils.storage.clear();

                    // Redirect to org-specific login page
                    window.location.href = orgCode ? `/${orgCode}/login/` : '/';
                }
            });
        });
    },

    /**
     * Update pending registrations count
     */
    updatePendingCount: async function() {
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.DASHBOARD.STATS),
                method: 'GET',
                headers: API_CONFIG.getHeaders()
            });

            const pendingCount = (response.pending_students || 0) + (response.pending_staff || 0);

            if (pendingCount > 0) {
                $('#pendingCount').text(pendingCount).show();
            } else {
                $('#pendingCount').hide();
            }

        } catch (error) {
            console.error('Failed to load pending count:', error);
        }
    },

    /**
     * Filter menu items based on user role
     */
    filterMenuByRole: function() {
        const userRole = Utils.storage.get('user_role');

        if (!userRole) {
            return;
        }

        // Show/hide menu items based on role
        if (userRole === 'admin') {
            // Admin sees everything
            $('.nav-item').show();
        } else if (userRole === 'head_teacher') {
            // Head teacher doesn't see admin-only items
            $('.nav-item.admin-only').hide();
            $('.nav-item.head-teacher-only').show();
        } else if (userRole === 'teacher') {
            // Teacher only sees basic items
            $('.nav-item').hide();
            $('.nav-item:not(.admin-only):not(.head-teacher-only)').show();
        }
    },

    /**
     * Update page title
     */
    updatePageTitle: function(title) {
        $('#pageTitle').text(title);
        document.title = `${title} - Kerala Islamic Centre`;
    }
};

/**
 * Export for use in other files
 */
window.Layout = Layout;