# ./config.py

import os
from datetime import timedelta

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key_change_in_production')
    DEBUG = True

    # MongoDB settings
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    DB_NAME = 'lifebyme'

    # Session settings
    SESSION_LIFETIME = timedelta(days=7)
    
    # Password settings (minimal for development)
    MIN_PASSWORD_LENGTH = 1

    # Logging
    LOG_FILE = 'logs/app.log'
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # API Configuration
    API_TIMEOUT = 30  # seconds

    STORIES_PER_SEASON = 5