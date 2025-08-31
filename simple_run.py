#!/usr/bin/env python3
"""
Simple runner for the Insurance Claims Management System
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    print("✅ Successfully imported app modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def main():
    print("🚀 Starting Insurance Claims Management System...")
    
    try:
        # Create Flask app
        app = create_app()
        print("✅ Flask app created successfully")
        
        # Create database tables
        with app.app_context():
            db.create_all()
            print("✅ Database tables created")
            
            # Create admin user if not exists
            from app.models import User
            admin_user = User.query.filter_by(email='admin@insurance.com').first()
            
            if not admin_user:
                from werkzeug.security import generate_password_hash
                admin = User(
                    email='admin@insurance.com',
                    full_name='مدير النظام',
                    password_hash=generate_password_hash('admin123'),
                    role='admin',
                    active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created")
        
        print("\n" + "="*60)
        print("🎉 Server is starting!")
        print("🌐 Access the application at: http://localhost:5000")
        print("📧 Admin email: admin@insurance.com")
        print("🔑 Admin password: admin123")
        print("="*60)
        
        # Run the application
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
