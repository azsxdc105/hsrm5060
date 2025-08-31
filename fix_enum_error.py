#!/usr/bin/env python3
"""
Fix enum error in notifications
"""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_enum_error():
    """Fix the enum error by updating database values"""
    print("🔧 إصلاح خطأ enum الإشعارات...")
    print("=" * 40)
    
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # Update any 'in_app' values to match enum
            with db.engine.connect() as conn:
                # Check if notifications table exists
                result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'"))
                if result.fetchone():
                    print("✅ جدول الإشعارات موجود")
                    
                    # Update any incorrect enum values
                    conn.execute(db.text("UPDATE notifications SET notification_type = 'in_app' WHERE notification_type = 'IN_APP'"))
                    conn.execute(db.text("UPDATE notifications SET notification_type = 'email' WHERE notification_type = 'EMAIL'"))
                    conn.execute(db.text("UPDATE notifications SET notification_type = 'sms' WHERE notification_type = 'SMS'"))
                    conn.execute(db.text("UPDATE notifications SET notification_type = 'push' WHERE notification_type = 'PUSH'"))
                    conn.execute(db.text("UPDATE notifications SET notification_type = 'whatsapp' WHERE notification_type = 'WHATSAPP'"))
                    
                    conn.commit()
                    print("✅ تم تحديث قيم enum في قاعدة البيانات")
                else:
                    print("⚠️ جدول الإشعارات غير موجود")
                
                # Check notification_templates table
                result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_templates'"))
                if result.fetchone():
                    print("✅ جدول قوالب الإشعارات موجود")
                    
                    # Update template types
                    conn.execute(db.text("UPDATE notification_templates SET notification_type = 'in_app' WHERE notification_type = 'IN_APP'"))
                    conn.execute(db.text("UPDATE notification_templates SET notification_type = 'email' WHERE notification_type = 'EMAIL'"))
                    conn.execute(db.text("UPDATE notification_templates SET notification_type = 'sms' WHERE notification_type = 'SMS'"))
                    conn.execute(db.text("UPDATE notification_templates SET notification_type = 'push' WHERE notification_type = 'PUSH'"))
                    conn.execute(db.text("UPDATE notification_templates SET notification_type = 'whatsapp' WHERE notification_type = 'WHATSAPP'"))
                    
                    conn.commit()
                    print("✅ تم تحديث قيم enum في جدول القوالب")
                else:
                    print("⚠️ جدول قوالب الإشعارات غير موجود")
            
            print("✅ تم إصلاح خطأ enum بنجاح!")
            return True
            
    except Exception as e:
        print(f"❌ خطأ في الإصلاح: {e}")
        return False

def clear_problematic_data():
    """Clear any problematic notification data"""
    print("\n🧹 تنظيف البيانات المشكلة...")
    print("-" * 30)
    
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            with db.engine.connect() as conn:
                # Delete any notifications with invalid enum values
                result = conn.execute(db.text("DELETE FROM notifications WHERE notification_type NOT IN ('email', 'sms', 'push', 'whatsapp', 'in_app')"))
                deleted_notifications = result.rowcount
                
                # Delete any templates with invalid enum values  
                result = conn.execute(db.text("DELETE FROM notification_templates WHERE notification_type NOT IN ('email', 'sms', 'push', 'whatsapp', 'in_app')"))
                deleted_templates = result.rowcount
                
                conn.commit()
                
                print(f"🗑️ تم حذف {deleted_notifications} إشعار مشكل")
                print(f"🗑️ تم حذف {deleted_templates} قالب مشكل")
                
            return True
            
    except Exception as e:
        print(f"❌ خطأ في التنظيف: {e}")
        return False

def recreate_notification_tables():
    """Recreate notification tables with correct schema"""
    print("\n🔄 إعادة إنشاء جداول الإشعارات...")
    print("-" * 40)
    
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            with db.engine.connect() as conn:
                # Drop existing tables
                conn.execute(db.text("DROP TABLE IF EXISTS notifications"))
                conn.execute(db.text("DROP TABLE IF EXISTS notification_templates"))
                conn.execute(db.text("DROP TABLE IF EXISTS user_notification_settings"))
                conn.commit()
                
                print("🗑️ تم حذف الجداول القديمة")
            
            # Recreate tables
            db.create_all()
            print("✅ تم إنشاء الجداول الجديدة")
            
            # Create default templates
            from app.models import NotificationTemplate
            
            templates = [
                {
                    'name': 'مطالبة جديدة',
                    'notification_type': 'email',
                    'subject': 'مطالبة تأمين جديدة - رقم {claim_number}',
                    'body': 'تم استلام مطالبة تأمين جديدة برقم {claim_number}. يرجى مراجعة النظام.',
                    'is_active': True
                },
                {
                    'name': 'تحديث المطالبة',
                    'notification_type': 'whatsapp',
                    'subject': 'تحديث المطالبة {claim_number}',
                    'body': 'تم تحديث حالة مطالبتك رقم {claim_number}. الحالة الجديدة: {status}',
                    'is_active': True
                },
                {
                    'name': 'إشعار عام',
                    'notification_type': 'in_app',
                    'subject': 'إشعار من النظام',
                    'body': 'لديك إشعار جديد في نظام إدارة مطالبات التأمين.',
                    'is_active': True
                }
            ]
            
            for template_data in templates:
                template = NotificationTemplate(**template_data)
                db.session.add(template)
            
            db.session.commit()
            print("✅ تم إنشاء القوالب الافتراضية")
            
            return True
            
    except Exception as e:
        print(f"❌ خطأ في إعادة الإنشاء: {e}")
        return False

def main():
    """Main function"""
    print("🔧 إصلاح خطأ enum الإشعارات")
    print("نظام إدارة مطالبات التأمين")
    print("=" * 50)
    
    # Try simple fix first
    if fix_enum_error():
        print("\n🎉 تم الإصلاح بنجاح!")
        return True
    
    # If that fails, try cleaning data
    print("\n🔄 محاولة تنظيف البيانات...")
    if clear_problematic_data():
        if fix_enum_error():
            print("\n🎉 تم الإصلاح بعد التنظيف!")
            return True
    
    # Last resort: recreate tables
    print("\n🔄 إعادة إنشاء الجداول...")
    if recreate_notification_tables():
        print("\n🎉 تم إعادة إنشاء الجداول بنجاح!")
        return True
    
    print("\n❌ فشل في إصلاح المشكلة")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
