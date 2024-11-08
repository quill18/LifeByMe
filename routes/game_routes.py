# ./routes/game_routes.py

from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request
from flask_wtf.csrf import generate_csrf
from models.session import Session
from models.user import User
from models.game.life import Life
from models.game.story import Story, StoryStatus
from .auth_decorator import login_required
import logging
from typing import Optional
from datetime import datetime
from bson import ObjectId
from models.game.enums import LifeStage, Intensity, Difficulty
import bleach
from typing import Tuple, List
from models.game.base import Ocean, Trait, Skill
from models.game.story_ai import begin_story, continue_story, conclude_story, generate_memory_from_story
from models.game.memory import Memory
import asyncio

game_bp = Blueprint('game', __name__)
logger = logging.getLogger(__name__)

def get_current_user() -> Optional[User]:
    """Get current user from session"""
    session_id = session.get('session_id')
    if not session_id:
        return None
    
    db_session = Session.get_by_session_id(session_id)
    if not db_session:
        return None
        
    return User.get_by_id(db_session.user_id)

def get_current_life(db_session: Session) -> Optional[Life]:
    """Get current life from session"""
    if not db_session.current_life_id:
        return None
    return Life.get_by_id(db_session.current_life_id)

@game_bp.route('/game')
@login_required
def game():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))

    db_session = Session.get_by_session_id(session['session_id'])
    current_life = get_current_life(db_session)
    
    if not current_life:
        return redirect(url_for('game.lives'))
    
    current_story = Story.get_by_life_id(current_life._id)
    
    return render_template('game/game.html',
                         user=user,
                         life=current_life,
                         story=current_story,
                         StoryStatus=StoryStatus,  # Add this line
                         csrf_token=generate_csrf())


@game_bp.route('/game/lives')
@login_required
def lives():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Get all lives for user, sorted by last_played
    lives = Life.get_by_user_id(user._id)
    lives.sort(key=lambda x: x.last_played, reverse=True)
    
    return render_template('game/lives.html',
                         user=user,
                         lives=lives,
                         csrf_token=generate_csrf())

@game_bp.route('/game/load_life/<life_id>')
@login_required
def load_life(life_id):
    try:
        user = get_current_user()
        if not user:
            logger.error("No user found in session")
            return redirect(url_for('auth.login'))
        
        life = Life.get_by_id(ObjectId(life_id))
        if not life:
            logger.error(f"Life {life_id} not found")
            return redirect(url_for('game.lives'))
            
        if life.user_id != user._id:
            logger.error(f"Life {life_id} does not belong to user {user._id}")
            return redirect(url_for('game.lives'))
        
        # Update session with new life
        db_session = Session.get_by_session_id(session['session_id'])
        if not db_session:
            logger.error("No database session found")
            return redirect(url_for('auth.login'))
        
        logger.info(f"Updating session {db_session.session_id} with life {life_id}")
        db_session.update_current_life(life._id)  
        logger.info("Successfully updated current life")
        
        return redirect(url_for('game.game'))
        
    except Exception as e:
        logger.error(f"Error in load_life: {str(e)}")
        return redirect(url_for('game.lives'))

@game_bp.route('/game/delete_life/<life_id>', methods=['POST'])
@login_required
def delete_life(life_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        life = Life.get_by_id(ObjectId(life_id))
        if not life:
            return jsonify({'success': False, 'error': 'Life not found'}), 404
            
        if life.user_id != user._id:
            return jsonify({'success': False, 'error': 'Not authorized'}), 403
        
        # Delete the life and all associated data
        life.delete()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting life: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def validate_new_life_data(form_data) -> Tuple[bool, List[str]]:
    """Validate new life form data and return (is_valid, error_messages)"""
    errors = []
    
    # Validate name
    name = bleach.clean(form_data.get('name', '').strip())
    if not name:
        errors.append('Name is required')
    elif len(name) > 50:
        errors.append('Name must be 50 characters or less')
    
    # Validate gender
    gender = form_data.get('gender')
    if not gender:
        errors.append('Gender selection is required')
    elif gender == 'Custom':
        custom_gender = bleach.clean(form_data.get('custom_gender', '').strip())
        if not custom_gender:
            errors.append('Custom gender description is required')
        elif len(custom_gender) > 50:
            errors.append('Custom gender description must be 50 characters or less')
    
    # Validate intensity
    intensity = form_data.get('intensity')
    if not intensity or not hasattr(Intensity, intensity):
        errors.append('Valid intensity selection is required')
    
    # Validate difficulty
    difficulty = form_data.get('difficulty')
    if not difficulty or not hasattr(Difficulty, difficulty):
        errors.append('Valid difficulty selection is required')
    
    # Validate custom directions (optional)
    custom_directions = bleach.clean(form_data.get('custom_directions', '').strip())
    if custom_directions and len(custom_directions) > 250:
        errors.append('Custom directions must be 250 characters or less')
    
    return (len(errors) == 0, errors)

@game_bp.route('/game/new_life', methods=['GET', 'POST'])
@login_required
def new_life():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))

    if request.method == 'GET':
        return render_template('game/new_life.html',
                             csrf_token=generate_csrf())

    # Process POST request
    form_data = {
        'name': request.form.get('name', '').strip(),
        'gender': request.form.get('gender', ''),
        'custom_gender': request.form.get('custom_gender', '').strip(),
        'intensity': request.form.get('intensity', ''),
        'difficulty': request.form.get('difficulty', ''),
        'custom_directions': request.form.get('custom_directions', '').strip()
    }
    
    is_valid, errors = validate_new_life_data(request.form)
    
    if not is_valid:
        return render_template('game/new_life.html',
                             errors=errors,
                             form_data=form_data,
                             csrf_token=generate_csrf())
    
    try:
        # Create new life
        life = Life(
            user_id=user._id,
            name=bleach.clean(form_data['name']),
            age=16,  # High School Junior
            life_stage=LifeStage.HIGH_SCHOOL,
            gender=bleach.clean(form_data['gender']),
            custom_gender=bleach.clean(form_data['custom_gender']) if form_data['gender'] == 'Custom' else None,
            intensity=Intensity[form_data['intensity']],
            difficulty=Difficulty[form_data['difficulty']],
            custom_directions=bleach.clean(form_data['custom_directions']),
            current_employment=None,
            ocean=Ocean(),
            traits=[],
            skills=[],
            current_stress=0
        )
        
        # Save to database
        life.save()
        
        # Update session with new life
        db_session = Session.get_by_session_id(session['session_id'])
        db_session.update_current_life(life._id)
        
        logger.info(f"Created new life '{life.name}' for user {user.username}")
        return redirect(url_for('game.game'))
        
    except Exception as e:
        logger.error(f"Error creating new life: {str(e)}")
        return render_template('game/new_life.html',
                             errors=['An error occurred while creating your new life'],
                             form_data=form_data,
                             csrf_token=generate_csrf())

@game_bp.route('/game/new_story', methods=['POST'])
@login_required
def new_story():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Not logged in'}), 401

        db_session = Session.get_by_session_id(session['session_id'])
        current_life = get_current_life(db_session)
        if not current_life:
            return jsonify({'error': 'No active life'}), 400

        # Check if there's an active story
        existing_story = Story.get_by_life_id(current_life._id)
        if existing_story and not existing_story.completed:
            return jsonify({'error': 'There is already an active story'}), 400

        # Get story beginning
        story_response = begin_story(current_life)

        # Create new story object
        story = Story(
            life_id=current_life._id,
            prompt="Starting new story",  # We might want to store the actual prompt later
            beats=[(story_response.story_text, None)],
            current_options=story_response.options
        )
        story.save()

        # Return rendered partial template
        return render_template('game/partials/story.html', 
                      story=story,
                      StoryStatus=StoryStatus,  # Add this line
                      csrf_token=generate_csrf())

    except Exception as e:
        import traceback
        logger.error(f"Error creating new story: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@game_bp.route('/game/story/choose', methods=['POST'])
@login_required
def choose_option():
    try:
        data = request.get_json()
        if not data or 'option_index' not in data:
            return jsonify({'error': 'Missing option index'}), 400

        user = get_current_user()
        if not user:
            return jsonify({'error': 'Not logged in'}), 401

        db_session = Session.get_by_session_id(session['session_id'])
        current_life = get_current_life(db_session)
        if not current_life:
            return jsonify({'error': 'No active life'}), 400

        # Get current story
        story = Story.get_by_life_id(current_life._id)
        if not story:
            return jsonify({'error': 'No active story'}), 400

        if story.status != StoryStatus.ACTIVE:
            return jsonify({'error': 'Story is not active'}), 400

        # Validate option index
        option_index = int(data['option_index'])
        if option_index < 0 or option_index >= len(story.current_options):
            return jsonify({'error': 'Invalid option index'}), 400

        selected_option = story.current_options[option_index]

        # Record the player's choice
        story.add_player_response(selected_option)

        # Get next story beat
        if len(story.beats) >= 2:
            story_response = conclude_story(current_life, story, selected_option)
            story.conclude_story(story_response.story_text)
        else:
            story_response = continue_story(current_life, story, selected_option)
            # Add new beat with options
            story.add_story_beat(
                story_response.story_text,
                story_response.options
            )

        print(story_response)

        # Return rendered partial template
        return render_template('game/partials/story.html', 
                             story=story,
                             StoryStatus=StoryStatus,  # Add this line
                             csrf_token=generate_csrf())

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error processing story choice: {str(e)}")
        return jsonify({'error': str(e)}), 500
    

@game_bp.route('/game/story/delete/<story_id>', methods=['POST'])
@login_required
def delete_story(story_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Not logged in'}), 401

        story = Story.get_by_id(ObjectId(story_id))
        if not story:
            return jsonify({'error': 'Story not found'}), 404

        # Verify story belongs to current life
        db_session = Session.get_by_session_id(session['session_id'])
        current_life = get_current_life(db_session)
        if not current_life or story.life_id != current_life._id:
            return jsonify({'error': 'Story not found'}), 404

        story.delete_story()
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error deleting story: {str(e)}")
        return jsonify({'error': str(e)}), 500

@game_bp.route('/game/story/make_memory/<story_id>', methods=['POST'])
@login_required
def make_memory(story_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Not logged in'}), 401

        story = Story.get_by_id(ObjectId(story_id))
        if not story:
            return jsonify({'error': 'Story not found'}), 404

        # Verify story belongs to current life
        db_session = Session.get_by_session_id(session['session_id'])
        current_life = get_current_life(db_session)
        if not current_life or story.life_id != current_life._id:
            return jsonify({'error': 'Story not found'}), 404

        if story.status != StoryStatus.CONCLUDED:
            return jsonify({'error': 'Story is not ready for memory creation'}), 400

        # Generate memory parameters
        memory_data = generate_memory_from_story(current_life, story)

        # Collect character IDs from character changes
        character_ids = []
        for char_change in memory_data.get('character_changes', []):
            char_id = ObjectId(char_change['character_id'])
            character = Character.get_by_id(char_id)
            if character and character.life_id == current_life._id:
                character_ids.append(char_id)

        # Create memory object
        memory = Memory(
            life_id=current_life._id,
            title=memory_data['title'],
            description=memory_data['description'],
            importance=memory_data['importance'],
            permanence=memory_data['permanence'],
            emotional_tags=memory_data['emotional_tags'],
            context_tags=memory_data['context_tags'],
            story_tags=memory_data['story_tags'],
            ocean_impact=Ocean.from_dict(memory_data['ocean_changes']),
            trait_impacts=[
                Trait(t['name'], t['value']) 
                for t in memory_data.get('trait_changes', [])
            ],
            skill_impacts=[
                Skill(s['name'], s['value']) 
                for s in memory_data.get('skill_changes', [])
            ],
            life_stage=current_life.life_stage,
            age_experienced=current_life.age,
            current_relevance=memory_data['importance'],  # Start with importance as relevance
            stress_impact=memory_data['stress_change'],
            character_ids=character_ids,
            source_story_id=story._id
        )
        memory.save()

        # Apply memory effects to life
        current_life.apply_memory(memory)

        # Update character relationships if any
        for char_change in memory_data.get('character_changes', []):
            char_id = ObjectId(char_change['character_id'])
            character = Character.get_by_id(char_id)
            if character and character.life_id == current_life._id:
                character.update_relationship(
                    friendship_change=char_change.get('friendship_change', 0),
                    romance_change=char_change.get('romance_change', 0),
                    conflict_change=char_change.get('conflict_change', 0)
                )
                # Add memory to character's memory list
                character.add_memory(memory._id)

        # Mark story as completed
        story.complete_with_memory(memory._id)

        # Redirect to memory view
        return jsonify({
            'success': True,
            'redirect': url_for('game.view_memory', memory_id=str(memory._id))
        })

    except Exception as e:
        logger.error(f"Error creating memory: {str(e)}")
        return jsonify({'error': str(e)}), 500

@game_bp.route('/game/memory/<memory_id>')
@login_required
def view_memory(memory_id):
    try:
        user = get_current_user()
        if not user:
            logger.error("No user found in session")
            return redirect(url_for('auth.login'))

        try:
            memory = Memory.get_by_id(ObjectId(memory_id))
        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {str(e)}\n{traceback.format_exc()}")
            return redirect(url_for('game.game'))

        if not memory:
            logger.error(f"Memory {memory_id} not found")
            return redirect(url_for('game.game'))

        # Verify memory belongs to current life
        db_session = Session.get_by_session_id(session['session_id'])
        current_life = get_current_life(db_session)
        if not current_life or memory.life_id != current_life._id:
            logger.error(f"Memory {memory_id} does not belong to current life")
            return redirect(url_for('game.game'))

        # Get associated characters
        try:
            characters = memory.get_characters()
        except Exception as e:
            logger.error(f"Error retrieving characters for memory {memory_id}: {str(e)}\n{traceback.format_exc()}")
            characters = []
        
        # Get original story if it exists
        try:
            story = Story.get_by_id(memory.source_story_id) if memory.source_story_id else None
        except Exception as e:
            logger.error(f"Error retrieving story for memory {memory_id}: {str(e)}\n{traceback.format_exc()}")
            story = None

        return render_template('game/memory.html',
                             memory=memory,
                             characters=characters,
                             story=story,
                             life=current_life,
                             user=user,
                             csrf_token=generate_csrf())

    except Exception as e:
        logger.error(f"Error viewing memory: {str(e)}\n{traceback.format_exc()}")
        #return redirect(url_for('game.game'))
