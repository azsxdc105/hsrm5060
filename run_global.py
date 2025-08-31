#!/usr/bin/env python3
"""
Global Runner for Insurance Claims Management System
Run the application accessible from anywhere in the world
"""
import os
import sys
import socket
from app import create_app

def get_local_ip():
    """Get local IP address"""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def main():
    """Run the application for global access"""
    print("🌍 نظام إدارة مطالبات التأمين - الوصول العالمي")
    print("=" * 60)
    
    # Set environment for production
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    # Create app
    app = create_app()
    
    # Configure for global access
    app.config.update(
        DEBUG=False,
        TESTING=False,
        # Allow all origins for CORS
        CORS_ORIGINS=['*'],
        # Security headers
        SESSION_COOKIE_SECURE=False,  # Set to True if using HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    # Get network information
    local_ip = get_local_ip()
    port = 5000
    
    print("✅ التطبيق جاهز للتشغيل")
    print("🌐 سيكون متاحاً على جميع عناوين IP")
    print()
    print("📡 معلومات الوصول:")
    print(f"   🏠 محلي: http://127.0.0.1:{port}")
    print(f"   🌐 الشبكة المحلية: http://{local_ip}:{port}")
    print(f"   📱 اختبار الواتساب: http://{local_ip}:{port}/advanced-notifications/whatsapp-test")
    print()
    print("👤 بيانات تسجيل الدخول:")
    print("   📧 البريد الإلكتروني: admin@insurance.com")
    print("   🔑 كلمة المرور: admin123")
    print()
    print("⚠️ ملاحظات مهمة:")
    print("   - تأكد من فتح المنفذ 5000 في جدار الحماية")
    print("   - للوصول من الإنترنت، استخدم ngrok أو خدمة مماثلة")
    print("   - غير كلمة المرور الافتراضية للأمان")
    print()
    print("🚀 بدء الخادم...")
    print("   للإيقاف: اضغط Ctrl+C")
    print("-" * 60)
    
    try:
        # Run on all interfaces
        app.run(
            host='0.0.0.0',  # Listen on all interfaces
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الخادم")
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل الخادم: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
