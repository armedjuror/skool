/**
 * Student Registration Form
 * Multi-step form with real-time validation
 * Kerala Islamic Centre - Madrassa Management System
 */

$(document).ready(function() {
    StudentRegistration.init();
});

const StudentRegistration = {
    currentStep: 1,
    totalSteps: 5,
    formData: {},
    photoFile: null,

    init: function() {
        this.loadInitialData();
        this.attachEventListeners();
        this.updateProgressBar();
    },

    loadInitialData: async function() {
        Utils.showLoader();

        try {
            // Load branches
            await this.loadBranches();

            // Load classes
            await this.loadClasses();

        } catch (error) {
            console.error('Error loading initial data:', error);
            Utils.showToast('Failed to load form data. Please refresh the page.', 'error');
        } finally {
            Utils.hideLoader();
        }
    },

    loadBranches: async function() {
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.BRANCHES)+`?org_code=${ORG_CODE}`,
                method: 'GET'
            });

            const branches = response.results || response.data || response;
            const branchSelect = $('#branch');

            // Clear existing options except the first one
            branchSelect.find('option:not(:first)').remove();

            // Add branches from API
            if (Array.isArray(branches) && branches.length > 0) {
                branches.forEach(branch => {
                    const branchName = branch.name || branch.branch_name || branch;
                    const branchId = branch.id || branchName;
                    branchSelect.append(`<option value="${branchId}">${branchName}</option>`);
                });
                console.log(`✓ Loaded ${branches.length} branches from API`);
            } else {
                console.warn('No branches returned from API, using default list');
            }

        } catch (error) {
            console.error('Error loading branches:', error);
        }
    },

    loadClasses: async function() {
        try {
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.UTILITIES.CLASSES)+`?org_code=${ORG_CODE}`,
                method: 'GET'
            });

            const classes = response.results || response.data || response;
            const classSelect = $('#class_admitted');
            const completedClassSelect = $('#completed_classes');

            // Clear existing options except the first one
            classSelect.find('option:not(:first)').remove();
            completedClassSelect.find('option:not(:first)').remove();

            // Add classes from API
            if (Array.isArray(classes) && classes.length > 0) {
                classes.forEach(cls => {
                    const className = cls.name || cls.class_name || cls;
                    const classId = cls.id || className;
                    const displayName = cls.display_name || `Class ${className}`;

                    classSelect.append(`<option value="${classId}">${displayName}</option>`);
                    completedClassSelect.append(`<option value="${classId}">${displayName}</option>`);
                });
                console.log(`✓ Loaded ${classes.length} classes from API`);
            } else {
                console.warn('No classes returned from API, using default list');
            }

        } catch (error) {
            console.error('Error loading classes:', error);
            console.warn('Falling back to default class list');
        }
    },


    attachEventListeners: function() {
        const self = this;

        // Navigation buttons
        $('#nextBtn').on('click', function() {
            self.nextStep();
        });

        $('#prevBtn').on('click', function() {
            self.prevStep();
        });

        // Form submission
        $('#studentRegistrationForm').on('submit', function(e) {
            e.preventDefault();
            self.submitForm();
        });

        // Photo upload
        $('#photoPreviewBox').on('click', function() {
            $('#student_photo').click();
        });

        $('#student_photo').on('change', function(e) {
            self.handlePhotoUpload(e);
        });

        // Age calculation on DOB change
        $('#date_of_birth').on('change', function() {
            self.calculateAge();
        });

        // Real-time validation for all inputs
        $('#studentRegistrationForm input, #studentRegistrationForm select, #studentRegistrationForm textarea').on('blur', function() {
            self.validateField($(this));
        });

        // Real-time validation on input for better UX
        $('#studentRegistrationForm input[type="email"]').on('input', function() {
            self.validateEmail($(this));
        });

        $('#studentRegistrationForm input[type="tel"]').on('input', function() {
            self.validatePhone($(this));
        });

        // Study type and ID card type dependency
        $('#study_type').on('change', function() {
            const studyType = $(this).val();
            const idCardType = $('#id_card_type');

            if (studyType === 'Permanent') {
                idCardType.val('QID');
            } else if (studyType === 'Temporary') {
                idCardType.val('Passport');
            }
        });
    },

    nextStep: function() {
        // Validate current section before moving to next
        if (this.validateSection(this.currentStep)) {
            // Hide current section
            $(`.form-section[data-section="${this.currentStep}"]`).removeClass('active');

            // Mark current step as completed
            $(`.progress-step[data-step="${this.currentStep}"]`).addClass('completed');

            // Move to next step
            this.currentStep++;

            // Show next section
            $(`.form-section[data-section="${this.currentStep}"]`).addClass('active');

            // Mark next step as active
            $(`.progress-step[data-step="${this.currentStep}"]`).addClass('active');

            // Update UI
            this.updateProgressBar();
            this.updateNavigationButtons();

            // Scroll to top
            this.scrollToTop();
        }
    },

    prevStep: function() {
        // Hide current section
        $(`.form-section[data-section="${this.currentStep}"]`).removeClass('active');

        // Remove active from current step
        $(`.progress-step[data-step="${this.currentStep}"]`).removeClass('active');

        // Move to previous step
        this.currentStep--;

        // Show previous section
        $(`.form-section[data-section="${this.currentStep}"]`).addClass('active');

        // Remove completed from previous step (allow editing)
        $(`.progress-step[data-step="${this.currentStep}"]`).removeClass('completed');

        // Update UI
        this.updateProgressBar();
        this.updateNavigationButtons();

        // Scroll to top
        this.scrollToTop();
    },

    validateSection: function(step) {
        const section = $(`.form-section[data-section="${step}"]`);
        let isValid = true;

        // Get all required fields in this section
        section.find('input[required], select[required], textarea[required]').each(function() {
            const field = $(this);

            // Special handling for file input
            if (field.attr('type') === 'file') {
                if (!StudentRegistration.photoFile) {
                    field.addClass('is-invalid');
                    isValid = false;
                } else {
                    field.removeClass('is-invalid').addClass('is-valid');
                }
            } else if (!StudentRegistration.validateField(field)) {
                isValid = false;
            }
        });

        if (!isValid) {
            Utils.showToast('Please fill all required fields correctly', 'warning');
        }

        return isValid;
    },

    validateField: function(field) {
        const value = field.val().trim();
        const fieldType = field.attr('type');
        const fieldName = field.attr('name');

        // Skip validation for readonly fields
        if (field.prop('readonly')) {
            return true;
        }

        // Required field validation
        if (field.prop('required') && !value) {
            field.removeClass('is-valid').addClass('is-invalid');
            return false;
        }

        // Email validation
        if (fieldType === 'email' && value) {
            return this.validateEmail(field);
        }

        // Phone validation
        if (fieldType === 'tel' && value) {
            return this.validatePhone(field);
        }

        // Pattern validation
        if (field.attr('pattern') && value) {
            const pattern = new RegExp(field.attr('pattern'));
            if (!pattern.test(value)) {
                field.removeClass('is-valid').addClass('is-invalid');
                return false;
            }
        }

        // Date validation (not in future for DOB)
        if (fieldName === 'date_of_birth' && value) {
            const selectedDate = new Date(value);
            const today = new Date();
            if (selectedDate > today) {
                field.removeClass('is-valid').addClass('is-invalid');
                return false;
            }
        }

        // If field passes all validations
        if (value) {
            field.removeClass('is-invalid').addClass('is-valid');
        }
        return true;
    },

    validateEmail: function(field) {
        const email = field.val().trim();
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (email && !emailPattern.test(email)) {
            field.removeClass('is-valid').addClass('is-invalid');
            return false;
        }

        if (email) {
            field.removeClass('is-invalid').addClass('is-valid');
        }
        return true;
    },

    validatePhone: function(field) {
        const phone = field.val().trim();
        const phonePattern = /^[0-9]{8,15}$/;

        if (phone && !phonePattern.test(phone)) {
            field.removeClass('is-valid').addClass('is-invalid');
            return false;
        }

        if (phone) {
            field.removeClass('is-invalid').addClass('is-valid');
        }
        return true;
    },

    calculateAge: function() {
        const dob = $('#date_of_birth').val();
        if (dob) {
            const birthDate = new Date(dob);
            const today = new Date();
            let age = today.getFullYear() - birthDate.getFullYear();
            const monthDiff = today.getMonth() - birthDate.getMonth();

            if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
                age--;
            }

            $('#age').val(age + ' years');
        }
    },

    handlePhotoUpload: function(e) {
        const file = e.target.files[0];

        if (file) {
            // Validate file type
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                Utils.showToast('Please upload a JPG or PNG image', 'error');
                $('#student_photo').val('');
                return;
            }

            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                Utils.showToast('Image size should not exceed 5MB', 'error');
                $('#student_photo').val('');
                return;
            }

            // Store file
            this.photoFile = file;

            // Preview image
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#photoPreviewBox').html(`<img src="${e.target.result}" alt="Student Photo">`);
                $('#student_photo').removeClass('is-invalid').addClass('is-valid');
            };
            reader.readAsDataURL(file);
        }
    },

    updateProgressBar: function() {
        // Update progress line fill
        const progress = ((this.currentStep - 1) / (this.totalSteps - 1)) * 100;
        $('#progressLineFill').css('width', progress + '%');
    },

    updateNavigationButtons: function() {
        // Show/hide previous button
        if (this.currentStep === 1) {
            $('#prevBtn').hide();
        } else {
            $('#prevBtn').show();
        }

        // Show/hide next and submit buttons
        if (this.currentStep === this.totalSteps) {
            $('#nextBtn').hide();
            $('#submitBtn').show();
        } else {
            $('#nextBtn').show();
            $('#submitBtn').hide();
        }
    },

    scrollToTop: function() {
        $('html, body').animate({
            scrollTop: $('.registration-card').offset().top - 20
        }, 300);
    },

    collectFormData: function() {
        const formData = new FormData();

        // Organization code (required for API)
        formData.append('org_code', ORG_CODE);

        // Section 1: Personal Details
        // Map form values to API expected values

        formData.append('admission_type', $('#admission_type').val());
        formData.append('student_name', $('#student_name').val());
        formData.append('gender', $('#gender').val());
        formData.append('dob', $('#date_of_birth').val());
        formData.append('study_type', $('#study_type').val());
        formData.append('id_card_type', $('#id_card_type').val());
        formData.append('id_card_number', $('#id_number').val());

        // Add photo file
        if (this.photoFile) {
            formData.append('photo', this.photoFile);
        }

        // Section 2: Family Details
        formData.append('father_name', $('#father_name').val());
        formData.append('parent_mobile', $('#parent_mobile').val());
        formData.append('father_whatsapp', $('#whatsapp_number').val());
        formData.append('email', $('#email').val());
        formData.append('mother_name', $('#mother_name').val());
        formData.append('siblings_details', $('#siblings_details').val() || '');

        // Section 3: Address in Qatar (as JSON object)
        const qatarAddress = {
            place: $('#place_qatar').val() || '',
            landmark: $('#landmark').val() || '',
            building_no: $('#building_number').val() || '',
            street_no: $('#street_number').val() || '',
            zone_no: $('#zone_number').val() || ''
        };
        formData.append('qatar_address', JSON.stringify(qatarAddress));

        // Section 4: Address in India (as JSON object)
        const indiaAddress = {
            state: $('#state_india').val() || '',
            district: $('#district_india').val() || '',
            panchayath: $('#panchayath').val() || '',
            place: $('#place_india').val() || '',
            house_name: $('#house_name').val() || '',
            contact_number: $('#contact_india').val() || ''
        };
        formData.append('india_address', JSON.stringify(indiaAddress));

        // Section 5: Academic Details
        formData.append('class_to_admit', $('#class_admitted').val());
        formData.append('interested_branch', $('#branch').val());
        formData.append('completed_classes', $('#completed_classes').val() || '');
        formData.append('previous_madrasa', $('#previous_madrasa').val() || '');
        formData.append('tc_number', $('#tc_number').val() || '');
        formData.append('aadhar_number', $('#aadhar_number').val() || '');

        return formData;
    },

    submitForm: async function() {
        // Final validation of all sections
        let allValid = true;
        for (let i = 1; i <= this.totalSteps; i++) {
            if (!this.validateSection(i)) {
                allValid = false;

                // Navigate to first invalid section
                if (i !== this.currentStep) {
                    // Reset to invalid section
                    $(`.form-section[data-section="${this.currentStep}"]`).removeClass('active');
                    $(`.progress-step[data-step="${this.currentStep}"]`).removeClass('active');

                    this.currentStep = i;

                    $(`.form-section[data-section="${this.currentStep}"]`).addClass('active');
                    $(`.progress-step[data-step="${this.currentStep}"]`).addClass('active');

                    this.updateProgressBar();
                    this.updateNavigationButtons();
                    this.scrollToTop();
                }
                break;
            }
        }

        if (!allValid) {
            Utils.showToast('Please complete all required fields correctly', 'error');
            return;
        }

        // Show loading
        Utils.showLoader();
        $('#submitBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i> Submitting...');

        try {
            // Collect form data
            const formData = this.collectFormData();

            // Make API call
            const response = await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.REGISTRATION.STUDENT.SUBMIT),
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    // Don't include auth headers for public registration
                }
            });

            // Hide form, show success message
            $('#studentRegistrationForm').hide();
            $('.progress-container').hide();
            $('#successContainer').fadeIn();

            // Scroll to success message
            $('html, body').animate({
                scrollTop: $('#successContainer').offset().top - 100
            }, 500);

        } catch (error) {
            console.error('Registration error:', error);

            let errorMessage = 'Registration failed. Please try again.';

            if (error.responseJSON) {
                if (error.responseJSON.message) {
                    errorMessage = error.responseJSON.message;
                } else if (error.responseJSON.errors) {
                    // Display field-specific errors
                    const errors = error.responseJSON.errors;
                    const firstError = Object.values(errors)[0];
                    errorMessage = Array.isArray(firstError) ? firstError[0] : firstError;
                }
            }

            Utils.showToast(errorMessage, 'error');

        } finally {
            Utils.hideLoader();
            $('#submitBtn').prop('disabled', false).html('<i class="fas fa-paper-plane me-2"></i> Submit Application');
        }
    }
};

