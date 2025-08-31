#!/usr/bin/env python3
"""
Database Migration Script
Adds claim_type_id column to existing claims table
"""

import os
import sys
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Claim, ClaimType
from app.routes.dynamic_forms import init_default_claim_types

def migrate_database():
    """Migrate existing database to support dynamic forms"""
    app = create_app('development')
    
    with app.app_context():
        print("🔧 Starting Database Migration...")
        
        # Get database path
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite:///' in db_uri:
            db_path = db_uri.replace('sqlite:///', '')
        else:
            db_path = 'instance/claims.db'
        
        # Make sure the path is absolute
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.path.dirname(__file__), db_path)
        
        print(f"📊 Database: {db_path}")
        
        if not os.path.exists(db_path):
            print("❌ Database file not found. Creating new database...")
            # Create all tables from scratch
            db.create_all()
            print("✅ New database created!")
            
            # Initialize default claim types
            print("📋 Adding default claim types and fields...")
            init_default_claim_types()
            print("✅ Default claim types added successfully!")
            return True
        
        try:
            # Connect to SQLite database directly
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if claims table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='claims'")
            if not cursor.fetchone():
                print("❌ Claims table not found. Creating all tables...")
                conn.close()
                db.create_all()
                print("✅ All tables created!")
                
                # Initialize default claim types
                print("📋 Adding default claim types and fields...")
                init_default_claim_types()
                print("✅ Default claim types added successfully!")
                return True
            
            # Check if claim_type_id column exists
            cursor.execute("PRAGMA table_info(claims)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'claim_type_id' not in columns:
                print("➕ Adding claim_type_id column to claims table...")
                
                # Add the new column
                cursor.execute("""
                    ALTER TABLE claims 
                    ADD COLUMN claim_type_id INTEGER
                """)
                
                print("✅ claim_type_id column added successfully!")
            else:
                print("✅ claim_type_id column already exists")
            
            conn.commit()
            conn.close()
            
            # Now create all tables (including new ones)
            print("📋 Creating new tables...")
            db.create_all()
            print("✅ All tables created successfully!")
            
            # Initialize default claim types if they don't exist
            if not ClaimType.query.first():
                print("📋 Adding default claim types and fields...")
                init_default_claim_types()
                print("✅ Default claim types added successfully!")
            else:
                print("✅ Claim types already exist")
            
            # Update existing claims with default claim type
            print("🔄 Updating existing claims...")
            
            # Get or create a default claim type
            default_claim_type = ClaimType.query.filter_by(code='general').first()
            if not default_claim_type:
                # Create a general claim type for existing claims
                default_claim_type = ClaimType(
                    name_ar='مطالبة عامة',
                    name_en='General Claim',
                    code='general',
                    description_ar='نوع افتراضي للمطالبات الموجودة',
                    description_en='Default type for existing claims',
                    icon='fas fa-file-alt',
                    color='#6c757d',
                    sort_order=0
                )
                db.session.add(default_claim_type)
                db.session.commit()
                print("✅ Created default claim type for existing claims")
            
            # Update claims without claim_type_id
            claims_updated = 0
            claims_without_type = Claim.query.filter_by(claim_type_id=None).all()
            
            for claim in claims_without_type:
                claim.claim_type_id = default_claim_type.id
                claims_updated += 1
            
            if claims_updated > 0:
                db.session.commit()
                print(f"✅ Updated {claims_updated} existing claims with default type")
            else:
                print("✅ No claims needed updating")
            
            print("\n🎉 Database migration completed successfully!")
            
            # Show summary
            print("\n📊 Database Summary:")
            print(f"   • Total Claims: {Claim.query.count()}")
            print(f"   • Claim Types: {ClaimType.query.count()}")
            
            claim_types = ClaimType.query.all()
            for ct in claim_types:
                count = Claim.query.filter_by(claim_type_id=ct.id).count()
                print(f"     - {ct.name_ar}: {count} claims")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)