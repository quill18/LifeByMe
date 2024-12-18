// ./static/js/game.js

// Initialize story scroll functionality
function initializeStoryScroll() {
    const storyScroll = document.querySelector('.story-scroll');
    if (storyScroll) {
        storyScroll.scrollTop = storyScroll.scrollHeight;
    }
}

// Initialize customize story form
function initializeCustomizeForm() {
    const customizeToggle = document.querySelector('.customize-toggle');
    const customizeForm = document.querySelector('.customize-form');
    
    if (customizeToggle && customizeForm) {
        customizeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            customizeForm.style.display = customizeForm.style.display === 'none' ? 'block' : 'none';
            customizeToggle.textContent = customizeForm.style.display === 'none' ? '⚙ Customize' : '✕ Hide';
        });
    }
}

// Initialize sliding panels functionality
function initializePanels() {
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
    
    // Setup action buttons
    actionButtons.forEach(button => {
        button.addEventListener('click', () => {
            const panelId = `${button.dataset.panel}-panel`;
            const panel = document.getElementById(panelId);
            
            closeAllPanels();
            
            if (panel) {
                panel.classList.add('active');
                overlay.classList.add('active');
                
                switch (button.dataset.panel) {
                    case 'traits': loadTraits(); break;
                    case 'memories': loadMemories(); break;
                    case 'characters': loadCharacters(); break;
                }
            }
        });
    });
    
    // Setup close buttons
    closeButtons.forEach(button => button.addEventListener('click', closeAllPanels));
    overlay.addEventListener('click', closeAllPanels);
    
    // Setup escape key handler
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeAllPanels();
    });
}

// Initialize story control buttons
function initializeStoryControls() {
    const centerColumn = document.querySelector('.center-column');
    if (!centerColumn) return;

    // Use event delegation for story controls
    centerColumn.addEventListener('click', async (e) => {
        // Handle Start/New Story button
        if (e.target.matches('.start-story-button, .story-complete .new-story-button')) {
            e.preventDefault();
            await handleNewStory();
        }
        
        // Handle Story option buttons
        if (e.target.matches('.story-option')) {
            await handleStoryChoice(e.target);
        }
    });
}

// Story management functions
async function deleteStory(storyId) {
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
        
        location.reload();
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting story. Please try again.');
    }
}

async function makeMemory(storyId, buttonContainer) {
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

// Initialize story management buttons
function initializeStoryManagement() {
    const centerColumn = document.querySelector('.center-column');
    if (!centerColumn) return;

    // Use event delegation for story management buttons
    centerColumn.addEventListener('click', async (e) => {
        // Handle Delete Story button
        if (e.target.matches('.delete-story-button')) {
            if (!confirm('Are you sure you want to delete this story? This cannot be undone.')) {
                return;
            }
            await deleteStory(e.target.dataset.storyId);
        }

        // Handle Make Memory button
        if (e.target.matches('.make-memory-button')) {
            await makeMemory(e.target.dataset.storyId, e.target.parentElement);
        }
    });
}

// Main initialization
document.addEventListener('DOMContentLoaded', () => {
    initializeStoryScroll();
    initializeCustomizeForm();
    initializePanels();
    initializeStoryControls();
    initializeStoryManagement();
    StoryCustomization.initialize();
});

async function handleStoryChoice(optionButton) {
    const centerColumn = document.querySelector('.center-column');
    if (!centerColumn) return;

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
                        <span class="memory-title"><a href="/game/memory/${memory.id}">${memory.title}</a></span>
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

async function loadCharacters() {
    const panel = document.querySelector('#characters-panel');
    const loading = panel.querySelector('.loading-placeholder');
    const charactersList = panel.querySelector('.characters-list');

    try {
        const response = await fetch('/game/characters', {
            headers: {
                'X-CSRFToken': CSRFToken.getToken()
            }
        });
        
        if (!response.ok) throw new Error('Failed to load characters');
        
        const data = await response.json();
        
        if (data.characters.length === 0) {
            charactersList.innerHTML = '<div class="empty-state">No characters found.</div>';
        } else {
            // Sort characters alphabetically
            data.characters.sort((a, b) => a.name.localeCompare(b.name));
            
            charactersList.innerHTML = data.characters.map(character => `
                <div class="character-item" onclick="window.location.href='/game/character/${character.id}'">
                    <div class="character-item-info">
                        <div class="character-item-name"><a href="/game/character/${character.id}">${character.name}</a></div>
                        <div class="character-item-details">
                            <span class="character-item-age">Age ${character.age}</span> • 
                            <span class="character-item-relationship">${character.relationship_type}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        loading.style.display = 'none';
        charactersList.style.display = 'block';  // Changed from 'flex' to 'block'
        
    } catch (error) {
        console.error('Error loading characters:', error);
        loading.textContent = 'Error loading characters. Please try again.';
    }
}

async function handleNewStory() {
    try {
        const token = CSRFToken.getToken();
        if (!token) {
            throw new Error('CSRF token not found');
        }

        // Get custom story seed
        const customSeed = document.getElementById('customStorySeed')?.value.trim() || '';
        
        // Show loading state
        const centerColumn = document.querySelector('.center-column');
        centerColumn.innerHTML = '<div class="loading">Starting new story...</div>';
        
        // Make API call with custom seed
        const response = await fetch('/game/new_story', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token
            },
            body: JSON.stringify({
                custom_story_seed: customSeed
            })
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

    
// Story Customization Functions
const StoryCustomization = {
    state: {
        hasUserModifiedSeed: false,
    },

    buildStorySeed() {
        const focusCharacter = document.getElementById('focusCharacter');
        const storyTheme = document.getElementById('storyTheme');
        const customSeed = [];
        
        if (focusCharacter?.value) {
            const characterName = focusCharacter.options[focusCharacter.selectedIndex].text;
            customSeed.push(`Make sure this story focuses on ${characterName}.`);
        }
        
        if (storyTheme?.value) {
            customSeed.push(`Make sure this story focuses on a theme of ${storyTheme.value}.`);
        }
        
        return customSeed.join('\n');
    },

    warnUserAboutOverwrite() {
        return confirm('You have manually edited the story seed. Using the dropdowns will overwrite your changes. Continue?');
    },

    handleDropdownChange(event) {
        const seedTextarea = document.getElementById('customStorySeed');
        if (!seedTextarea) return;

        if (this.state.hasUserModifiedSeed && seedTextarea.value.trim()) {
            if (!this.warnUserAboutOverwrite()) {
                // Reset the dropdown to its previous value
                event.target.value = '';
                return;
            }
        }

        seedTextarea.value = this.buildStorySeed();
        this.state.hasUserModifiedSeed = false;
    },

    handleSeedInput() {
        this.state.hasUserModifiedSeed = true;
    },

    initialize() {
        const focusCharacter = document.getElementById('focusCharacter');
        const storyTheme = document.getElementById('storyTheme');
        const customSeed = document.getElementById('customStorySeed');
        
        if (focusCharacter) {
            focusCharacter.addEventListener('change', (e) => this.handleDropdownChange(e));
        }
        
        if (storyTheme) {
            storyTheme.addEventListener('change', (e) => this.handleDropdownChange(e));
        }
        
        if (customSeed) {
            customSeed.addEventListener('input', () => this.handleSeedInput());
        }
    }
};
