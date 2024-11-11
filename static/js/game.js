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

document.addEventListener('click', async (e) => {
    // Delete story button
    if (e.target.matches('.delete-story-button')) {
        if (!confirm('Are you sure you want to delete this story? This cannot be undone.')) {
            return;
        }
        
        const storyId = e.target.dataset.storyId;
        try {
            const response = await fetch(`/game/story/delete/${storyId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRFToken.getToken()
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete story');
            }
            
            // Refresh the game page
            location.reload();
            
        } catch (error) {
            console.error('Error:', error);
            alert('Error deleting story. Please try again.');
        }
    }
    
    // Make memory button
    if (e.target.matches('.make-memory-button')) {
        const storyId = e.target.dataset.storyId;
        const buttonContainer = e.target.parentElement;
        
        // Show loading state
        buttonContainer.innerHTML = '<div class="loading">Creating memory...</div>';
        
        try {
            const response = await fetch(`/game/story/make_memory/${storyId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRFToken.getToken()
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to create memory');
            }
            
            const data = await response.json();
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                location.reload();
            }
            
        } catch (error) {
            console.error('Error:', error);
            buttonContainer.innerHTML = `
                <div class="error-message">
                    Error creating memory. Please try again.
                    <button class="button primary" onclick="location.reload()">
                        Refresh
                    </button>
                </div>`;
        }
    }
});


document.addEventListener('DOMContentLoaded', () => {
    // Panel functionality
    const actionButtons = document.querySelectorAll('.action-button');
    const panels = document.querySelectorAll('.slide-panel');
    const closeButtons = document.querySelectorAll('.close-panel');
    
    // Create overlay element
    const overlay = document.createElement('div');
    overlay.className = 'panel-overlay';
    document.body.appendChild(overlay);
    
    function closeAllPanels() {
        panels.forEach(panel => panel.classList.remove('active'));
        overlay.classList.remove('active');
    }
    
    // Handle action button clicks
    actionButtons.forEach(button => {
        button.addEventListener('click', () => {
            const panelId = `${button.dataset.panel}-panel`;
            const panel = document.getElementById(panelId);
            
            // Close any open panels first
            closeAllPanels();
            
            // Open the selected panel
            if (panel) {
                panel.classList.add('active');
                overlay.classList.add('active');
                
                // Load the appropriate content
                switch (button.dataset.panel) {
                    case 'traits':
                        loadTraits();
                        break;
                    case 'skills':
                        loadSkills();
                        break;
                    case 'memories':
                        loadMemories();
                        break;
                    case 'characters':
                        // Add character loading function when implemented
                        break;
                }
            }
        });
    });
    
    // Handle close button clicks
    closeButtons.forEach(button => {
        button.addEventListener('click', closeAllPanels);
    });
    
    // Handle overlay clicks
    overlay.addEventListener('click', closeAllPanels);
    
    // Handle escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAllPanels();
        }
    });
});

// Panel content loading functions
async function loadTraits() {
    const panel = document.querySelector('#traits-panel');
    const loading = panel.querySelector('.loading-placeholder');
    const traitsList = panel.querySelector('.traits-list');

    try {
        const response = await fetch('/game/traits', {
            headers: {
                'X-CSRFToken': CSRFToken.getToken()
            }
        });
        
        if (!response.ok) throw new Error('Failed to load traits');
        
        const data = await response.json();
        
        if (data.traits.length === 0) {
            traitsList.innerHTML = '<div class="empty-state">No secondary traits developed yet.</div>';
        } else {
            traitsList.innerHTML = data.traits.map(trait => `
                <div class="trait-item">
                    <span class="trait-name">${trait.name}</span>
                    <span class="trait-value ${trait.value > 0 ? 'positive' : 'negative'}">${trait.value > 0 ? '+' : ''}${trait.value}</span>
                </div>
            `).join('');
        }
        
        loading.style.display = 'none';
        traitsList.style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading traits:', error);
        loading.textContent = 'Error loading traits. Please try again.';
    }
}

async function loadSkills() {
    const panel = document.querySelector('#skills-panel');
    const loading = panel.querySelector('.loading-placeholder');
    const skillsList = panel.querySelector('.skills-list');

    try {
        const response = await fetch('/game/skills', {
            headers: {
                'X-CSRFToken': CSRFToken.getToken()
            }
        });
        
        if (!response.ok) throw new Error('Failed to load skills');
        
        const data = await response.json();
        
        if (data.skills.length === 0) {
            skillsList.innerHTML = '<div class="empty-state">No skills learned yet.</div>';
        } else {
            skillsList.innerHTML = data.skills.map(skill => `
                <div class="skill-item">
                    <span class="skill-name">${skill.name}</span>
                    <span class="skill-value">${skill.value}</span>
                </div>
            `).join('');
        }
        
        loading.style.display = 'none';
        skillsList.style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading skills:', error);
        loading.textContent = 'Error loading skills. Please try again.';
    }
}

async function loadMemories() {
    const panel = document.querySelector('#memories-panel');
    const loading = panel.querySelector('.loading-placeholder');
    const memoriesList = panel.querySelector('.memories-list');

    try {
        const response = await fetch('/game/memories', {
            headers: {
                'X-CSRFToken': CSRFToken.getToken()
            }
        });
        
        if (!response.ok) throw new Error('Failed to load memories');
        
        const data = await response.json();
        
        if (data.memories.length === 0) {
            memoriesList.innerHTML = '<div class="empty-state">No memories yet.</div>';
        } else {
            memoriesList.innerHTML = data.memories.map(memory => `
                <div class="memory-item" onclick="window.location.href='/game/memory/${memory.id}'">
                    <div class="memory-header">
                        <span class="memory-title">${memory.title}</span>
                        <span class="memory-importance">Importance: ${memory.importance}</span>
                    </div>
                    <div class="memory-details">
                        <div class="memory-tags">
                            ${memory.emotional_tags.map(tag => 
                                `<span class="memory-tag">${tag}</span>`
                            ).join('')}
                        </div>
                        <span class="memory-age">Age ${memory.age_experienced}</span>
                    </div>
                </div>
            `).join('');
        }
        
        loading.style.display = 'none';
        memoriesList.style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading memories:', error);
        loading.textContent = 'Error loading memories. Please try again.';
    }
}
