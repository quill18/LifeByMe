async function deleteLine(lifeId) {
    if (!confirm('Are you sure you want to delete this life?')) {
        return;
    }
    
    try {
        const response = await fetch(`/game/delete_life/${lifeId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const element = document.getElementById(`life-${lifeId}`);
            if (element) {
                element.remove();
            }
            
            // If no more lives, refresh to show the "Start your first life" message
            const remainingLives = document.querySelectorAll('.life-entry');
            if (remainingLives.length === 0) {
                location.reload();
            }
        } else {
            alert('Error deleting life: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting life. Please try again.');
    }
}