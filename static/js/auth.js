// ./static/js/auth.js

document.addEventListener('DOMContentLoaded', () => {
    // Login form validation
    ValidationUtils.addFormValidation('loginForm', {
        'username': [
            ValidationRules.required,
            ValidationRules.alphanumeric
        ],
        'password': [
            ValidationRules.required
        ]
    });

    // Registration form validation
    ValidationUtils.addFormValidation('registerForm', {
        'username': [
            ValidationRules.required,
            ValidationRules.alphanumeric
        ],
        'password': [
            ValidationRules.required,
            ValidationRules.minLength(1) // Minimum length from config
        ],
        'password_confirm': [
            ValidationRules.required,
            ValidationRules.matchField('password')
        ]
    });

    // Optional API key validation (only if provided)
    const apiKeyField = document.getElementById('openai_api_key');
    if (apiKeyField) {
        apiKeyField.addEventListener('change', (e) => {
            ValidationUtils.clearErrors(apiKeyField.parentNode);
            const value = e.target.value.trim();
            if (value && !value.startsWith('sk-')) {
                ValidationUtils.showError(apiKeyField, 'Invalid API key format');
            }
        });
    }

    // Handle navbar login form
    const navLoginForm = document.querySelector('.nav-form');
    if (navLoginForm) {
        navLoginForm.addEventListener('submit', (e) => {
            const username = navLoginForm.querySelector('input[name="username"]');
            const password = navLoginForm.querySelector('input[name="password"]');
            
            ValidationUtils.clearErrors(navLoginForm);
            let isValid = true;

            if (!username.value.trim()) {
                ValidationUtils.showError(username, 'Required');
                isValid = false;
            } else if (!ValidationUtils.isAlphanumeric(username.value.trim())) {
                ValidationUtils.showError(username, 'Invalid username');
                isValid = false;
            }

            if (!password.value) {
                ValidationUtils.showError(password, 'Required');
                isValid = false;
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    // Handle GPT model radio buttons
    const modelRadios = document.querySelectorAll('input[name="gpt_model"]');
    const customModelGroup = document.getElementById('customModelGroup');
    const customModel = document.getElementById('customModel');

    if (modelRadios && customModelGroup) {
        modelRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                customModelGroup.style.display = radio.value === 'custom' ? 'block' : 'none';
                customModel.required = radio.value === 'custom';
            });
        });
    }

});