# ./app.py

from flask import Flask, render_template, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from config import Config
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.game_routes import game_bp
from models.session import Session

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Set up logging
if not os.path.exists('logs'):
    os.mkdir('logs')

# Configure logging at the root logger level
logging.basicConfig(
    level=logging.INFO,
    format=Config.LOG_FORMAT,
    datefmt=Config.LOG_DATE_FORMAT,
    handlers=[
        # File handler with rotation
        RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=10240000,  # 10MB
            backupCount=10
        ),
        # Console handler
        logging.StreamHandler()
    ]
)

# Get the root logger
logger = logging.getLogger()

# Set the level for all loggers
logger.setLevel(logging.INFO)

# Make sure all handlers have the right formatter
formatter = logging.Formatter(
    fmt=Config.LOG_FORMAT,
    datefmt=Config.LOG_DATE_FORMAT
)

for handler in logger.handlers:
    handler.setFormatter(formatter)

app.logger.info('LifeByMe startup')

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(game_bp)

@app.before_request
def check_session():
    """Check if session is valid before each request"""
    if 'session_id' in session:
        db_session = Session.get_by_session_id(session['session_id'])
        if not db_session:
            session.clear()

@app.context_processor
def utility_processor():
    """Make certain functions available to all templates"""
    def format_datetime(dt):
        if dt:
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return ''
    
    return dict(
        format_datetime=format_datetime
    )

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html', 
                         errors=['The requested page was not found']), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {str(error)}')
    return render_template('index.html',
                         errors=['An unexpected error has occurred']), 500

def init_app(app):
    """Initialize the app with any first-time setup"""
    try:
        Session.cleanup_expired_sessions()
        app.logger.info('Cleaned up expired sessions')
    except Exception as e:
        app.logger.error(f'Error cleaning up sessions: {str(e)}')

    # Check if MongoDB is available
    from pymongo import MongoClient
    try:
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        app.logger.info('Successfully connected to MongoDB')
    except Exception as e:
        app.logger.error(f'Failed to connect to MongoDB: {str(e)}')
        raise

    # Create indexes if they don't exist
    try:
        client = MongoClient(Config.MONGO_URI)
        db = client[Config.DB_NAME]
        
        # User indexes
        db.users.create_index('username', unique=True)
        
        # Session indexes
        db.sessions.create_index('session_id', unique=True)
        db.sessions.create_index('user_id')
        db.sessions.create_index('last_accessed')
        
        app.logger.info('Database indexes verified')
    except Exception as e:
        app.logger.error(f'Failed to create database indexes: {str(e)}')
        raise

# Development server configuration
if __name__ == '__main__':
    # Initialize the app
    init_app(app)

    # Start development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )