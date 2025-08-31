#!/usr/bin/env python3
"""
Flask Deployment Script
سكريبت نشر تطبيق Flask
"""
import os
import sys
import subprocess
import argparse
from datetime import datetime

class FlaskDeployer:
    def __init__(self):
        self.app_name = "insurance-claims-app"
        self.port = os.environ.get('PORT', 5000)
        
    def deploy_local(self, debug=False):
        """Deploy locally for development"""
        print("🚀 نشر محلي للتطوير")
        print("-" * 30)
        
        try:
            if debug:
                # Development mode with Flask
                os.environ['FLASK_ENV'] = 'development'
                os.environ['FLASK_DEBUG'] = '1'
                subprocess.run([sys.executable, 'run.py'], check=True)
            else:
                # Production mode with Gunicorn
                os.environ['FLASK_ENV'] = 'production'
                subprocess.run([
                    'gunicorn',
                    '--config', 'gunicorn_config.py',
                    'run:app'
                ], check=True)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ خطأ في النشر المحلي: {e}")
            return False
        except KeyboardInterrupt:
            print("\n🛑 تم إيقاف الخادم")
            return True
            
        return True
    
    def deploy_heroku(self):
        """Deploy to Heroku"""
        print("🚢 نشر على Heroku")
        print("-" * 20)
        
        try:
            # Check if Heroku CLI is installed
            subprocess.run(['heroku', '--version'], 
                         capture_output=True, check=True)
            
            # Login check
            result = subprocess.run(['heroku', 'auth:whoami'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ يرجى تسجيل الدخول أولاً: heroku login")
                return False
            
            print(f"✅ مسجل دخول كـ: {result.stdout.strip()}")
            
            # Create app if not exists
            app_name = input("اسم التطبيق على Heroku (اتركه فارغاً للإنشاء التلقائي): ").strip()
            
            if app_name:
                subprocess.run(['heroku', 'create', app_name], check=True)
            else:
                subprocess.run(['heroku', 'create'], check=True)
            
            # Set environment variables
            subprocess.run([
                'heroku', 'config:set',
                'FLASK_ENV=production',
                f'SECRET_KEY={self.generate_secret_key()}',
                'SIMPLE_WHATSAPP_NUMBER=+966501234567'
            ], check=True)
            
            # Deploy
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', f'Deploy {datetime.now()}'], check=True)
            subprocess.run(['git', 'push', 'heroku', 'main'], check=True)
            
            print("✅ تم النشر على Heroku بنجاح!")
            
            # Open app
            subprocess.run(['heroku', 'open'], check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ خطأ في النشر على Heroku: {e}")
            return False
        except FileNotFoundError:
            print("❌ Heroku CLI غير مثبت. حمله من: https://devcenter.heroku.com/articles/heroku-cli")
            return False
            
        return True
    
    def deploy_railway(self):
        """Deploy to Railway"""
        print("🚂 نشر على Railway")
        print("-" * 20)
        
        print("📋 خطوات النشر على Railway:")
        print("1. اذهب إلى: https://railway.app")
        print("2. سجل دخول بحساب GitHub")
        print("3. اضغط 'New Project'")
        print("4. اختر 'Deploy from GitHub repo'")
        print("5. اختر مستودع المشروع")
        print("6. أضف متغيرات البيئة:")
        print("   - FLASK_ENV=production")
        print(f"   - SECRET_KEY={self.generate_secret_key()}")
        print("   - SIMPLE_WHATSAPP_NUMBER=+966501234567")
        print("7. انتظر النشر التلقائي")
        
        return True
    
    def deploy_render(self):
        """Deploy to Render"""
        print("🌊 نشر على Render")
        print("-" * 18)
        
        print("📋 خطوات النشر على Render:")
        print("1. اذهب إلى: https://render.com")
        print("2. سجل دخول بحساب GitHub")
        print("3. اضغط 'New +' → 'Web Service'")
        print("4. ربط مستودع GitHub")
        print("5. إعدادات البناء:")
        print("   Build Command: pip install -r requirements.txt")
        print("   Start Command: gunicorn --bind 0.0.0.0:$PORT run:app")
        print("6. أضف متغيرات البيئة:")
        print("   - FLASK_ENV=production")
        print(f"   - SECRET_KEY={self.generate_secret_key()}")
        print("   - SIMPLE_WHATSAPP_NUMBER=+966501234567")
        print("7. اضغط 'Create Web Service'")
        
        return True
    
    def deploy_docker(self):
        """Deploy using Docker"""
        print("🐳 نشر باستخدام Docker")
        print("-" * 25)
        
        try:
            # Check if Docker is installed
            subprocess.run(['docker', '--version'], 
                         capture_output=True, check=True)
            
            # Build image
            print("🔨 بناء صورة Docker...")
            subprocess.run([
                'docker', 'build', 
                '-t', self.app_name, 
                '.'
            ], check=True)
            
            # Run container
            print("🚀 تشغيل الحاوية...")
            subprocess.run([
                'docker', 'run', 
                '-p', f'{self.port}:5000',
                '-e', 'FLASK_ENV=production',
                '-e', f'SECRET_KEY={self.generate_secret_key()}',
                self.app_name
            ], check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ خطأ في Docker: {e}")
            return False
        except FileNotFoundError:
            print("❌ Docker غير مثبت. حمله من: https://docker.com")
            return False
        except KeyboardInterrupt:
            print("\n🛑 تم إيقاف الحاوية")
            return True
            
        return True
    
    def deploy_nginx(self):
        """Deploy with Nginx (Linux only)"""
        print("🌐 نشر مع Nginx")
        print("-" * 17)
        
        if os.name != 'posix':
            print("❌ هذا الخيار متاح فقط على Linux/Mac")
            return False
        
        nginx_config = f"""
server {{
    listen 80;
    server_name your-domain.com;
    
    location / {{
        proxy_pass http://127.0.0.1:{self.port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    location /static {{
        alias /path/to/your/app/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
}}
"""
        
        print("📝 إعداد Nginx:")
        print("1. ثبت Nginx: sudo apt install nginx")
        print("2. أنشئ ملف الإعداد:")
        print("   sudo nano /etc/nginx/sites-available/insurance-app")
        print("3. أضف الإعداد التالي:")
        print(nginx_config)
        print("4. فعل الموقع:")
        print("   sudo ln -s /etc/nginx/sites-available/insurance-app /etc/nginx/sites-enabled/")
        print("5. أعد تشغيل Nginx:")
        print("   sudo systemctl restart nginx")
        print("6. شغل التطبيق:")
        print(f"   gunicorn --bind 127.0.0.1:{self.port} run:app")
        
        return True
    
    def generate_secret_key(self):
        """Generate a secure secret key"""
        import secrets
        return secrets.token_hex(32)
    
    def check_requirements(self):
        """Check if all requirements are installed"""
        print("🔍 فحص المتطلبات...")
        
        try:
            import flask
            print(f"✅ Flask {flask.__version__}")
        except ImportError:
            print("❌ Flask غير مثبت")
            return False
        
        # Check if gunicorn is available for production
        try:
            subprocess.run(['gunicorn', '--version'], 
                         capture_output=True, check=True)
            print("✅ Gunicorn متاح")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ Gunicorn غير مثبت (مطلوب للإنتاج)")
            print("   تثبيت: pip install gunicorn")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Flask Deployment Script')
    parser.add_argument('platform', choices=[
        'local', 'heroku', 'railway', 'render', 'docker', 'nginx'
    ], help='منصة النشر')
    parser.add_argument('--debug', action='store_true', 
                       help='تشغيل في وضع التطوير (للنشر المحلي فقط)')
    
    args = parser.parse_args()
    
    deployer = FlaskDeployer()
    
    print("🚀 سكريبت نشر تطبيق Flask")
    print("=" * 35)
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 المنصة: {args.platform}")
    print()
    
    # Check requirements
    if not deployer.check_requirements():
        print("❌ يرجى تثبيت المتطلبات أولاً")
        return 1
    
    print()
    
    # Deploy based on platform
    success = False
    
    if args.platform == 'local':
        success = deployer.deploy_local(debug=args.debug)
    elif args.platform == 'heroku':
        success = deployer.deploy_heroku()
    elif args.platform == 'railway':
        success = deployer.deploy_railway()
    elif args.platform == 'render':
        success = deployer.deploy_render()
    elif args.platform == 'docker':
        success = deployer.deploy_docker()
    elif args.platform == 'nginx':
        success = deployer.deploy_nginx()
    
    if success:
        print("\n🎉 تم النشر بنجاح!")
    else:
        print("\n❌ فشل في النشر")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
