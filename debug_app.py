#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Attempting to import app...")
    from app import create_app
    print("✅ Import successful!")
    
    print("Creating app...")
    app = create_app()
    print("✅ App created successfully!")
    
    print("Starting server on http://localhost:5000")
    print("Login: admin@insurance.com / admin123")
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
