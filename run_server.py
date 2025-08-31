#!/usr/bin/env python3
"""
Simple server runner
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create Flask application
app = create_app()

if __name__ == '__main__':
    print("🚀 Starting Flask application...")
    print("🌐 URL: http://localhost:5000")
    print("✅ Application ready!")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )
