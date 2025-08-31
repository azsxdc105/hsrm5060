#!/usr/bin/env python3
"""
Main application entry point
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app

    # Create Flask application
    app = create_app()

    if __name__ == '__main__':
        # Get configuration from environment variables
        host = os.environ.get('FLASK_HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 5000)))
        debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

        print(f"🚀 Starting Flask application...")
        print(f"📍 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"🐛 Debug: {debug}")
        print(f"🌐 URL: http://{host}:{port}")
        print(f"")
        print(f"✅ Application ready!")

        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False  # Disable reloader to avoid issues
        )

except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
