// ./static/js/user.js

document.addEventListener('DOMContentLoaded', () => {
    // Password change form validation
    ValidationUtils.addFormValidation('passwordForm', {
        'current_password': [
            ValidationRules.required
        ],
        'new_password': [
            ValidationRules.required,
            ValidationRules.minLength(1) // Minimum length from config
        ],
        'new_password_confirm': [
            ValidationRules.required,
            ValidationRules.matchField('new_password')
        ]
    });

    // API key form validation
    const apiKeyForm = document.getElementById('apiKeyForm');
    if (apiKeyForm) {
        apiKeyForm.addEventListener('submit', (e) => {
            const apiKeyField = document.getElementById('openai_api_key');
            ValidationUtils.clearErrors(apiKeyForm);

            const value = apiKeyField.value.trim();
            if (value && !value.startsWith('sk-')) {
                e.preventDefault();
                ValidationUtils.showError(apiKeyField, 'Invalid API key format');
            }
        });

        // Real-time API key validation
        const apiKeyField = document.getElementById('openai_api_key');
        apiKeyField.addEventListener('change', (e) => {
            ValidationUtils.clearErrors(apiKeyForm);
            const value = e.target.value.trim();
            if (value && !value.startsWith('sk-')) {
                ValidationUtils.showError(apiKeyField, 'Invalid API key format');
            }
        });
    }

    // Add confirmation for API key removal
    const apiKeyField = document.getElementById('openai_api_key');
    if (apiKeyField && apiKeyField.value) {
        apiKeyForm.addEventListener('submit', (e) => {
            if (!apiKeyField.value.trim() && !confirm('Remove API key?')) {
                e.preventDefault();
            }
        });
    }
});