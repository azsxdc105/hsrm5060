#!/usr/bin/env python3
"""
Minimal server for testing
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables to avoid issues
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = 'True'

try:
    print("🔍 Starting minimal server...")
    
    # Import Flask app with minimal configuration
    from flask import Flask, render_template, redirect, url_for, render_template_string
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager, UserMixin, login_required, current_user
    from werkzeug.security import generate_password_hash, check_password_hash
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minimal_claims.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    
    # Initialize extensions
    db = SQLAlchemy(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    
    # Simple User model
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        full_name = db.Column(db.String(120), nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(255))
        role = db.Column(db.String(20), default='admin')
        active = db.Column(db.Boolean, default=True)
        
        def set_password(self, password):
            self.password_hash = generate_password_hash(password)
        
        def check_password(self, password):
            return check_password_hash(self.password_hash, password)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return render_template_string('''
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>نظام إدارة مطالبات التأمين</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-header bg-primary text-white text-center">
                                    <h2>مرحباً بك في نظام إدارة مطالبات التأمين</h2>
                                </div>
                                <div class="card-body">
                                    <div class="alert alert-success">
                                        <h4>✅ السيرفر يعمل بنجاح!</h4>
                                        <p>مرحباً {{ current_user.full_name }}، تم تسجيل دخولك بنجاح.</p>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="card bg-light">
                                                <div class="card-body text-center">
                                                    <h5>النظام الكامل</h5>
                                                    <p>للوصول إلى النظام الكامل، يرجى إيقاف هذا السيرفر وتشغيل النظام الأساسي.</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="card bg-light">
                                                <div class="card-body text-center">
                                                    <h5>معلومات المستخدم</h5>
                                                    <p><strong>الاسم:</strong> {{ current_user.full_name }}</p>
                                                    <p><strong>البريد:</strong> {{ current_user.email }}</p>
                                                    <p><strong>الدور:</strong> {{ current_user.role }}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="text-center mt-3">
                                        <a href="/logout" class="btn btn-danger">تسجيل الخروج</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            ''')
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        from flask import request, flash
        from flask_login import login_user
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('بيانات تسجيل الدخول غير صحيحة')
        
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>تسجيل الدخول</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-primary text-white text-center">
                                <h3>تسجيل الدخول</h3>
                            </div>
                            <div class="card-body">
                                {% with messages = get_flashed_messages() %}
                                    {% if messages %}
                                        <div class="alert alert-danger">
                                            {% for message in messages %}
                                                {{ message }}
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                {% endwith %}
                                
                                <form method="POST">
                                    <div class="mb-3">
                                        <label for="email" class="form-label">البريد الإلكتروني</label>
                                        <input type="email" class="form-control" id="email" name="email" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="password" class="form-label">كلمة المرور</label>
                                        <input type="password" class="form-control" id="password" name="password" required>
                                    </div>
                                    <button type="submit" class="btn btn-primary w-100">تسجيل الدخول</button>
                                </form>
                                
                                <div class="mt-3 text-center">
                                    <small class="text-muted">
                                        البريد: admin@insurance.com<br>
                                        كلمة المرور: admin123
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''')
    
    @app.route('/logout')
    @login_required
    def logout():
        from flask_login import logout_user
        logout_user()
        return redirect(url_for('login'))
    
    # Initialize database
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(email='admin@insurance.com').first()
        if not admin:
            admin = User(
                full_name='مدير النظام',
                email='admin@insurance.com',
                role='admin',
                active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created")
        else:
            print("✅ Admin user already exists")
    
    print("\n" + "="*50)
    print("🚀 MINIMAL SERVER READY")
    print("="*50)
    print("🌐 URL: http://localhost:5000")
    print("👤 Admin Email: admin@insurance.com")
    print("🔑 Password: admin123")
    print("="*50)
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")