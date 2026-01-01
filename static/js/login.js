/**
 * Login Page JavaScript
 */

$(document).ready(function() {
    // Check if already logged in
    if (Utils.storage.get('auth_token')) {
        window.location.href = '/dashboard';
        return;
    }

    // Handle login form submission
    $('#loginForm').on('submit', async function(e) {
        e.preventDefault();

        const email = $('#email').val();
        const password = $('#password').val();
        const remember = $('#rememberMe').is(':checked');

        Utils.showLoader();

        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.AUTH.LOGIN),
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                data: JSON.stringify({
                    email: email,
                    password: password,
                    remember: remember
                })
            });

            // Store auth token
            Utils.storage.set('auth_token', response.token);
            Utils.storage.set('user_role', response.user.role);
            Utils.storage.set('user_name', response.user.name);
            Utils.storage.set('user_id', response.user.id);

            Utils.showToast('Login successful! Redirecting...', 'success');

            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);

        } catch (error) {
            Utils.hideLoader();

            let message = 'Login failed. Please try again.';
            if (error.responseJSON && error.responseJSON.message) {
                message = error.responseJSON.message;
            } else if (error.status === 401) {
                message = 'Invalid email or password.';
            }

            Utils.showToast(message, 'error');
        }
    });

    // Handle forgot password
    $('#forgotPasswordLink').on('click', function(e) {
        e.preventDefault();

        Modal.show({
            title: 'Forgot Password',
            body: `
                <p class="mb-3">Enter your email address and we'll send you instructions to reset your password.</p>
                <form id="forgotPasswordForm">
                    <div class="mb-3">
                        <label for="resetEmail" class="form-label">Email Address</label>
                        <input type="email" class="form-control" id="resetEmail" 
                               name="email" required placeholder="Enter your email">
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
                    label: 'Send Reset Link',
                    class: 'btn-primary',
                    onClick: async () => {
                        const email = $('#resetEmail').val();

                        if (!Utils.isValidEmail(email)) {
                            Utils.showToast('Please enter a valid email address', 'error');
                            return;
                        }

                        Utils.showLoader();

                        try {
                            await $.ajax({
                                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.AUTH.FORGOT_PASSWORD),
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                data: JSON.stringify({ email: email })
                            });

                            Modal.hide();
                            Utils.hideLoader();
                            Utils.showToast('Password reset link sent to your email', 'success');

                        } catch (error) {
                            Utils.hideLoader();
                            Utils.showToast('Failed to send reset link. Please try again.', 'error');
                        }
                    }
                }
            ]
        });
    });
});