#!/usr/bin/env python3
"""
Fix notification enum values in database
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def fix_notification_enum():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Checking existing notification types...")
            
            # Check if table exists
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='advanced_notifications';"))
            if not result.fetchone():
                print("✅ Table 'advanced_notifications' doesn't exist yet. No fix needed.")
                return
            
            # Check existing notification types
            result = db.session.execute(text("SELECT DISTINCT notification_type FROM advanced_notifications;"))
            existing_types = [row[0] for row in result.fetchall()]
            
            print(f"📋 Found existing types: {existing_types}")
            
            # Map of incorrect values to correct values
            fixes = {
                'in_app': 'IN_APP',
                'email': 'EMAIL', 
                'sms': 'SMS',
                'push': 'PUSH',
                'whatsapp': 'WHATSAPP'
            }
            
            # Apply fixes
            for old_value, new_value in fixes.items():
                if old_value in existing_types:
                    print(f"🔧 Fixing '{old_value}' -> '{new_value}'...")
                    db.session.execute(
                        text("UPDATE advanced_notifications SET notification_type = :new_value WHERE notification_type = :old_value"),
                        {'new_value': new_value, 'old_value': old_value}
                    )
            
            # Also fix notification_templates table if it exists
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_templates';"))
            if result.fetchone():
                print("🔧 Fixing notification_templates table...")
                for old_value, new_value in fixes.items():
                    db.session.execute(
                        text("UPDATE notification_templates SET notification_type = :new_value WHERE notification_type = :old_value"),
                        {'new_value': new_value, 'old_value': old_value}
                    )
            
            # Also fix notification_queue table if it exists
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_queue';"))
            if result.fetchone():
                print("🔧 Fixing notification_queue table...")
                for old_value, new_value in fixes.items():
                    db.session.execute(
                        text("UPDATE notification_queue SET notification_type = :new_value WHERE notification_type = :old_value"),
                        {'new_value': new_value, 'old_value': old_value}
                    )
            
            # Commit changes
            db.session.commit()
            print("✅ Successfully fixed notification enum values!")
            
            # Verify the fix
            result = db.session.execute(text("SELECT DISTINCT notification_type FROM advanced_notifications;"))
            updated_types = [row[0] for row in result.fetchall()]
            print(f"📋 Updated types: {updated_types}")
            
        except Exception as e:
            print(f"❌ Error fixing enum values: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    fix_notification_enum()
