#!/usr/bin/env python3
"""
Database Update Script - Add WhatsApp Support
"""
import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

def update_database():
    """Update database to add WhatsApp support"""
    print("🔄 تحديث قاعدة البيانات لدعم الواتساب...")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if whatsapp_number column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'whatsapp_number' not in columns:
                print("📱 إضافة عمود رقم الواتساب...")

                # Add whatsapp_number column to users table
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN whatsapp_number VARCHAR(20)'))
                    conn.commit()
                print("✅ تم إضافة عمود whatsapp_number بنجاح")
            else:
                print("✅ عمود whatsapp_number موجود بالفعل")
            
            # Update existing users to copy phone number to whatsapp_number if empty
            users_updated = 0
            users = User.query.all()
            
            for user in users:
                if user.phone and not user.whatsapp_number:
                    user.whatsapp_number = user.phone
                    users_updated += 1
            
            if users_updated > 0:
                db.session.commit()
                print(f"📞 تم تحديث {users_updated} مستخدم بأرقام الواتساب")
            
            print("\n✅ تم تحديث قاعدة البيانات بنجاح!")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحديث قاعدة البيانات: {e}")
            db.session.rollback()
            return False

def test_whatsapp_integration():
    """Test WhatsApp integration"""
    print("\n🧪 اختبار تكامل الواتساب...")
    print("=" * 30)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if WhatsApp configuration exists
            whatsapp_token = app.config.get('WHATSAPP_ACCESS_TOKEN')
            phone_number_id = app.config.get('WHATSAPP_PHONE_NUMBER_ID')
            
            if whatsapp_token and phone_number_id:
                print("✅ إعدادات WhatsApp Business API موجودة")
                
                # Test WhatsApp client
                from app.notification_services import get_whatsapp_client
                client = get_whatsapp_client()
                
                if client:
                    print("✅ تم إنشاء WhatsApp client بنجاح")
                    return True
                else:
                    print("⚠️ فشل في إنشاء WhatsApp client")
                    return False
            else:
                print("⚠️ إعدادات WhatsApp غير مكونة")
                print("💡 استخدم python whatsapp_setup.py لتكوين الواتساب")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في اختبار الواتساب: {e}")
            return False

def show_whatsapp_status():
    """Show current WhatsApp integration status"""
    print("\n📊 حالة تكامل الواتساب:")
    print("=" * 30)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check database
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'whatsapp_number' in columns:
                print("✅ قاعدة البيانات: محدثة")
                
                # Count users with WhatsApp numbers
                users_with_whatsapp = User.query.filter(User.whatsapp_number.isnot(None)).count()
                total_users = User.query.count()
                
                print(f"📱 المستخدمون مع أرقام واتساب: {users_with_whatsapp}/{total_users}")
            else:
                print("❌ قاعدة البيانات: تحتاج تحديث")
            
            # Check configuration
            whatsapp_token = app.config.get('WHATSAPP_ACCESS_TOKEN')
            phone_number_id = app.config.get('WHATSAPP_PHONE_NUMBER_ID')
            
            if whatsapp_token and phone_number_id:
                print("✅ الإعدادات: مكونة")
            else:
                print("⚠️ الإعدادات: غير مكونة")
            
            # Check notification service
            try:
                from app.notification_services import get_whatsapp_client
                client = get_whatsapp_client()
                if client:
                    print("✅ الخدمة: متاحة")
                else:
                    print("⚠️ الخدمة: غير متاحة")
            except:
                print("❌ الخدمة: خطأ")
                
        except Exception as e:
            print(f"❌ خطأ في فحص الحالة: {e}")

def main():
    """Main function"""
    print("🔗 تحديث النظام لدعم الواتساب")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'update':
            update_database()
        elif command == 'test':
            test_whatsapp_integration()
        elif command == 'status':
            show_whatsapp_status()
        else:
            print("❌ أمر غير معروف")
            print("الاستخدام: python update_database_whatsapp.py [update|test|status]")
    else:
        # Run all operations
        print("🔄 تشغيل جميع العمليات...")
        
        # Update database
        if update_database():
            # Test integration
            test_whatsapp_integration()
        
        # Show status
        show_whatsapp_status()
        
        print("\n💡 نصائح:")
        print("- استخدم python whatsapp_setup.py لتكوين الواتساب")
        print("- تأكد من إضافة أرقام الواتساب للمستخدمين")
        print("- اختبر الإرسال من صفحة الإشعارات المتقدمة")

if __name__ == "__main__":
    main()
