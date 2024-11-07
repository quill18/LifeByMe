# ./routes/auth_decorator.py

from functools import wraps
from flask import session, redirect, url_for
from models.session import Session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = session.get('session_id')
        if not session_id:
            return redirect(url_for('auth.login'))
        
        db_session = Session.get_by_session_id(session_id)
        if not db_session:
            session.clear()
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function