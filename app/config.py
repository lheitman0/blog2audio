import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration settings for all environments"""
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///blog2audio.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cache settings
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # OpenAI API
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # TTS settings
    DEFAULT_VOICE = 'onyx'
    AVAILABLE_VOICES = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    
    # API rate limiting
    RATELIMIT_DEFAULT = "100 per day"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Audio storage
    AUDIO_UPLOAD_FOLDER = os.path.join('static', 'audio')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB limit for uploads
    
    # Text processing
    MAX_TEXT_LENGTH = 4096  # Maximum text length for TTS
    
    # User defaults
    GUEST_USER_LIMIT = 3  # Number of conversions for guests


class DevelopmentConfig(Config):
    """Development configuration settings"""
    DEBUG = True
    CACHE_TYPE = 'SimpleCache'
    SQLALCHEMY_ECHO = True
    

class TestingConfig(Config):
    """Testing configuration settings"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'


class ProductionConfig(Config):
    """Production configuration settings"""
    # Use Redis for caching in production
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.getenv('REDIS_URL')
    
    # Rate limiting with Redis in production
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL')
    
    # More restrictive file upload settings
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'html'}
    
    # Security headers
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    
    # Logging
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', 'false').lower() == 'true'