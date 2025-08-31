#!/usr/bin/env python3
"""
Clean application starter
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app
from app import create_app, db

# Create application
app = create_app()

# Initialize database
with app.app_context():
    try:
        db.create_all()
        
        # Create admin user if not exists
        from app.models import User
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
        
    except Exception as e:
        print(f"Database setup error: {e}")

if __name__ == '__main__':
    print("🚀 Starting Insurance Claims Management System")
    print("🌐 Access at: http://localhost:5000")
    print("👤 Admin Login: admin@insurance.com / admin123")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )
