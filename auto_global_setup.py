#!/usr/bin/env python3
"""
Automatic Global Access Setup
"""
import os
import sys
import subprocess
import requests
import json
import time
import threading
from datetime import datetime

class GlobalAccessManager:
    def __init__(self):
        self.server_process = None
        self.ngrok_process = None
        self.public_url = None
        
    def check_server_status(self):
        """Check if Flask server is running"""
        try:
            response = requests.get('http://127.0.0.1:5000', timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def start_flask_server(self):
        """Start Flask server"""
        print("🚀 بدء تشغيل السيرفر...")
        
        try:
            self.server_process = subprocess.Popen([
                sys.executable, 'run.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            for i in range(30):  # Wait up to 30 seconds
                if self.check_server_status():
                    print("✅ السيرفر يعمل بشكل طبيعي")
                    return True
                time.sleep(1)
            
            print("❌ فشل في بدء السيرفر")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في تشغيل السيرفر: {e}")
            return False
    
    def check_ngrok_installed(self):
        """Check if ngrok is installed"""
        try:
            result = subprocess.run(['ngrok', 'version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def start_ngrok_tunnel(self):
        """Start ngrok tunnel"""
        print("🌐 بدء نفق ngrok...")
        
        try:
            self.ngrok_process = subprocess.Popen([
                'ngrok', 'http', '5000', '--log=stdout'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for ngrok to start
            time.sleep(5)
            
            # Get public URL
            for i in range(10):
                try:
                    response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        tunnels = data.get('tunnels', [])
                        if tunnels:
                            self.public_url = tunnels[0]['public_url']
                            print("✅ تم إنشاء النفق بنجاح!")
                            return True
                except:
                    pass
                time.sleep(1)
            
            print("❌ فشل في الحصول على الرابط العام")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في تشغيل ngrok: {e}")
            return False
    
    def display_access_info(self):
        """Display access information"""
        print("\n" + "="*60)
        print("🎉 النظام متاح الآن عالمياً!")
        print("="*60)
        
        if self.public_url:
            print(f"🌍 الرابط العام: {self.public_url}")
            print(f"📱 اختبار الواتساب: {self.public_url}/advanced-notifications/whatsapp-test")
            print(f"🔐 لوحة الإدارة: {self.public_url}/admin")
        
        print("\n👤 بيانات تسجيل الدخول:")
        print("   📧 البريد الإلكتروني: admin@insurance.com")
        print("   🔑 كلمة المرور: admin123")
        
        print("\n⚠️ ملاحظات مهمة:")
        print("   - هذا الرابط مؤقت وسيتغير عند إعادة تشغيل ngrok")
        print("   - لا تشارك بيانات حساسة عبر ngrok")
        print("   - غير كلمة المرور الافتراضية للأمان")
        
        # Save to file
        if self.public_url:
            self.save_access_info()
    
    def save_access_info(self):
        """Save access information to file"""
        try:
            with open('public_access_info.txt', 'w', encoding='utf-8') as f:
                f.write(f"🌍 نظام إدارة مطالبات التأمين - معلومات الوصول العالمي\n")
                f.write(f"{'='*60}\n\n")
                f.write(f"📅 تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"🔗 الروابط:\n")
                f.write(f"   الرابط العام: {self.public_url}\n")
                f.write(f"   اختبار الواتساب: {self.public_url}/advanced-notifications/whatsapp-test\n")
                f.write(f"   لوحة الإدارة: {self.public_url}/admin\n")
                f.write(f"   إرسال إشعار: {self.public_url}/advanced-notifications/send\n\n")
                f.write(f"👤 بيانات تسجيل الدخول:\n")
                f.write(f"   البريد الإلكتروني: admin@insurance.com\n")
                f.write(f"   كلمة المرور: admin123\n\n")
                f.write(f"⚠️ ملاحظات:\n")
                f.write(f"   - غير كلمة المرور فوراً للأمان\n")
                f.write(f"   - هذا الرابط مؤقت ويتغير عند إعادة التشغيل\n")
                f.write(f"   - لا تشارك بيانات حساسة\n")
            
            print("📄 تم حفظ معلومات الوصول في ملف public_access_info.txt")
            
        except Exception as e:
            print(f"⚠️ لم يتم حفظ الملف: {e}")
    
    def monitor_services(self):
        """Monitor running services"""
        print("\n🔍 مراقبة الخدمات...")
        print("   للإيقاف: اضغط Ctrl+C")
        print("-" * 40)
        
        try:
            while True:
                # Check server status
                server_status = "🟢 يعمل" if self.check_server_status() else "🔴 متوقف"
                
                # Check ngrok status
                ngrok_status = "🟢 يعمل" if self.ngrok_process and self.ngrok_process.poll() is None else "🔴 متوقف"
                
                print(f"\r🖥️ السيرفر: {server_status} | 🌐 ngrok: {ngrok_status}", end="", flush=True)
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n\n🛑 إيقاف الخدمات...")
            self.cleanup()
    
    def cleanup(self):
        """Clean up processes"""
        if self.ngrok_process:
            self.ngrok_process.terminate()
            print("✅ تم إيقاف ngrok")
        
        if self.server_process:
            self.server_process.terminate()
            print("✅ تم إيقاف السيرفر")
    
    def setup_global_access(self):
        """Main setup function"""
        print("🌍 إعداد الوصول العالمي لنظام إدارة مطالبات التأمين")
        print("="*60)
        print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 1: Check/Start Flask server
        if not self.check_server_status():
            if not self.start_flask_server():
                print("❌ فشل في بدء السيرفر")
                return False
        else:
            print("✅ السيرفر يعمل بالفعل")
        
        # Step 2: Check ngrok
        if not self.check_ngrok_installed():
            print("❌ ngrok غير مثبت")
            print("\n📥 يرجى تحميل ngrok من:")
            print("   https://ngrok.com/download")
            print("\n📋 خطوات التثبيت:")
            print("1. حمل ngrok من الرابط أعلاه")
            print("2. فك الضغط في هذا المجلد")
            print("3. سجل حساب مجاني في ngrok.com")
            print("4. احصل على authtoken")
            print("5. شغل: ngrok config add-authtoken YOUR_TOKEN")
            return False
        
        print("✅ ngrok مثبت ومتاح")
        
        # Step 3: Start ngrok tunnel
        if not self.start_ngrok_tunnel():
            print("❌ فشل في إنشاء النفق")
            return False
        
        # Step 4: Display access info
        self.display_access_info()
        
        # Step 5: Monitor services
        self.monitor_services()
        
        return True

def main():
    """Main function"""
    manager = GlobalAccessManager()
    
    try:
        success = manager.setup_global_access()
        if not success:
            print("\n❌ فشل في إعداد الوصول العالمي")
            return 1
    except KeyboardInterrupt:
        print("\n\n🛑 تم إيقاف الإعداد بواسطة المستخدم")
        manager.cleanup()
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        manager.cleanup()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
