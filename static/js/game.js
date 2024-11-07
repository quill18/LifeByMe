// ./static/js/game.js

document.addEventListener('DOMContentLoaded', () => {
    const centerColumn = document.querySelector('.center-column');
    
    // Handle "Start New Story" button click
    document.addEventListener('click', async (e) => {
        if (e.target.matches('.no-story button')) {
            try {
                const token = CSRFToken.getToken();
                if (!token) {
                    throw new Error('CSRF token not found');
                }
                console.log('Token found:', token);  // Debug log

                // Show loading state
                centerColumn.innerHTML = '<div class="loading">Starting new story...</div>';
                
                // Make API call
                const headers = {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                };
                console.log('Using headers:', headers);  // Debug log
                
                const response = await fetch('/game/new_story', {
                    method: 'POST',
                    headers: headers
                });
                
                
                const responseText = await response.text();
                
                if (!response.ok) {
                    // Try to parse error as JSON if possible
                    try {
                        const errorData = JSON.parse(responseText);
                        throw new Error(errorData.error || 'Failed to start story');
                    } catch (jsonError) {
                        // If it's not JSON, use the text directly
                        throw new Error(responseText || 'Failed to start story');
                    }
                }
                
                // Replace content with new story HTML
                centerColumn.innerHTML = responseText;
                
            } catch (error) {
                console.log(error);
                centerColumn.innerHTML = `
                    <div class="error-message">
                        ${error.message}
                        <button class="button primary" onclick="location.reload()">
                            Try Again
                        </button>
                    </div>`;
            }
        }
    });
});