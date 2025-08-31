#!/usr/bin/env python3
"""
Setup Global Access for Insurance Claims Management System
"""
import os
import sys
import subprocess
import requests
import json
import time
from datetime import datetime

def check_ngrok_installed():
    """Check if ngrok is installed"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok مثبت ومتاح")
            print(f"   الإصدار: {result.stdout.strip()}")
            return True
        else:
            print("❌ ngrok غير مثبت")
            return False
    except FileNotFoundError:
        print("❌ ngrok غير مثبت")
        return False

def install_ngrok():
    """Install ngrok"""
    print("📥 تحميل وتثبيت ngrok...")
    print("=" * 30)
    
    print("🔗 يرجى تحميل ngrok من الرابط التالي:")
    print("   https://ngrok.com/download")
    print()
    print("📋 خطوات التثبيت:")
    print("1. اذهب إلى https://ngrok.com/download")
    print("2. حمل الإصدار المناسب لنظام التشغيل")
    print("3. فك الضغط عن الملف")
    print("4. ضع ملف ngrok.exe في مجلد النظام أو في مجلد المشروع")
    print("5. سجل حساب مجاني في ngrok.com")
    print("6. احصل على authtoken من لوحة التحكم")
    print("7. شغل: ngrok config add-authtoken YOUR_TOKEN")
    print()
    
    return False

def setup_ngrok_tunnel():
    """Setup ngrok tunnel"""
    print("🌐 إعداد نفق ngrok...")
    print("-" * 25)
    
    try:
        # Start ngrok tunnel
        print("🚀 بدء تشغيل نفق ngrok...")
        
        # Run ngrok in background
        process = subprocess.Popen([
            'ngrok', 'http', '5000',
            '--log=stdout'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a bit for ngrok to start
        time.sleep(3)
        
        # Get ngrok API info
        try:
            response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                
                if tunnels:
                    public_url = tunnels[0]['public_url']
                    print("✅ تم إنشاء النفق بنجاح!")
                    print(f"🌍 الرابط العام: {public_url}")
                    print(f"🔗 رابط اختبار الواتساب: {public_url}/advanced-notifications/whatsapp-test")
                    
                    # Save URL to file
                    with open('public_url.txt', 'w') as f:
                        f.write(f"Public URL: {public_url}\n")
                        f.write(f"WhatsApp Test: {public_url}/advanced-notifications/whatsapp-test\n")
                        f.write(f"Admin Panel: {public_url}/admin\n")
                        f.write(f"Login: admin@insurance.com / admin123\n")
                        f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
                    print("📄 تم حفظ الرابط في ملف public_url.txt")
                    
                    return public_url, process
                else:
                    print("❌ لم يتم العثور على أنفاق نشطة")
                    return None, process
            else:
                print("❌ فشل في الحصول على معلومات النفق")
                return None, process
                
        except requests.exceptions.ConnectionError:
            print("❌ لا يمكن الاتصال بـ ngrok API")
            print("💡 تأكد من تشغيل ngrok بشكل صحيح")
            return None, process
            
    except Exception as e:
        print(f"❌ خطأ في إعداد ngrok: {e}")
        return None, None

def setup_production_server():
    """Setup production server configuration"""
    print("🏭 إعداد خادم الإنتاج...")
    print("-" * 25)
    
    # Update Flask configuration for production
    config_updates = """
# Production Configuration for Global Access
import os

class ProductionConfig:
    DEBUG = False
    TESTING = False
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-key-change-this'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///insurance_claims.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS for global access
    CORS_ORIGINS = ['*']  # Allow all origins
    
    # Session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # WhatsApp configuration
    WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    SIMPLE_WHATSAPP_ENABLED = True
    SIMPLE_WHATSAPP_NUMBER = os.environ.get('SIMPLE_WHATSAPP_NUMBER', '+966501234567')
"""
    
    # Save production config
    with open('production_config.py', 'w', encoding='utf-8') as f:
        f.write(config_updates)
    
    print("✅ تم إنشاء ملف إعدادات الإنتاج")
    
    return True

def create_global_runner():
    """Create a script to run the app globally"""
    print("📝 إنشاء سكريبت التشغيل العالمي...")
    print("-" * 35)
    
    runner_script = '''#!/usr/bin/env python3
"""
Global Runner for Insurance Claims Management System
"""
import os
import sys
from app import create_app

def main():
    """Run the application for global access"""
    print("🌍 بدء تشغيل نظام إدارة مطالبات التأمين للوصول العالمي")
    print("=" * 60)
    
    # Set environment for production
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    # Create app
    app = create_app()
    
    # Configure for global access
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
    print("✅ التطبيق جاهز للتشغيل")
    print("🌐 سيكون متاحاً على جميع عناوين IP")
    print("🔒 تأكد من تأمين النظام قبل النشر العام")
    print()
    print("🚀 بدء الخادم...")
    
    # Run on all interfaces
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )

if __name__ == '__main__':
    main()
'''
    
    with open('run_global.py', 'w', encoding='utf-8') as f:
        f.write(runner_script)
    
    print("✅ تم إنشاء run_global.py")
    
    return True

def create_docker_setup():
    """Create Docker setup for easy deployment"""
    print("🐳 إنشاء إعداد Docker...")
    print("-" * 25)
    
    # Dockerfile
    dockerfile = '''FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=run_global.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "run_global.py"]
'''
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)
    
    # Docker Compose
    docker_compose = '''version: '3.8'

services:
  insurance-app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-super-secret-key-change-this
      - SIMPLE_WHATSAPP_NUMBER=+966501234567
    volumes:
      - ./uploads:/app/uploads
      - ./instance:/app/instance
    restart: unless-stopped
'''
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)
    
    print("✅ تم إنشاء Dockerfile و docker-compose.yml")
    
    return True

def show_deployment_options():
    """Show various deployment options"""
    print("\n🚀 خيارات النشر العالمي:")
    print("=" * 30)
    
    print("1. 🔥 ngrok (سريع ومجاني):")
    print("   - مثالي للاختبار والعروض التوضيحية")
    print("   - رابط مؤقت يتغير عند إعادة التشغيل")
    print("   - سهل الإعداد")
    
    print("\n2. ☁️ خدمات السحابة المجانية:")
    print("   - Heroku (مجاني مع قيود)")
    print("   - Railway (مجاني مع قيود)")
    print("   - Render (مجاني مع قيود)")
    print("   - PythonAnywhere (مجاني مع قيود)")
    
    print("\n3. 🏢 خوادم VPS:")
    print("   - DigitalOcean")
    print("   - Linode")
    print("   - AWS EC2")
    print("   - Google Cloud")
    
    print("\n4. 🐳 Docker:")
    print("   - سهل النشر على أي خادم")
    print("   - يمكن استخدامه مع Kubernetes")
    print("   - متوافق مع جميع منصات السحابة")

def main():
    """Main function"""
    print("🌍 إعداد الوصول العالمي لنظام إدارة مطالبات التأمين")
    print("=" * 60)
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Setup production configuration
    setup_production_server()
    create_global_runner()
    create_docker_setup()
    
    # Check for ngrok
    if check_ngrok_installed():
        print("\n🚀 هل تريد بدء نفق ngrok الآن؟ (y/n)")
        choice = input().lower().strip()
        
        if choice == 'y':
            public_url, process = setup_ngrok_tunnel()
            
            if public_url:
                print(f"\n🎉 النظام متاح الآن عالمياً!")
                print(f"🌍 الرابط العام: {public_url}")
                print(f"👤 تسجيل الدخول: admin@insurance.com / admin123")
                print(f"📱 اختبار الواتساب: {public_url}/advanced-notifications/whatsapp-test")
                
                print("\n⚠️ ملاحظات مهمة:")
                print("- هذا الرابط مؤقت وسيتغير عند إعادة تشغيل ngrok")
                print("- تأكد من تأمين النظام قبل مشاركة الرابط")
                print("- لا تشارك بيانات حساسة عبر ngrok")
                
                print("\n🔄 لإيقاف النفق، اضغط Ctrl+C")
                
                try:
                    # Keep the script running
                    process.wait()
                except KeyboardInterrupt:
                    print("\n🛑 تم إيقاف النفق")
                    process.terminate()
            else:
                print("❌ فشل في إنشاء النفق")
        else:
            print("✅ تم إنشاء الملفات المطلوبة للنشر")
    else:
        install_ngrok()
    
    show_deployment_options()
    
    print("\n📄 الملفات المنشأة:")
    print("- run_global.py: سكريبت التشغيل العالمي")
    print("- production_config.py: إعدادات الإنتاج")
    print("- Dockerfile: لنشر Docker")
    print("- docker-compose.yml: لتشغيل Docker Compose")
    
    if os.path.exists('public_url.txt'):
        print("- public_url.txt: معلومات الرابط العام")

if __name__ == "__main__":
    main()
