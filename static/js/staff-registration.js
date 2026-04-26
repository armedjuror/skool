/**
 * Staff Registration Form
 * Multi-step form with real-time validation
 * Kerala Islamic Centre - Madrassa Management System
 */

$(document).ready(function() {
    StaffRegistration.init();
});

const StaffRegistration = {
    currentStep: 1,
    totalSteps: 5,
    photoFile: null,
    docFiles: {
        qid_front: null,
        qid_back: null,
    },

    init: function() {
        this.attachEventListeners();
        this.updateProgressBar();
    },

    attachEventListeners: function() {
        const self = this;

        $('#nextBtn').on('click', function() { self.nextStep(); });
        $('#prevBtn').on('click', function() { self.prevStep(); });

        $('#staffRegistrationForm').on('submit', function(e) {
            e.preventDefault();
            self.submitForm();
        });

        // Photo upload
        $('#photoPreviewBox').on('click', function() { $('#staff_photo').click(); });
        $('#staff_photo').on('change', function(e) { self.handlePhotoUpload(e); });

        // QID document uploads
        $('#qid_front').on('change', function(e) {
            self.handleDocUpload(e, 'qid_front', 'qidFrontPreviewBox');
        });
        $('#qid_back').on('change', function(e) {
            self.handleDocUpload(e, 'qid_back', 'qidBackPreviewBox');
        });

        // Age calculation
        $('#date_of_birth').on('change', function() { self.calculateAge(); });

        // Real-time validation
        $('#staffRegistrationForm input, #staffRegistrationForm select, #staffRegistrationForm textarea').on('blur', function() {
            self.validateField($(this));
        });
        $('#staffRegistrationForm input[type="email"]').on('input', function() {
            self.validateEmail($(this));
        });
        $('#staffRegistrationForm input[type="tel"]').on('input', function() {
            self.validatePhone($(this));
        });
    },

    nextStep: function() {
        if (this.validateSection(this.currentStep)) {
            $(`.form-section[data-section="${this.currentStep}"]`).removeClass('active');
            $(`.progress-step[data-step="${this.currentStep}"]`).addClass('completed');
            this.currentStep++;
            $(`.form-section[data-section="${this.currentStep}"]`).addClass('active');
            $(`.progress-step[data-step="${this.currentStep}"]`).addClass('active');
            this.updateProgressBar();
            this.updateNavigationButtons();
            this.scrollToTop();
        }
    },

    prevStep: function() {
        $(`.form-section[data-section="${this.currentStep}"]`).removeClass('active');
        $(`.progress-step[data-step="${this.currentStep}"]`).removeClass('active');
        this.currentStep--;
        $(`.form-section[data-section="${this.currentStep}"]`).addClass('active');
        $(`.progress-step[data-step="${this.currentStep}"]`).removeClass('completed');
        this.updateProgressBar();
        this.updateNavigationButtons();
        this.scrollToTop();
    },

    validateSection: function(step) {
        const section = $(`.form-section[data-section="${step}"]`);
        let isValid = true;

        section.find('input[required], select[required], textarea[required]').each(function() {
            const field = $(this);

            if (field.attr('type') === 'file') {
                const fieldName = field.attr('name');
                let stored = false;
                if (fieldName === 'staff_photo') {
                    stored = !!StaffRegistration.photoFile;
                    if (!stored) $('#photoPreviewBox').css('border-color', 'var(--danger)');
                } else {
                    stored = !!StaffRegistration.docFiles[fieldName];
                    if (!stored) $('#' + (fieldName === 'qid_front' ? 'qidFrontPreviewBox' : 'qidBackPreviewBox')).addClass('is-invalid');
                }
                if (!stored) isValid = false;
            } else if (!StaffRegistration.validateField(field)) {
                isValid = false;
            }
        });

        if (!isValid) Utils.showToast('Please fill all required fields correctly', 'warning');
        return isValid;
    },

    validateField: function(field) {
        const value = field.val().trim();
        const fieldType = field.attr('type');
        const fieldName = field.attr('name');

        if (field.prop('readonly')) return true;

        if (field.prop('required') && !value) {
            field.removeClass('is-valid').addClass('is-invalid');
            return false;
        }

        if (fieldType === 'email' && value) return this.validateEmail(field);
        if (fieldType === 'tel'   && value) return this.validatePhone(field);

        if (field.attr('pattern') && value) {
            const pattern = new RegExp(field.attr('pattern'));
            if (!pattern.test(value)) {
                field.removeClass('is-valid').addClass('is-invalid');
                return false;
            }
        }

        if (fieldName === 'date_of_birth' && value) {
            if (new Date(value) > new Date()) {
                field.removeClass('is-valid').addClass('is-invalid');
                return false;
            }
        }

        if (value) field.removeClass('is-invalid').addClass('is-valid');
        return true;
    },

    validateEmail: function(field) {
        const email = field.val().trim();
        const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (email && !pattern.test(email)) {
            field.removeClass('is-valid').addClass('is-invalid');
            return false;
        }
        if (email) field.removeClass('is-invalid').addClass('is-valid');
        return true;
    },

    validatePhone: function(field) {
        const phone = field.val().trim();
        const pattern = /^[0-9]{8,15}$/;
        if (phone && !pattern.test(phone)) {
            field.removeClass('is-valid').addClass('is-invalid');
            return false;
        }
        if (phone) field.removeClass('is-invalid').addClass('is-valid');
        return true;
    },

    calculateAge: function() {
        const dob = $('#date_of_birth').val();
        if (dob) {
            const birth = new Date(dob);
            const today = new Date();
            let age = today.getFullYear() - birth.getFullYear();
            const m = today.getMonth() - birth.getMonth();
            if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
            $('#age').val(age + ' years');
        }
    },

    handlePhotoUpload: function(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
            Utils.showToast('Please upload a JPG or PNG image', 'error');
            e.target.value = '';
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            Utils.showToast('Image size should not exceed 5MB', 'error');
            e.target.value = '';
            return;
        }

        this.photoFile = file;
        const reader = new FileReader();
        reader.onload = function(ev) {
            $('#photoPreviewBox').html(`<img src="${ev.target.result}" alt="Staff Photo">`);
            $('#photoPreviewBox').css('border-color', '');
            $('#staff_photo').removeClass('is-invalid').addClass('is-valid');
        };
        reader.readAsDataURL(file);
    },

    handleDocUpload: function(e, fileKey, previewBoxId) {
        const file = e.target.files[0];
        if (!file) return;

        if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
            Utils.showToast('Please upload a JPG or PNG image', 'error');
            e.target.value = '';
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            Utils.showToast('Image size should not exceed 5MB', 'error');
            e.target.value = '';
            return;
        }

        this.docFiles[fileKey] = file;
        const reader = new FileReader();
        reader.onload = function(ev) {
            $('#' + previewBoxId).html(`<img src="${ev.target.result}" alt="${fileKey}">`);
            $('#' + previewBoxId).removeClass('is-invalid');
        };
        reader.readAsDataURL(file);
    },

    updateProgressBar: function() {
        const progress = ((this.currentStep - 1) / (this.totalSteps - 1)) * 100;
        $('#progressLineFill').css('width', progress + '%');
    },

    updateNavigationButtons: function() {
        $('#prevBtn').toggle(this.currentStep > 1);
        if (this.currentStep === this.totalSteps) {
            $('#nextBtn').hide();
            $('#submitBtn').show();
        } else {
            $('#nextBtn').show();
            $('#submitBtn').hide();
        }
    },

    scrollToTop: function() {
        $('html, body').animate({ scrollTop: $('.registration-card').offset().top - 20 }, 300);
    },

    collectFormData: function() {
        const formData = new FormData();

        formData.append('org_code', ORG_CODE);

        // Section 1: Personal
        formData.append('full_name',     $('#full_name').val());
        formData.append('gender',        $('#gender').val());
        formData.append('dob',           $('#date_of_birth').val());
        formData.append('id_card_type',  $('#id_card_type').val());
        formData.append('id_card_number', $('#id_card_number').val());
        if (this.photoFile)          formData.append('photo',     this.photoFile);
        if (this.docFiles.qid_front) formData.append('qid_front', this.docFiles.qid_front);
        if (this.docFiles.qid_back)  formData.append('qid_back',  this.docFiles.qid_back);

        // Section 2: Contact
        formData.append('mobile',    $('#mobile').val());
        formData.append('whatsapp',  $('#whatsapp').val() || '');
        formData.append('email',     $('#email').val());

        // Section 3: Qatar Address (JSON)
        formData.append('qatar_address', JSON.stringify({
            place:       $('#place_qatar').val()     || '',
            landmark:    $('#landmark').val()        || '',
            building_no: $('#building_number').val() || '',
            street_no:   $('#street_number').val()   || '',
            zone_no:     $('#zone_number').val()     || '',
        }));

        // Section 4: India Address (JSON)
        formData.append('india_address', JSON.stringify({
            state:          $('#state_india').val()    || '',
            district:       $('#district_india').val() || '',
            panchayath:     $('#panchayath').val()     || '',
            place:          $('#place_india').val()    || '',
            house_name:     $('#house_name').val()     || '',
            contact_number: $('#contact_india').val()  || '',
        }));

        // Section 5: Academic
        formData.append('religious_academic_details', $('#religious_academic_details').val() || '');
        formData.append('academic_details',           $('#academic_details').val()           || '');
        formData.append('previous_institution',       $('#previous_institution').val()       || '');
        formData.append('msr_number',                 $('#msr_number').val()                 || '');
        formData.append('aadhar_number',              $('#aadhar_number').val()              || '');

        return formData;
    },

    submitForm: async function() {
        let allValid = true;
        for (let i = 1; i <= this.totalSteps; i++) {
            if (!this.validateSection(i)) {
                allValid = false;
                if (i !== this.currentStep) {
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

        Utils.showLoader();
        $('#submitBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i> Submitting...');

        try {
            await $.ajax({
                url: API_CONFIG.getUrl(API_CONFIG.ENDPOINTS.REGISTRATION.STAFF.SUBMIT),
                method: 'POST',
                data: this.collectFormData(),
                processData: false,
                contentType: false,
            });

            $('#staffRegistrationForm').hide();
            $('#progressContainer').hide();
            $('#successContainer').fadeIn();
            $('html, body').animate({ scrollTop: $('#successContainer').offset().top - 100 }, 500);

        } catch (error) {
            console.error('Staff registration error:', error);
            let msg = 'Registration failed. Please try again.';
            if (error.responseJSON) {
                msg = error.responseJSON.message
                    || (error.responseJSON.errors && Object.values(error.responseJSON.errors)[0])
                    || msg;
                if (Array.isArray(msg)) msg = msg[0];
            }
            Utils.showToast(msg, 'error');
        } finally {
            Utils.hideLoader();
            $('#submitBtn').prop('disabled', false).html('<i class="fas fa-paper-plane me-2"></i> Submit Application');
        }
    },
};