#!/usr/bin/env python3
"""
Add security fields to User model
"""
from app import create_app, db
from app.models import User
from datetime import datetime

def add_security_fields():
    """Add security fields to existing users table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Add new columns to users table
            with db.engine.connect() as conn:
                try:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN last_login DATETIME;'))
                    print("✓ Added last_login column")
                except Exception as e:
                    print(f"  last_login column might already exist: {e}")

                try:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN login_attempts INTEGER DEFAULT 0;'))
                    print("✓ Added login_attempts column")
                except Exception as e:
                    print(f"  login_attempts column might already exist: {e}")

                try:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN locked_until DATETIME;'))
                    print("✓ Added locked_until column")
                except Exception as e:
                    print(f"  locked_until column might already exist: {e}")

                try:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN password_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP;'))
                    print("✓ Added password_changed_at column")
                except Exception as e:
                    print(f"  password_changed_at column might already exist: {e}")

                try:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0;'))
                    print("✓ Added two_factor_enabled column")
                except Exception as e:
                    print(f"  two_factor_enabled column might already exist: {e}")

                try:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(32);'))
                    print("✓ Added two_factor_secret column")
                except Exception as e:
                    print(f"  two_factor_secret column might already exist: {e}")

                # Update existing users with default values
                try:
                    conn.execute(db.text('''
                        UPDATE users
                        SET login_attempts = 0,
                            two_factor_enabled = 0,
                            password_changed_at = CURRENT_TIMESTAMP
                        WHERE login_attempts IS NULL;
                    '''))
                    print("✓ Updated existing users with default values")
                except Exception as e:
                    print(f"  Error updating users: {e}")

                conn.commit()
            
            print("=" * 50)
            print("✅ Security fields added successfully!")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error adding security fields: {e}")
            print("Note: Some columns might already exist, which is normal.")

if __name__ == '__main__':
    add_security_fields()
