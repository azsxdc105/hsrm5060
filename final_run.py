#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

print("🚀 Server starting at http://localhost:5000")
print("📧 Login: admin@insurance.com / admin123")

app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
