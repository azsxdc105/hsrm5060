#!/usr/bin/env python3
"""
Comprehensive database integrity fix
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def fix_all_database_issues():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Running comprehensive database integrity check...")
            
            # 1. Fix claim_classifications issues
            print("\n1️⃣ Checking claim_classifications...")
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='claim_classifications';"))
            if result.fetchone():
                # Check for NULL claim_id
                result = db.session.execute(text("SELECT COUNT(*) FROM claim_classifications WHERE claim_id IS NULL;"))
                null_count = result.fetchone()[0]
                if null_count > 0:
                    print(f"   🔧 Fixing {null_count} NULL claim_id records...")
                    db.session.execute(text("DELETE FROM claim_classifications WHERE claim_id IS NULL;"))
                
                # Check for orphaned records
                result = db.session.execute(text("""
                    SELECT COUNT(*) FROM claim_classifications cc 
                    LEFT JOIN claims c ON cc.claim_id = c.id 
                    WHERE c.id IS NULL AND cc.claim_id IS NOT NULL;
                """))
                orphaned_count = result.fetchone()[0]
                if orphaned_count > 0:
                    print(f"   🔧 Fixing {orphaned_count} orphaned records...")
                    db.session.execute(text("""
                        DELETE FROM claim_classifications 
                        WHERE claim_id NOT IN (SELECT id FROM claims);
                    """))
                print("   ✅ claim_classifications fixed")
            else:
                print("   ✅ claim_classifications table doesn't exist")
            
            # 2. Fix notification enum issues
            print("\n2️⃣ Checking notification enums...")
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='advanced_notifications';"))
            if result.fetchone():
                # Fix notification_type enum
                type_fixes = {
                    'in_app': 'IN_APP',
                    'email': 'EMAIL',
                    'sms': 'SMS',
                    'push': 'PUSH',
                    'whatsapp': 'WHATSAPP'
                }

                for old_value, new_value in type_fixes.items():
                    result = db.session.execute(
                        text("SELECT COUNT(*) FROM advanced_notifications WHERE notification_type = :old_value"),
                        {'old_value': old_value}
                    )
                    count = result.fetchone()[0]
                    if count > 0:
                        print(f"   🔧 Fixing {count} notification_type '{old_value}' -> '{new_value}' records...")
                        db.session.execute(
                            text("UPDATE advanced_notifications SET notification_type = :new_value WHERE notification_type = :old_value"),
                            {'new_value': new_value, 'old_value': old_value}
                        )

                # Fix priority enum
                priority_fixes = {
                    'low': 'LOW',
                    'normal': 'NORMAL',
                    'high': 'HIGH',
                    'urgent': 'URGENT'
                }

                for old_value, new_value in priority_fixes.items():
                    result = db.session.execute(
                        text("SELECT COUNT(*) FROM advanced_notifications WHERE priority = :old_value"),
                        {'old_value': old_value}
                    )
                    count = result.fetchone()[0]
                    if count > 0:
                        print(f"   🔧 Fixing {count} priority '{old_value}' -> '{new_value}' records...")
                        db.session.execute(
                            text("UPDATE advanced_notifications SET priority = :new_value WHERE priority = :old_value"),
                            {'new_value': new_value, 'old_value': old_value}
                        )

                print("   ✅ notification enums fixed")
            else:
                print("   ✅ advanced_notifications table doesn't exist")
            
            # 3. Fix foreign key constraints
            print("\n3️⃣ Checking foreign key constraints...")
            
            # Check claim_attachments
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='claim_attachments';"))
            if result.fetchone():
                result = db.session.execute(text("""
                    SELECT COUNT(*) FROM claim_attachments ca 
                    LEFT JOIN claims c ON ca.claim_id = c.id 
                    WHERE c.id IS NULL;
                """))
                orphaned_attachments = result.fetchone()[0]
                if orphaned_attachments > 0:
                    print(f"   🔧 Fixing {orphaned_attachments} orphaned claim_attachments...")
                    db.session.execute(text("""
                        DELETE FROM claim_attachments 
                        WHERE claim_id NOT IN (SELECT id FROM claims);
                    """))
            
            # Check email_logs
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='email_logs';"))
            if result.fetchone():
                result = db.session.execute(text("""
                    SELECT COUNT(*) FROM email_logs el 
                    LEFT JOIN claims c ON el.claim_id = c.id 
                    WHERE c.id IS NULL;
                """))
                orphaned_logs = result.fetchone()[0]
                if orphaned_logs > 0:
                    print(f"   🔧 Fixing {orphaned_logs} orphaned email_logs...")
                    db.session.execute(text("""
                        DELETE FROM email_logs 
                        WHERE claim_id NOT IN (SELECT id FROM claims);
                    """))
            
            print("   ✅ foreign key constraints fixed")
            
            # 4. Commit all changes
            db.session.commit()
            print("\n✅ All database integrity issues have been fixed!")
            
            # 5. Final verification
            print("\n📊 Final verification:")
            
            # Count records in main tables
            tables_to_check = ['users', 'claims', 'claim_attachments', 'email_logs', 'advanced_notifications']
            for table in tables_to_check:
                result = db.session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';"))
                if result.fetchone():
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    count = result.fetchone()[0]
                    print(f"   - {table}: {count} records")
                else:
                    print(f"   - {table}: table doesn't exist")
                    
        except Exception as e:
            print(f"❌ Error fixing database issues: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    fix_all_database_issues()
