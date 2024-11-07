// ./static/js/game.js

document.addEventListener('DOMContentLoaded', () => {
    const centerColumn = document.querySelector('.center-column');
    
    // Handle all button clicks in the game area
    document.addEventListener('click', async (e) => {
        // Start New Story button
        if (e.target.matches('.no-story button, .story-complete .new-story-button')) {
            await handleNewStory();
        }
        
        // Story option buttons
        if (e.target.matches('.story-option')) {
            await handleStoryChoice(e.target);
        }
    });

    async function handleNewStory() {
        try {
            const token = CSRFToken.getToken();
            if (!token) {
                throw new Error('CSRF token not found');
            }

            // Show loading state
            centerColumn.innerHTML = '<div class="loading">Starting new story...</div>';
            
            // Make API call
            const response = await fetch('/game/new_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to start story');
            }
            
            // Replace content with new story HTML
            const htmlContent = await response.text();
            centerColumn.innerHTML = htmlContent;

            // Scroll the story area to the top for new stories
            const storyScroll = document.querySelector('.story-scroll');
            if (storyScroll) {
                storyScroll.scrollTop = 0;
            }
            
        } catch (error) {
            console.error('Error starting new story:', error);
            centerColumn.innerHTML = `
                <div class="error-message">
                    ${error.message}
                    <button class="button primary" onclick="location.reload()">
                        Try Again
                    </button>
                </div>`;
        }
    }

    async function handleStoryChoice(optionButton) {
        try {
            // Disable all option buttons to prevent double-clicks
            const allOptions = document.querySelectorAll('.story-option');
            allOptions.forEach(button => {
                button.disabled = true;
                button.classList.add('disabled');
            });

            // Show loading state below the options
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = 'Processing your choice...';
            optionButton.parentElement.after(loadingDiv);

            const token = CSRFToken.getToken();
            if (!token) {
                throw new Error('CSRF token not found');
            }

            // Get the option index from the button
            const optionIndex = optionButton.dataset.option;

            // Make API call
            const response = await fetch('/game/story/choose', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                },
                body: JSON.stringify({
                    option_index: optionIndex
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to process choice');
            }

            // Replace story content with new HTML
            const htmlContent = await response.text();
            centerColumn.innerHTML = htmlContent;

            // Scroll the story area to the bottom
            const storyScroll = document.querySelector('.story-scroll');
            if (storyScroll) {
                storyScroll.scrollTop = storyScroll.scrollHeight;
            }

        } catch (error) {
            console.error('Error processing choice:', error);
            // Re-enable buttons in case of error
            const allOptions = document.querySelectorAll('.story-option');
            allOptions.forEach(button => {
                button.disabled = false;
                button.classList.remove('disabled');
            });

            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.innerHTML = `
                ${error.message}
                <button class="button primary" onclick="location.reload()">
                    Try Again
                </button>
            `;
            centerColumn.appendChild(errorDiv);
        }
    }
});