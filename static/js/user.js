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

    // API Key visibility toggle
    const apiKeyInput = document.getElementById('openai_api_key');
    const toggleButton = document.querySelector('.toggle-visibility');
    
    if (toggleButton && apiKeyInput) {
        toggleButton.addEventListener('click', () => {
            // Toggle input type
            const isPassword = apiKeyInput.type === 'password';
            apiKeyInput.type = isPassword ? 'text' : 'password';
            
            // Toggle icon
            const eyeIcon = toggleButton.querySelector('.eye-icon');
            eyeIcon.classList.toggle('eye-closed');
            
            // Update aria-label for accessibility
            toggleButton.setAttribute('aria-label', 
                isPassword ? 'Hide API key' : 'Show API key');
        });

        // Ensure input starts as password type
        apiKeyInput.type = 'password';
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

// Add key press handler to prevent form submission when toggling visibility
document.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && event.target.classList.contains('toggle-visibility')) {
        event.preventDefault();
    }
});
