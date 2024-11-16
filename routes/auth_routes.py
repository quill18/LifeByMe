# ./routes/auth_routes.py

from flask import Blueprint, request, render_template, redirect, url_for, session
from flask_wtf.csrf import generate_csrf
import secrets
from models.user import User
from models.session import Session
from .auth_decorator import login_required
from config import Config  # Add this import
import logging
from datetime import datetime
from typing import List, Optional, Tuple
import traceback

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def get_client_ip() -> str:
    """Get client IP address with proxy support"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def validate_credentials(username: str, password: str) -> Tuple[List[str], Optional[User]]:
    """Validate login credentials and return (errors, user)"""
    errors = []
    user = None
    
    if not username or not password:
        errors.append('Username and password are required')
        return errors, None
    
    user = User.get_by_username(username)
    if not user or not user.verify_password(password):
        errors.append('Invalid username or password')
        return errors, None
        
    return errors, user

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if already logged in
    if session.get('session_id'):
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('login.html')

    errors = []
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    errors, user = validate_credentials(username, password)
    if errors:
        return render_template('login.html', errors=errors)

    try:
        ip_address = get_client_ip()
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        Session.create(session_id, user._id, ip_address)
        session['session_id'] = session_id
        
        # Update user login info
        user.update_login(ip_address)
        
        logger.info(f"Successful login for user {username} from IP {ip_address}")
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        errors.append('An error occurred during login')
        return render_template('login.html', errors=errors)

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    try:
        session_id = session.get('session_id')
        if session_id:
            db_session = Session.get_by_session_id(session_id)
            if db_session:
                db_session.delete()
        session.clear()
        logger.info(f"User logged out, session {session_id}")
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
    return redirect(url_for('auth.login'))

def validate_registration(username: str, password: str, password_confirm: str) -> List[str]:
    """Validate registration data and return list of errors"""
    errors = []
    
    if not username or not password:
        errors.append('Username and password are required')
    
    if not username.isalnum():
        errors.append('Username must contain only letters and numbers')
        
    if len(password) < Config.MIN_PASSWORD_LENGTH:
        errors.append(f'Password must be at least {Config.MIN_PASSWORD_LENGTH} characters')
        
    if password != password_confirm:
        errors.append('Passwords do not match')
        
    return errors

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect if already logged in
    if session.get('session_id'):
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('register.html', csrf_token=generate_csrf())

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    password_confirm = request.form.get('password_confirm', '').strip()
    openai_api_key = request.form.get('openai_api_key', '').strip() or None

    gpt_model = request.form.get('gpt_model', '').strip()
    custom_model = request.form.get('custom_model', '').strip()
    final_model = custom_model if gpt_model == 'custom' else gpt_model

    errors = validate_registration(username, password, password_confirm)
    if errors:
        return render_template('register.html', errors=errors, csrf_token=generate_csrf())

    try:
        ip_address = get_client_ip()
        user = User.create(username, password, openai_api_key, ip_address, gpt_model=final_model)
        logger.info(f"New user registered: {username} from IP {ip_address}")
        
        # Auto-login after registration
        session_id = secrets.token_urlsafe(32)
        Session.create(session_id, user._id, ip_address)
        session['session_id'] = session_id
        
        return redirect(url_for('index'))
        
    except ValueError as e:
        errors.append(str(e))
        return render_template('register.html', errors=errors, csrf_token=generate_csrf())
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}\n{traceback.format_exc()}")
        errors.append('An error occurred during registration')
        return render_template('register.html', errors=errors, csrf_token=generate_csrf())