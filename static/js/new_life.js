document.addEventListener('DOMContentLoaded', () => {
    const customDirectionsExamples = [
        "This world is filled with with supernatural elements and magic. [______] is a witch just learning to use their power.",
        "[______] is secretly an alien from another galaxy. They have to keep it secret from everyone!",
        "Weird and strange things happen all the time in this world and no one can explain why.",
        "This world is a soap opera, filled with ridiculous and over-the-top drama. The crazier the drama, the better!",
        "This world is all about romance, romance, romance!",
        "[______] comes from a very rich family, but tries to hide it.",
        "[______] comes from a devout Muslim family as is finding it difficult to balance their life.",
        "[______] and their family moved here from Japan not very long ago.",
    ];

    // Form elements
    const form = document.getElementById('newLifeForm');
    const genderInputs = document.querySelectorAll('input[name="gender"]');
    const customGenderGroup = document.getElementById('customGenderGroup');
    const customGenderInput = document.getElementById('customGender');
    const customDirections = document.getElementById('customDirections');
    
    // Character counters
    const nameInput = document.getElementById('name');
    const nameCount = document.getElementById('nameCount');
    const genderCount = document.getElementById('genderCount');
    const directionsCount = document.getElementById('directionsCount');

    // Handle gender selection
    genderInputs.forEach(input => {
        input.addEventListener('change', () => {
            if (input.value === 'Custom') {
                customGenderGroup.style.display = 'block';
                customGenderInput.required = true;
            } else {
                customGenderGroup.style.display = 'none';
                customGenderInput.required = false;
                customGenderInput.value = '';
            }
        });
    });
    
    // Character count updates
    function updateCount(input, display) {
        input.addEventListener('input', () => {
            display.textContent = input.value.length;
        });
    }

    updateCount(nameInput, nameCount);
    updateCount(customGenderInput, genderCount);
    updateCount(customDirections, directionsCount);

    // Custom directions placeholder animation
    let currentExample = null;
    let typingTimer = null;
    let waitTimer = null;

    function getRandomExample() {
        let newExample;
        do {
            newExample = customDirectionsExamples[
                Math.floor(Math.random() * customDirectionsExamples.length)
            ];
        } while (newExample === currentExample);
        return newExample;
    }

    function typeText(text, current = 0) {
        if (current < text.length) {
            customDirections.placeholder = text.slice(0, current + 1);
            typingTimer = setTimeout(() => typeText(text, current + 1), 50);
        } else {
            waitTimer = setTimeout(startNewExample, 1000);
        }
    }

    function startNewExample() {
        const newExample = getRandomExample();
        currentExample = newExample;
        customDirections.placeholder = '';
        typeText(newExample);
    }

    // Start the first example
    startNewExample();

    if (form) {
        form.addEventListener('submit', (e) => {
            let isValid = true;
    
            // Name validation
            if (nameInput.value.trim().length === 0) {
                isValid = false;
                ValidationUtils.showError(nameInput, 'Name is required');
            }
    
            // Custom gender validation
            if (form.querySelector('input[name="gender"]:checked')?.value === 'Custom' && 
                customGenderInput.value.trim().length === 0) {
                isValid = false;
                ValidationUtils.showError(customGenderInput, 'Custom gender description is required');
            }
    
            // Intensity validation
            if (!form.querySelector('input[name="intensity"]:checked')) {
                isValid = false;
                ValidationUtils.showError(
                    form.querySelector('.radio-group'),
                    'Please select an intensity level'
                );
            }
    
            // Difficulty validation
            if (!form.querySelector('input[name="difficulty"]:checked')) {
                isValid = false;
                ValidationUtils.showError(
                    form.querySelector('.radio-group'),
                    'Please select a difficulty level'
                );
            }
    
            if (!isValid) {
                e.preventDefault();
                return;
            }
    
            // Find just the buttons container
            const formActions = form.querySelector('.form-actions');
            if (!formActions) return;
    
            // Clear any previous error messages
            ValidationUtils.clearErrors(form);
            
            // Replace only the buttons with the loading state
            formActions.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">
                        <p>Please wait while we generate your new life...</p>
                        <p class="loading-subtext">Creating your family, teachers, and classmates...</p>
                    </div>
                </div>`;
            
            // Make text inputs readonly but NOT disabled
            form.querySelectorAll('input[type="text"], textarea').forEach(input => {
                input.readOnly = true;
            });

            // Don't disable radio buttons at all, just prevent interaction visually
            form.querySelectorAll('.radio-option, .radio-option-horizontal').forEach(option => {
                option.style.opacity = '0.7';
                option.style.pointerEvents = 'none';
            });

            // Only disable the submit and cancel buttons
            form.querySelectorAll('button[type="submit"], .button.secondary').forEach(button => {
                button.disabled = true;
            });
        });
    }
});