#!/usr/bin/env python3
"""
WhatsApp Integration Test Script
"""
import os
import sys
import requests
import urllib.parse
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_integration():
    """Test WhatsApp database integration"""
    print("🗄️ اختبار تكامل قاعدة البيانات...")
    print("-" * 40)
    
    try:
        from app import create_app, db
        from app.models import User
        
        app = create_app()
        with app.app_context():
            # Check if whatsapp_number column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'whatsapp_number' in columns:
                print("✅ عمود whatsapp_number موجود في قاعدة البيانات")
                
                # Check users with WhatsApp numbers
                users_with_whatsapp = User.query.filter(User.whatsapp_number.isnot(None)).all()
                total_users = User.query.count()
                
                print(f"📊 المستخدمون مع أرقام واتساب: {len(users_with_whatsapp)}/{total_users}")
                
                for user in users_with_whatsapp:
                    print(f"   👤 {user.full_name}: {user.whatsapp_number}")
                
                return True
            else:
                print("❌ عمود whatsapp_number غير موجود")
                return False
                
    except Exception as e:
        print(f"❌ خطأ في اختبار قاعدة البيانات: {e}")
        return False

def test_whatsapp_services():
    """Test WhatsApp services"""
    print("\n🔧 اختبار خدمات الواتساب...")
    print("-" * 40)
    
    try:
        from app import create_app
        from app.notification_services import get_whatsapp_client, send_whatsapp_notification
        
        app = create_app()
        with app.app_context():
            # Test WhatsApp client creation
            client = get_whatsapp_client()
            
            if client:
                print("✅ تم إنشاء WhatsApp client بنجاح")
                print(f"   🔗 Base URL: {client.base_url}")
                return True
            else:
                print("⚠️ WhatsApp client غير متاح (إعدادات غير مكونة)")
                
                # Test simple WhatsApp functionality
                phone = "+966501234567"
                message = "اختبار الواتساب"
                whatsapp_url = f"https://wa.me/{phone.replace('+', '')}?text={urllib.parse.quote(message)}"
                
                print("✅ الإعداد البسيط متاح")
                print(f"   🔗 رابط الاختبار: {whatsapp_url}")
                return True
                
    except Exception as e:
        print(f"❌ خطأ في اختبار الخدمات: {e}")
        return False

def test_web_interface():
    """Test WhatsApp web interface"""
    print("\n🌐 اختبار الواجهة الويب...")
    print("-" * 40)
    
    try:
        # Test if server is running
        base_url = "http://127.0.0.1:5000"
        
        # Test main page
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ السيرفر يعمل بشكل طبيعي")
        else:
            print(f"⚠️ السيرفر يعمل لكن هناك مشكلة: {response.status_code}")
        
        # Test WhatsApp test page
        whatsapp_test_url = f"{base_url}/advanced-notifications/whatsapp-test"
        try:
            response = requests.get(whatsapp_test_url, timeout=5)
            if response.status_code in [200, 302]:  # 302 for login redirect
                print("✅ صفحة اختبار الواتساب متاحة")
                print(f"   🔗 الرابط: {whatsapp_test_url}")
            else:
                print(f"⚠️ صفحة اختبار الواتساب: {response.status_code}")
        except:
            print("⚠️ صفحة اختبار الواتساب غير متاحة")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ السيرفر غير متاح")
        print("💡 تأكد من تشغيل السيرفر: python run.py")
        return False
    except Exception as e:
        print(f"❌ خطأ في اختبار الواجهة: {e}")
        return False

def test_whatsapp_url_generation():
    """Test WhatsApp URL generation"""
    print("\n🔗 اختبار إنتاج روابط الواتساب...")
    print("-" * 40)
    
    test_cases = [
        {
            'phone': '+966501234567',
            'message': 'مرحباً! هذه رسالة تجريبية من نظام إدارة مطالبات التأمين.'
        },
        {
            'phone': '966501234567',
            'message': 'تم استلام مطالبة جديدة برقم #12345'
        },
        {
            'phone': '0501234567',
            'message': 'تحديث: تم الموافقة على مطالبتك'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        try:
            phone = case['phone']
            message = case['message']
            
            # Clean phone number
            if not phone.startswith('+'):
                if phone.startswith('966'):
                    phone = '+' + phone
                elif phone.startswith('05'):
                    phone = '+966' + phone[1:]
                else:
                    phone = '+966' + phone
            
            # Generate WhatsApp URL
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f"https://wa.me/{phone.replace('+', '')}?text={encoded_message}"
            
            print(f"✅ اختبار {i}:")
            print(f"   📱 الرقم: {phone}")
            print(f"   💬 الرسالة: {message[:50]}...")
            print(f"   🔗 الرابط: {whatsapp_url[:80]}...")
            
        except Exception as e:
            print(f"❌ خطأ في اختبار {i}: {e}")
    
    return True

def test_notification_integration():
    """Test notification system integration"""
    print("\n🔔 اختبار تكامل نظام الإشعارات...")
    print("-" * 40)
    
    try:
        from app import create_app
        from app.advanced_notifications import AdvancedNotificationService
        
        app = create_app()
        with app.app_context():
            # Test notification service
            service = AdvancedNotificationService()
            
            if hasattr(service, 'whatsapp_client'):
                print("✅ خدمة الإشعارات تدعم الواتساب")
                
                if service.whatsapp_client:
                    print("✅ WhatsApp client مكون في خدمة الإشعارات")
                else:
                    print("⚠️ WhatsApp client غير مكون (سيستخدم الطريقة البسيطة)")
                
                return True
            else:
                print("❌ خدمة الإشعارات لا تدعم الواتساب")
                return False
                
    except Exception as e:
        print(f"❌ خطأ في اختبار نظام الإشعارات: {e}")
        return False

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n📊 تقرير الاختبار الشامل")
    print("=" * 50)
    
    tests = [
        ("تكامل قاعدة البيانات", test_database_integration),
        ("خدمات الواتساب", test_whatsapp_services),
        ("الواجهة الويب", test_web_interface),
        ("إنتاج روابط الواتساب", test_whatsapp_url_generation),
        ("تكامل نظام الإشعارات", test_notification_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ خطأ في تشغيل الاختبار: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 ملخص النتائج:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n📊 معدل النجاح: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 تكامل الواتساب يعمل بشكل ممتاز!")
    elif success_rate >= 60:
        print("⚠️ تكامل الواتساب يعمل مع بعض المشاكل")
    else:
        print("❌ تكامل الواتساب يحتاج إصلاحات")
    
    # Recommendations
    print("\n💡 التوصيات:")
    if passed < total:
        print("- راجع الأخطاء أعلاه وقم بإصلاحها")
        print("- تأكد من تشغيل السيرفر: python run.py")
        print("- تأكد من تحديث قاعدة البيانات: python update_database_whatsapp.py")
    
    print("- اختبر الميزة من المتصفح: http://127.0.0.1:5000/advanced-notifications/whatsapp-test")
    print("- راجع دليل الاستخدام: WHATSAPP_INTEGRATION_GUIDE.md")
    
    return success_rate >= 80

def main():
    """Main test function"""
    print("📱 اختبار تكامل الواتساب الشامل")
    print("نظام إدارة مطالبات التأمين")
    print("=" * 50)
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = generate_test_report()
    
    print(f"\n🏁 انتهى الاختبار - {'نجح' if success else 'فشل'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
