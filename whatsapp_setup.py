#!/usr/bin/env python3
"""
WhatsApp Integration Setup for Insurance Claims Management System
"""
import os
import requests
import json
from datetime import datetime

class WhatsAppSetup:
    def __init__(self):
        self.access_token = None
        self.phone_number_id = None
        self.verify_token = None
        self.webhook_url = None
        
    def configure_whatsapp(self):
        """Configure WhatsApp Business API"""
        print("🔧 إعداد WhatsApp Business API")
        print("=" * 50)
        
        print("\n📋 يرجى إدخال المعلومات التالية:")
        print("(يمكنك الحصول عليها من Facebook Developers Console)")
        
        # Get configuration from user
        self.access_token = input("🔑 Access Token: ").strip()
        self.phone_number_id = input("📱 Phone Number ID: ").strip()
        self.verify_token = input("🔐 Webhook Verify Token: ").strip()
        
        # Optional webhook URL
        webhook_input = input("🌐 Webhook URL (اختياري، اتركه فارغ إذا لم تكن تعرف): ").strip()
        if webhook_input:
            self.webhook_url = webhook_input
        
        return self.save_configuration()
    
    def save_configuration(self):
        """Save WhatsApp configuration"""
        try:
            # Create environment variables
            env_content = f"""
# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN={self.access_token}
WHATSAPP_PHONE_NUMBER_ID={self.phone_number_id}
WHATSAPP_VERIFY_TOKEN={self.verify_token}
"""
            
            if self.webhook_url:
                env_content += f"WHATSAPP_WEBHOOK_URL={self.webhook_url}\n"
            
            # Save to .env file
            with open('.env', 'a', encoding='utf-8') as f:
                f.write(env_content)
            
            # Also update config.py
            config_addition = f"""
# WhatsApp Configuration (Added automatically)
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '{self.access_token}')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '{self.phone_number_id}')
WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN', '{self.verify_token}')
"""
            
            with open('config.py', 'a', encoding='utf-8') as f:
                f.write(config_addition)
            
            print("✅ تم حفظ إعدادات WhatsApp بنجاح!")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في حفظ الإعدادات: {e}")
            return False
    
    def test_whatsapp_connection(self):
        """Test WhatsApp API connection"""
        print("\n🧪 اختبار الاتصال بـ WhatsApp API...")
        
        if not self.access_token or not self.phone_number_id:
            print("❌ يرجى تكوين WhatsApp أولاً")
            return False
        
        try:
            # Test API endpoint
            url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ الاتصال بـ WhatsApp API ناجح!")
                print(f"📱 رقم الهاتف: {data.get('display_phone_number', 'غير محدد')}")
                print(f"📊 حالة الرقم: {data.get('verified_name', 'غير محدد')}")
                return True
            else:
                print(f"❌ فشل الاتصال: {response.status_code}")
                print(f"📄 الرسالة: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في الاختبار: {e}")
            return False
    
    def send_test_message(self, recipient_number):
        """Send a test WhatsApp message"""
        print(f"\n📤 إرسال رسالة تجريبية إلى {recipient_number}...")
        
        if not self.access_token or not self.phone_number_id:
            print("❌ يرجى تكوين WhatsApp أولاً")
            return False
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Ensure phone number format is correct
            if not recipient_number.startswith('+'):
                if recipient_number.startswith('966'):
                    recipient_number = '+' + recipient_number
                elif recipient_number.startswith('05'):
                    recipient_number = '+966' + recipient_number[1:]
                else:
                    recipient_number = '+966' + recipient_number
            
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_number,
                "type": "text",
                "text": {
                    "body": f"🎉 مرحباً! هذه رسالة تجريبية من نظام إدارة مطالبات التأمين.\n\n📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n✅ تم ربط WhatsApp بنجاح!"
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'غير محدد')
                print("✅ تم إرسال الرسالة التجريبية بنجاح!")
                print(f"📧 معرف الرسالة: {message_id}")
                return True
            else:
                print(f"❌ فشل إرسال الرسالة: {response.status_code}")
                print(f"📄 الرسالة: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في إرسال الرسالة: {e}")
            return False

def setup_simple_whatsapp():
    """Simple WhatsApp setup using direct phone number"""
    print("📱 إعداد WhatsApp البسيط")
    print("=" * 30)
    print("هذا الإعداد يستخدم WhatsApp Web API البسيط")
    print("⚠️ ملاحظة: هذا للاختبار فقط وقد لا يعمل في الإنتاج")
    
    phone_number = input("📱 أدخل رقم الواتساب (مثال: +966501234567): ").strip()
    
    if not phone_number:
        print("❌ يرجى إدخال رقم صحيح")
        return False
    
    # Save to config
    try:
        config_addition = f"""
# Simple WhatsApp Configuration
SIMPLE_WHATSAPP_NUMBER = '{phone_number}'
SIMPLE_WHATSAPP_ENABLED = True
"""
        
        with open('config.py', 'a', encoding='utf-8') as f:
            f.write(config_addition)
        
        print("✅ تم حفظ رقم الواتساب!")
        print(f"📱 الرقم المحفوظ: {phone_number}")
        
        # Test with WhatsApp Web URL
        test_message = "مرحباً من نظام إدارة مطالبات التأمين!"
        whatsapp_url = f"https://wa.me/{phone_number.replace('+', '')}?text={test_message}"
        
        print(f"\n🔗 رابط الاختبار:")
        print(f"   {whatsapp_url}")
        print("\n💡 يمكنك فتح هذا الرابط لاختبار الإرسال")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الحفظ: {e}")
        return False

def main():
    """Main setup function"""
    print("🔗 إعداد ربط الواتساب بنظام إدارة مطالبات التأمين")
    print("=" * 60)
    
    print("\nاختر طريقة الإعداد:")
    print("1. WhatsApp Business API (الأفضل - للاستخدام المهني)")
    print("2. إعداد بسيط (للاختبار)")
    print("3. عرض الإعدادات الحالية")
    print("4. اختبار الإعدادات الموجودة")
    
    choice = input("\nأدخل اختيارك (1-4): ").strip()
    
    if choice == "1":
        setup = WhatsAppSetup()
        if setup.configure_whatsapp():
            print("\n🧪 هل تريد اختبار الاتصال؟ (y/n)")
            if input().lower() == 'y':
                setup.test_whatsapp_connection()
                
                print("\n📤 هل تريد إرسال رسالة تجريبية؟ (y/n)")
                if input().lower() == 'y':
                    recipient = input("📱 أدخل رقم المستلم (مثال: +966501234567): ")
                    setup.send_test_message(recipient)
    
    elif choice == "2":
        setup_simple_whatsapp()
    
    elif choice == "3":
        print("\n📋 الإعدادات الحالية:")
        print(f"WHATSAPP_ACCESS_TOKEN: {'✅ محدد' if os.environ.get('WHATSAPP_ACCESS_TOKEN') else '❌ غير محدد'}")
        print(f"WHATSAPP_PHONE_NUMBER_ID: {'✅ محدد' if os.environ.get('WHATSAPP_PHONE_NUMBER_ID') else '❌ غير محدد'}")
        print(f"SIMPLE_WHATSAPP_NUMBER: {os.environ.get('SIMPLE_WHATSAPP_NUMBER', '❌ غير محدد')}")
    
    elif choice == "4":
        # Test existing configuration
        setup = WhatsAppSetup()
        setup.access_token = os.environ.get('WHATSAPP_ACCESS_TOKEN')
        setup.phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
        
        if setup.access_token and setup.phone_number_id:
            setup.test_whatsapp_connection()
        else:
            print("❌ لا توجد إعدادات WhatsApp Business API")
            
            simple_number = os.environ.get('SIMPLE_WHATSAPP_NUMBER')
            if simple_number:
                print(f"📱 الرقم البسيط المحفوظ: {simple_number}")
            else:
                print("❌ لا توجد إعدادات واتساب")
    
    else:
        print("❌ اختيار غير صحيح")

if __name__ == "__main__":
    main()
