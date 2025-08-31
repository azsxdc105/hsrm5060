#!/usr/bin/env python3
"""
Simple server without debug output
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress debug output
import warnings
warnings.filterwarnings("ignore")

try:
    from app import create_app, db
    
    # Create Flask application
    app = create_app()
    
    # Setup database
    with app.app_context():
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
    
    print("🚀 Server starting on http://localhost:5000")
    print("📧 Admin: admin@insurance.com / admin123")
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
