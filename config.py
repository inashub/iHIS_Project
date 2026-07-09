"""
iHIS - Intelligent Health Information System
Configuration Module
"""
import os
from datetime import timedelta

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ihis-secure-dev-key-2024-change-in-production'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'database', 'ihis.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }

    # File Uploads
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'dcm'}

    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    PASSWORD_HASH_METHOD = 'pbkdf2:sha256:600000'
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Pagination
    ITEMS_PER_PAGE = 20

    # Application Settings
    APP_NAME = 'iHIS'
    APP_FULL_NAME = 'Intelligent Health Information System'
    APP_VERSION = '1.0.0'
    HOSPITAL_NAME = 'General Hospital'
    HOSPITAL_ADDRESS = '123 Healthcare Avenue, Medical District'
    HOSPITAL_PHONE = '+1 (555) 123-4567'
    HOSPITAL_EMAIL = 'admin@ihis-health.com'

    # AI Integration (Future)
    AI_ENABLED = False
    AI_MODEL_PATH = os.path.join(BASE_DIR, 'services', 'ai', 'models')

    # FHIR/HL7 Integration (Future)
    FHIR_ENABLED = False
    HL7_ENABLED = False

    # DICOM Integration (Future)
    DICOM_ENABLED = False
    DICOM_STORAGE_PATH = os.path.join(UPLOAD_FOLDER, 'dicom')

    # Notification Settings
    EMAIL_ENABLED = False  # Set up SMTP for production
    SMS_ENABLED = False    # Set up SMS gateway for production
    ALERT_EMAIL = 'alerts@ihis-health.com'

    # Audit Log
    AUDIT_LOG_ENABLED = True
    AUDIT_LOG_RETENTION_DAYS = 2555  # 7 years for healthcare compliance

    # Timezone
    TIMEZONE = 'UTC'

    # Debug
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Set True to log SQL queries
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    # Use environment variables for all secrets in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
