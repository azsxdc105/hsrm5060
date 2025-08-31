#!/usr/bin/env python3
"""
Update database schema to add new columns
"""
import sqlite3
import os

def update_database():
    """Update database schema"""
    db_path = 'app.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add phone column to users table
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN phone VARCHAR(20)')
            print('✅ Added phone column to users table')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print('ℹ️  Phone column already exists')
            else:
                print(f'❌ Error adding phone column: {e}')
        
        # Add language column to users table
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN language VARCHAR(2) DEFAULT "ar"')
            print('✅ Added language column to users table')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print('ℹ️  Language column already exists')
            else:
                print(f'❌ Error adding language column: {e}')
        
        # Create notifications table if it doesn't exist
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    notification_type VARCHAR(50) NOT NULL,
                    related_claim_id VARCHAR(36),
                    is_read BOOLEAN DEFAULT 0,
                    sent_via_email BOOLEAN DEFAULT 0,
                    sent_via_sms BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    read_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (related_claim_id) REFERENCES claims (id)
                )
            ''')
            print('✅ Created notifications table')
        except sqlite3.OperationalError as e:
            print(f'ℹ️  Notifications table: {e}')
        
        # Create notification_preferences table if it doesn't exist
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    notification_type VARCHAR(50) NOT NULL,
                    email_enabled BOOLEAN DEFAULT 1,
                    sms_enabled BOOLEAN DEFAULT 0,
                    push_enabled BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, notification_type)
                )
            ''')
            print('✅ Created notification_preferences table')
        except sqlite3.OperationalError as e:
            print(f'ℹ️  Notification preferences table: {e}')
        
        # Update existing users to have default language
        try:
            cursor.execute('UPDATE users SET language = "ar" WHERE language IS NULL')
            updated_rows = cursor.rowcount
            if updated_rows > 0:
                print(f'✅ Updated {updated_rows} users with default language')
        except sqlite3.OperationalError as e:
            print(f'❌ Error updating users language: {e}')
        
        conn.commit()
        print('\n🎉 Database schema updated successfully!')
        
        # Show current users table structure
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print('\n📋 Current users table structure:')
        for col in columns:
            print(f'   - {col[1]} ({col[2]})')
        
    except Exception as e:
        print(f'❌ Unexpected error: {e}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_database()
