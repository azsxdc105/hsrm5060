#!/usr/bin/env python3
"""
Production-ready application entry point for Render.com
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_directories():
    """Create necessary directories for production"""
    directories = ['/tmp/uploads', '/tmp/backups', '/tmp/logs']
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create directory {directory}: {e}")

def setup_logging(app):
    """Setup production logging"""
    if not app.debug and not app.testing:
        # Create logs directory
        try:
            os.makedirs('/tmp/logs', exist_ok=True)
            
            # Setup file handler
            file_handler = RotatingFileHandler(
                '/tmp/logs/app.log', 
                maxBytes=10240000, 
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Application startup')
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")

def init_database(app):
    """Initialize database for production"""
    try:
        with app.app_context():
            from app import db
            from app.models import User, InsuranceCompany
            
            # Create tables
            db.create_all()
            
            # Create default admin user if not exists
            admin_email = app.config.get('ADMIN_EMAIL', 'admin@claims.com')
            admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
            
            admin_user = User.query.filter_by(email=admin_email).first()
            if not admin_user:
                from werkzeug.security import generate_password_hash
                admin_user = User(
                    full_name='مدير النظام',
                    email=admin_email,
                    password_hash=generate_password_hash(admin_password),
                    role='admin',
                    active=True
                )
                db.session.add(admin_user)
                db.session.commit()
                app.logger.info(f'Created admin user: {admin_email}')
            
            # Create default insurance company if not exists
            if InsuranceCompany.query.count() == 0:
                default_company = InsuranceCompany(
                    name='شركة التأمين الافتراضية',
                    email='info@insurance.com',
                    phone='123456789',
                    address='الرياض، المملكة العربية السعودية'
                )
                db.session.add(default_company)
                db.session.commit()
                app.logger.info('Created default insurance company')
                
    except Exception as e:
        print(f"Database initialization error: {e}")
        app.logger.error(f'Database initialization failed: {e}')

try:
    # Create necessary directories
    create_directories()
    
    # Import and create Flask application
    from app import create_app
    
    # Determine environment
    config_name = os.environ.get('FLASK_ENV', 'production')
    if config_name == 'development':
        config_name = 'production'  # Force production for deployment
    
    # Create application
    app = create_app(config_name)
    
    # Setup logging
    setup_logging(app)
    
    # Initialize database
    init_database(app)
    
    # Log startup information
    app.logger.info(f'🚀 Application started in {config_name} mode')
    app.logger.info(f'📍 Database: {app.config.get("SQLALCHEMY_DATABASE_URI", "Unknown")[:50]}...')
    app.logger.info(f'🔐 Debug mode: {app.debug}')
    
    print("✅ Application initialized successfully!")
    
    if __name__ == '__main__':
        # Development server (not used in production)
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)

except Exception as e:
    print(f"❌ Critical error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)