#!/usr/bin/env python3
"""
Debug server to identify issues
"""
import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("🔍 Starting debug server...")
    
    # Import Flask app
    from app import create_app, db
    
    print("✅ App imported successfully")
    
    # Create application with debug mode
    app = create_app()
    app.config['DEBUG'] = True
    
    print("✅ App created successfully")
    
    # Initialize database
    with app.app_context():
        print("🗄️ Setting up database...")
        try:
            db.create_all()
            print("✅ Database tables created")
            
            # Create admin user if not exists
            from app.models import User
            admin = User.query.filter_by(email='admin@insurance.com').first()
            if not admin:
                print("👤 Creating admin user...")
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
                
        except Exception as e:
            print(f"❌ Database setup error: {e}")
            traceback.print_exc()
    
    print("\n" + "="*50)
    print("🚀 DEBUG SERVER STARTING")
    print("="*50)
    print("🌐 URL: http://localhost:5000")
    print("👤 Admin Email: admin@insurance.com")
    print("🔑 Password: admin123")
    print("🐛 Debug mode: ON")
    print("="*50)
    
    # Run the application with debug
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=True, 
        use_reloader=False
    )
    
except Exception as e:
    print(f"❌ Critical Error: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")