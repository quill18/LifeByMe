// ./static/js/utils.js

// Form validation utilities
const ValidationUtils = {
    isAlphanumeric: (str) => /^[a-zA-Z0-9]+$/.test(str),
    
    showError: (element, message) => {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        element.parentNode.appendChild(errorDiv);
        element.classList.add('error');
    },

    clearErrors: (form) => {
        form.querySelectorAll('.field-error').forEach(error => error.remove());
        form.querySelectorAll('.error').forEach(field => field.classList.remove('error'));
    },

    addFormValidation: (formId, validationRules) => {
        const form = document.getElementById(formId);
        if (!form) return;

        form.addEventListener('submit', (e) => {
            ValidationUtils.clearErrors(form);
            let isValid = true;

            for (const [fieldId, rules] of Object.entries(validationRules)) {
                const field = document.getElementById(fieldId);
                if (!field) continue;

                for (const rule of rules) {
                    const validationResult = rule(field);
                    if (validationResult !== true) {
                        isValid = false;
                        ValidationUtils.showError(field, validationResult);
                        break;
                    }
                }
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    }
};

// Common validation rules
const ValidationRules = {
    required: (field) => {
        return field.value.trim() ? true : 'This field is required';
    },

    alphanumeric: (field) => {
        return ValidationUtils.isAlphanumeric(field.value.trim()) ? 
            true : 'Only letters and numbers are allowed';
    },

    minLength: (length) => {
        return (field) => {
            return field.value.length >= length ? 
                true : `Must be at least ${length} characters`;
        };
    },

    matchField: (otherFieldId) => {
        return (field) => {
            const otherField = document.getElementById(otherFieldId);
            return field.value === otherField.value ? 
                true : 'Fields do not match';
        };
    }
};

// CSRF token handling
const CSRFToken = {
    getToken: () => {
        const tokenInput = document.querySelector('input[name="csrf_token"]');
        return tokenInput ? tokenInput.value : null;
    },

    addTokenToHeaders: (headers = {}) => {
        const token = CSRFToken.getToken();
        if (token) {
            headers['X-CSRFToken'] = token;
        }
        return headers;
    }
};