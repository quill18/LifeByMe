// ./static/js/new_life.js

document.addEventListener('DOMContentLoaded', () => {
    const customDirectionsExamples = [
        "I want a life with supernatural elements and magic.",
        "I'm secretly a vampire. I have a ring that protects me from the sun.",
        "Weird and strange things happen all the time in my town.",
        "My life is a soap opera, filled with ridiculous and over-the-top drama.",
        "I want a life with a heavy focus on romance.",
        "My character comes from a devout Muslim family.",
        "My family and I just moved from Japan. It's my first time in America.",
        "My character struggles with social anxiety.",
        "My character is passionate about environmental activism.",
        "My character is interested in politics and social justice.",
        "My character is deeply involved in their local theater community.",
        "My character is passionate about technology and innovation.",
        "I want to become a renowned chef and explore culinary arts.",
        "I want to start very poor but become rich by my 30's.",
        "I want to focus on sports and athletic achievement.",
        "I want to explore artistic expression and creativity.",
        "I want to focus on family relationships and dynamics.",
        "I want to become a famous musician and deal with celebrity life.",
        //"My character is part of a close-knit immigrant community.",
        //"I want to explore themes of friendship and loyalty.",
        //"My character is dedicated to helping others.",
        //"I want to explore themes of personal growth and self-discovery.",
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
        //if (customDirections.value) return; // Don't type if user has entered text

        if (current < text.length) {
            customDirections.placeholder = text.slice(0, current + 1);
            typingTimer = setTimeout(() => typeText(text, current + 1), 50);
        } else {
            waitTimer = setTimeout(startNewExample, 1000);
        }
    }

    function startNewExample() {
        //if (customDirections.value) return; // Don't start if user has entered text

        const newExample = getRandomExample();
        currentExample = newExample;
        customDirections.placeholder = '';
        typeText(newExample);
    }

    // Start the first example
    startNewExample();

    // Clear timers if user starts typing
    /*customDirections.addEventListener('input', () => {
        if (typingTimer) clearTimeout(typingTimer);
        if (waitTimer) clearTimeout(waitTimer);
    });*/

    // Form validation
    form.addEventListener('submit', (e) => {
        let isValid = true;

        // Name validation
        if (nameInput.value.trim().length === 0) {
            isValid = false;
            ValidationUtils.showError(nameInput, 'Name is required');
        }

        // Custom gender validation
        if (genderSelect.value === 'Custom' && customGenderInput.value.trim().length === 0) {
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
        }
    });
});