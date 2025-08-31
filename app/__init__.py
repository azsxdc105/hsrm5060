from flask import Flask, render_template, request, g, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user, logout_user
from flask_mail import Mail
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_caching import Cache
from config import config
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
babel = Babel()
csrf = CSRFProtect()
jwt = JWTManager()
cors = CORS()
cache = Cache()

def create_app(config_name=None):
    app = Flask(__name__)
    
    config_name = config_name or os.environ.get('APP_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        },
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })

    # Initialize cache
    cache.init_app(app)

    # Setup performance monitoring (simplified)
    # from app.performance import performance_monitor

    @app.before_request
    def before_request():
        from flask import g
        import time
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        from flask import g, request
        from app.security import security_headers
        import time

        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            # performance_monitor.record_request_time(request.endpoint or 'unknown', duration)

            # Add performance headers
            response.headers['X-Response-Time'] = f"{duration:.3f}s"

        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response

    # Setup enhanced security monitoring
    from app.security_manager_simple import SecurityManager

    @app.before_request
    def security_middleware():
        """Enhanced security middleware for all requests"""
        # Skip security checks for static files
        if request.endpoint and request.endpoint.startswith('static'):
            return

        # Check if IP is blocked
        if SecurityManager.is_ip_blocked():
            return jsonify({'error': 'Access denied'}), 403

        # Rate limiting
        if SecurityManager.is_rate_limited():
            return jsonify({'error': 'Rate limit exceeded'}), 429

        # Validate session security for authenticated users
        if current_user.is_authenticated:
            if not SecurityManager.validate_session_security():
                logout_user()
                return redirect(url_for('auth.login'))

        # Check for suspicious input in form data
        if request.form:
            for key, value in request.form.items():
                if SecurityManager.detect_suspicious_input(value):
                    SecurityManager.log_security_event(
                        'malicious_input_blocked',
                        f'Blocked suspicious input in form field: {key}',
                        severity='high'
                    )
                    return jsonify({'error': 'Invalid input detected'}), 400
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
    login_manager.login_message_category = 'info'
    
    # Create upload folder (with error handling for production)
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    try:
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
    except Exception as e:
        app.logger.warning(f"Could not create upload folder {upload_folder}: {e}")

    # Create backup folder (with error handling for production)
    backup_folder = app.config.get('BACKUP_FOLDER', 'backups')
    try:
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder, exist_ok=True)
    except Exception as e:
        app.logger.warning(f"Could not create backup folder {backup_folder}: {e}")
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.claims import claims_bp
    from app.routes.admin import admin_bp
    from app.routes.notifications_simple import notifications_bp
    from app.routes.advanced_notifications import advanced_notifications_bp
    from app.routes.ai_classification import ai_classification_bp
    from app.routes.payments_full import payments_bp
    from app.routes.reports import reports_bp
    from app.routes.file_upload import file_upload_bp
    from app.routes.two_factor import two_factor_bp
    from app.routes.dynamic_forms import dynamic_forms_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(claims_bp, url_prefix='/claims')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(advanced_notifications_bp, url_prefix='/advanced-notifications')
    app.register_blueprint(ai_classification_bp, url_prefix='/ai-classification')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(reports_bp, url_prefix='/reports')  # Reports blueprint
    app.register_blueprint(file_upload_bp, url_prefix='/file-upload')  # File upload blueprint
    app.register_blueprint(two_factor_bp, url_prefix='/2fa')  # Two-factor authentication blueprint
    app.register_blueprint(dynamic_forms_bp)  # Dynamic forms blueprint
    app.register_blueprint(api_bp)  # API blueprint with /api/v1 prefix

    # Add standalone routes
    @app.route('/profile')
    @login_required
    def profile():
        """User profile page"""
        return render_template('main/profile.html')
    
    # Configure Babel locale selector
    def get_locale():
        from flask import request, session
        # Check if user manually selected language
        if 'language' in session:
            return session['language']
        # Check Accept-Language header
        return request.accept_languages.best_match(['ar', 'en']) or 'ar'
    
    babel.init_app(app, locale_selector=get_locale)
    
    return app