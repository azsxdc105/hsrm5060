import os
from dotenv import load_dotenv

load_dotenv()

class RenderConfig:
    """Configuration for Render.com deployment"""
    
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'render-production-secret-key-2024'
    
    # Database Configuration - Render provides PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///claims.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Production settings
    DEBUG = False
    DEVELOPMENT = False
    TESTING = False
    FLASK_ENV = 'production'
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB
    UPLOAD_FOLDER = '/tmp/uploads'  # Render uses /tmp for temporary files
    BACKUP_FOLDER = '/tmp/backups'
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}
    
    # Security Settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Disable features that require local files in production
    AI_ENABLED = False  # Disable AI features for now
    OCR_ENABLED = False  # Disable OCR for now
    SMS_ENABLED = False  # Can be enabled with proper Twilio config
    WHATSAPP_ENABLED = False  # Can be enabled with proper WhatsApp config
    
    # Cache Configuration - Use simple cache for free tier
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days
    
    # Notifications
    NOTIFICATIONS_ENABLED = True
    PUSH_NOTIFICATIONS_ENABLED = False
    
    # Languages
    LANGUAGES = ['ar', 'en']
    DEFAULT_LANGUAGE = 'ar'
    
    # Admin Configuration
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@claims.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')