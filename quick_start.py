#!/usr/bin/env python3
"""
Quick start script for the Insurance Claims Management System
"""
import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("🚀 Starting Insurance Claims Management System...")
print("📍 Working directory:", current_dir)

try:
    # Import Flask app
    print("📦 Importing application...")
    from app import create_app, db
    
    # Create application instance
    print("🏗️ Creating Flask application...")
    app = create_app()
    
    # Initialize database
    print("🗄️ Setting up database...")
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created")
            
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
            else:
                print("✅ Admin user already exists")
                
        except Exception as e:
            print(f"⚠️ Database setup warning: {e}")
    
    print("\n" + "="*60)
    print("🎉 APPLICATION READY!")
    print("="*60)
    print("🌐 URL: http://localhost:5000")
    print("👤 Admin Email: admin@insurance.com")
    print("🔑 Password: admin123")
    print("="*60)
    print("🚀 Starting server...")
    print("Press Ctrl+C to stop")
    print("-"*60)
    
    # Start the server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,
        threaded=True
    )
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're in the correct directory and all dependencies are installed.")
    print("Try running: pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    print("\n👋 Server stopped")
    input("Press Enter to exit...")
