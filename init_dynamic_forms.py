#!/usr/bin/env python3
"""
Initialize Dynamic Forms System
Creates database tables and adds default claim types and fields
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.routes.dynamic_forms import init_default_claim_types

def init_dynamic_forms():
    """Initialize dynamic forms system"""
    app = create_app('development')
    
    with app.app_context():
        print("🔧 Initializing Dynamic Forms System...")
        
        try:
            # Create all database tables
            print("📊 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Initialize default claim types and fields
            print("📋 Adding default claim types and fields...")
            init_default_claim_types()
            print("✅ Default claim types and fields added successfully!")
            
            print("\n🎉 Dynamic Forms System initialized successfully!")
            print("\n📋 Available Claim Types:")
            
            from app.models import ClaimType
            claim_types = ClaimType.query.all()
            for ct in claim_types:
                print(f"   • {ct.name_ar} ({ct.code}) - {len(ct.dynamic_fields)} fields")
            
            print(f"\n🔗 Access the dynamic forms at: http://127.0.0.1:5000/claims/new-dynamic")
            
        except Exception as e:
            print(f"❌ Error initializing dynamic forms: {e}")
            return False
    
    return True

if __name__ == '__main__':
    success = init_dynamic_forms()
    sys.exit(0 if success else 1)