#!/usr/bin/env python3
"""
Fix claim_classifications database integrity issues
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def fix_claim_classifications():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Checking claim_classifications table...")
            
            # Check if table exists
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='claim_classifications';"))
            if not result.fetchone():
                print("✅ Table 'claim_classifications' doesn't exist yet. No fix needed.")
                return
            
            # Check for records with NULL claim_id
            result = db.session.execute(text("SELECT COUNT(*) FROM claim_classifications WHERE claim_id IS NULL;"))
            null_count = result.fetchone()[0]
            
            print(f"📋 Found {null_count} records with NULL claim_id")
            
            if null_count > 0:
                print("🔧 Fixing NULL claim_id records...")
                
                # Option 1: Delete records with NULL claim_id (safest approach)
                db.session.execute(text("DELETE FROM claim_classifications WHERE claim_id IS NULL;"))
                
                # Option 2: Alternative - Update with a default value if needed
                # db.session.execute(text("UPDATE claim_classifications SET claim_id = 'unknown' WHERE claim_id IS NULL;"))
                
                db.session.commit()
                print("✅ Successfully removed records with NULL claim_id!")
            
            # Check for orphaned records (claim_id doesn't exist in claims table)
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM claim_classifications cc 
                LEFT JOIN claims c ON cc.claim_id = c.id 
                WHERE c.id IS NULL AND cc.claim_id IS NOT NULL;
            """))
            orphaned_count = result.fetchone()[0]
            
            print(f"📋 Found {orphaned_count} orphaned records")
            
            if orphaned_count > 0:
                print("🔧 Fixing orphaned records...")
                db.session.execute(text("""
                    DELETE FROM claim_classifications 
                    WHERE claim_id NOT IN (SELECT id FROM claims);
                """))
                db.session.commit()
                print("✅ Successfully removed orphaned records!")
            
            # Verify the fix
            result = db.session.execute(text("SELECT COUNT(*) FROM claim_classifications WHERE claim_id IS NULL;"))
            remaining_null = result.fetchone()[0]
            
            result = db.session.execute(text("SELECT COUNT(*) FROM claim_classifications;"))
            total_records = result.fetchone()[0]
            
            print(f"📊 Final status:")
            print(f"   - Total records: {total_records}")
            print(f"   - Records with NULL claim_id: {remaining_null}")
            
            if remaining_null == 0:
                print("✅ All integrity issues fixed!")
            else:
                print("⚠️ Some issues remain")
                
        except Exception as e:
            print(f"❌ Error fixing claim_classifications: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    fix_claim_classifications()
