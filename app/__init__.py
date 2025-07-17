from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from config import config
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
babel = Babel()
csrf = CSRFProtect()

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
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
    login_manager.login_message_category = 'info'
    
    # Create upload folder
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.claims import claims_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(claims_bp, url_prefix='/claims')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
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