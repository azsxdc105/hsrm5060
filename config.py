import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///claims.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Development settings
    DEBUG = True
    DEVELOPMENT = True
    TESTING = False

    # Flask settings
    FLASK_ENV = 'development'
    FLASK_DEBUG = True
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_MB', 25)) * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')

    # Backup Configuration
    BACKUP_FOLDER = os.environ.get('BACKUP_FOLDER', 'backups')
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}
    
    # AI Features
    AI_ENABLED = os.environ.get('AI_ENABLED', 'true').lower() in ['true', 'on', '1']
    OCR_ENABLED = os.environ.get('OCR_ENABLED', 'true').lower() in ['true', 'on', '1']

    # Google Vision API
    GOOGLE_VISION_API_KEY = os.environ.get('GOOGLE_VISION_API_KEY', 'AIzaSyAK0eL5EK8MreWpPJoniIM9ktuxyNYrx1Y')
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    # OCR Settings
    OCR_LANGUAGES = ['ar', 'en']  # Arabic and English
    OCR_CONFIDENCE_THRESHOLD = 0.7

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days

    # Cache Configuration
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))  # 5 minutes
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL') or 'redis://localhost:6379/0'

    # Notifications Configuration
    NOTIFICATIONS_ENABLED = os.environ.get('NOTIFICATIONS_ENABLED', 'true').lower() in ['true', 'on', '1']

    # SMS Configuration (Twilio)
    SMS_ENABLED = os.environ.get('SMS_ENABLED', 'false').lower() in ['true', 'on', '1']
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

    # Push Notifications
    PUSH_NOTIFICATIONS_ENABLED = os.environ.get('PUSH_NOTIFICATIONS_ENABLED', 'false').lower() in ['true', 'on', '1']

    # Notification Templates
    NOTIFICATION_TEMPLATES = {
        'claim_created': {
            'email_subject_ar': 'تم إنشاء مطالبة جديدة',
            'email_subject_en': 'New Claim Created',
            'sms_ar': 'تم إنشاء مطالبة جديدة برقم {claim_id}',
            'sms_en': 'New claim created with ID {claim_id}'
        },
        'claim_status_changed': {
            'email_subject_ar': 'تم تغيير حالة المطالبة',
            'email_subject_en': 'Claim Status Changed',
            'sms_ar': 'تم تغيير حالة المطالبة {claim_id} إلى {status}',
            'sms_en': 'Claim {claim_id} status changed to {status}'
        },
        'claim_sent': {
            'email_subject_ar': 'تم إرسال المطالبة',
            'email_subject_en': 'Claim Sent',
            'sms_ar': 'تم إرسال المطالبة {claim_id} بنجاح',
            'sms_en': 'Claim {claim_id} sent successfully'
        }
    }
    
    # Babel Configuration
    LANGUAGES = ['ar', 'en']
    DEFAULT_LANGUAGE = 'ar'
    
    # Admin Configuration
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@company.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

    # WhatsApp Configuration
    WHATSAPP_ENABLED = os.environ.get('WHATSAPP_ENABLED', 'false').lower() in ['true', 'on', '1']
    WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN')

    # Simple WhatsApp Configuration (for testing)
    SIMPLE_WHATSAPP_ENABLED = os.environ.get('SIMPLE_WHATSAPP_ENABLED', 'true').lower() in ['true', 'on', '1']
    SIMPLE_WHATSAPP_NUMBER = os.environ.get('SIMPLE_WHATSAPP_NUMBER', '+966501234567')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
    TESTING = False
    FLASK_ENV = 'production'
    FLASK_DEBUG = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database configuration for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # Disable resource-intensive features for free hosting
    AI_ENABLED = os.environ.get('AI_ENABLED', 'false').lower() in ['true', 'on', '1']
    OCR_ENABLED = os.environ.get('OCR_ENABLED', 'false').lower() in ['true', 'on', '1']
    SMS_ENABLED = os.environ.get('SMS_ENABLED', 'false').lower() in ['true', 'on', '1']
    WHATSAPP_ENABLED = os.environ.get('WHATSAPP_ENABLED', 'false').lower() in ['true', 'on', '1']
    
    # Use /tmp for file uploads in production (Render requirement)
    UPLOAD_FOLDER = '/tmp/uploads'
    BACKUP_FOLDER = '/tmp/backups'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}