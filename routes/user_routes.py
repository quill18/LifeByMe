# ./routes/user_routes.py

from flask import Blueprint, request, render_template, redirect, url_for, session
from flask_wtf.csrf import generate_csrf
from models.user import User
from models.session import Session
from .auth_decorator import login_required
import logging
from typing import Tuple, Optional, List

user_bp = Blueprint('user', __name__)
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

def validate_password_change(current_password: str, new_password: str, 
                           new_password_confirm: str, user: User) -> List[str]:
    """Validate password change data and return list of errors"""
    errors = []
    
    if not current_password or not new_password or not new_password_confirm:
        errors.append('All password fields are required')
        return errors
        
    if not user.verify_password(current_password):
        errors.append('Current password is incorrect')
        
    if len(new_password) < Config.MIN_PASSWORD_LENGTH:
        errors.append(f'New password must be at least {Config.MIN_PASSWORD_LENGTH} characters')
        
    if new_password != new_password_confirm:
        errors.append('New passwords do not match')
        
    return errors

@user_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('settings.html', 
                         user=user, 
                         csrf_token=generate_csrf())

@user_bp.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    new_password_confirm = request.form.get('new_password_confirm', '').strip()
    
    errors = validate_password_change(current_password, new_password, 
                                    new_password_confirm, user)
    
    if errors:
        return render_template('settings.html', 
                             errors=errors, 
                             user=user, 
                             csrf_token=generate_csrf())
    
    try:
        user.change_password(new_password)
        logger.info(f"Password changed for user {user.username}")
        return render_template('settings.html', 
                             success_message='Password successfully changed', 
                             user=user,
                             csrf_token=generate_csrf())
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        errors.append('An error occurred while changing password')
        return render_template('settings.html', 
                             errors=errors, 
                             user=user,
                             csrf_token=generate_csrf())

@user_bp.route('/settings/api_key', methods=['POST'])
@login_required
def update_api_key():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    new_key = request.form.get('openai_api_key', '').strip() or None
    
    try:
        user.update_openai_key(new_key)
        logger.info(f"API key updated for user {user.username}")
        return render_template('settings.html', 
                             success_message='API key successfully updated', 
                             user=user,
                             csrf_token=generate_csrf())
    except Exception as e:
        logger.error(f"Error updating API key: {str(e)}")
        return render_template('settings.html', 
                             errors=['An error occurred while updating API key'], 
                             user=user,
                             csrf_token=generate_csrf())