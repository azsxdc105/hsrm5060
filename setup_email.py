#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚙️ أداة إعداد البريد الإلكتروني التفاعلية
تساعدك في إعداد البريد الإلكتروني خطوة بخطوة
"""

import os
import sys
import getpass
from pathlib import Path

def print_header():
    """طباعة رأس البرنامج"""
    print("=" * 60)
    print("⚙️  أداة إعداد البريد الإلكتروني - نظام إدارة المطالبات")
    print("=" * 60)
    print()

def print_gmail_instructions():
    """طباعة تعليمات Gmail"""
    print("📧 تعليمات إعداد Gmail:")
    print("-" * 30)
    print("1. اذهب إلى: https://myaccount.google.com/security")
    print("2. فعّل 'التحقق بخطوتين' إذا لم يكن مفعلاً")
    print("3. اذهب إلى: https://myaccount.google.com/apppasswords")
    print("4. اختر 'Mail' ثم 'Other (Custom name)'")
    print("5. اكتب: 'Claims System'")
    print("6. انسخ كلمة المرور المكونة من 16 رقم")
    print()
    print("⚠️  هام: استخدم App Password وليس كلمة مرور Gmail العادية!")
    print()

def get_email_config():
    """الحصول على إعدادات البريد من المستخدم"""
    config = {}
    
    print("📝 أدخل معلومات البريد الإلكتروني:")
    print()
    
    # نوع البريد
    print("اختر نوع البريد الإلكتروني:")
    print("1. Gmail (موصى به)")
    print("2. Outlook/Hotmail")
    print("3. Yahoo")
    print("4. خادم مخصص")
    
    choice = input("اختر (1-4): ").strip()
    
    if choice == "1":
        # Gmail
        config['server'] = 'smtp.gmail.com'
        config['port'] = '587'
        config['use_tls'] = 'True'
        
        print("\n📧 إعداد Gmail:")
        config['username'] = input("أدخل بريدك الإلكتروني (@gmail.com): ").strip()
        
        if not config['username'].endswith('@gmail.com'):
            config['username'] += '@gmail.com'
        
        print("\n🔑 أدخل App Password (16 رقم من Google):")
        print("   (لن تظهر الأرقام أثناء الكتابة للأمان)")
        config['password'] = getpass.getpass("App Password: ").strip()
        
        config['sender'] = config['username']
        
    elif choice == "2":
        # Outlook
        config['server'] = 'smtp-mail.outlook.com'
        config['port'] = '587'
        config['use_tls'] = 'True'
        
        print("\n📧 إعداد Outlook:")
        config['username'] = input("أدخل بريدك الإلكتروني: ").strip()
        config['password'] = getpass.getpass("كلمة المرور: ").strip()
        config['sender'] = config['username']
        
    elif choice == "3":
        # Yahoo
        config['server'] = 'smtp.mail.yahoo.com'
        config['port'] = '587'
        config['use_tls'] = 'True'
        
        print("\n📧 إعداد Yahoo:")
        config['username'] = input("أدخل بريدك الإلكتروني: ").strip()
        config['password'] = getpass.getpass("كلمة المرور: ").strip()
        config['sender'] = config['username']
        
    else:
        # خادم مخصص
        print("\n🔧 إعداد خادم مخصص:")
        config['server'] = input("عنوان الخادم (مثل: smtp.yourcompany.com): ").strip()
        config['port'] = input("المنفذ (عادة 587 أو 465): ").strip()
        config['use_tls'] = input("استخدام TLS؟ (y/n): ").strip().lower() in ['y', 'yes', 'نعم']
        config['use_tls'] = 'True' if config['use_tls'] else 'False'
        config['username'] = input("اسم المستخدم: ").strip()
        config['password'] = getpass.getpass("كلمة المرور: ").strip()
        config['sender'] = input("البريد المرسل (يمكن أن يكون نفس اسم المستخدم): ").strip()
    
    return config

def create_env_file(config):
    """إنشاء ملف .env"""
    env_content = f"""# 📧 إعدادات البريد الإلكتروني - تم إنشاؤها تلقائياً
MAIL_SERVER={config['server']}
MAIL_PORT={config['port']}
MAIL_USE_TLS={config['use_tls']}
MAIL_USERNAME={config['username']}
MAIL_PASSWORD={config['password']}
MAIL_DEFAULT_SENDER={config['sender']}

# إعدادات أخرى
SECRET_KEY=claims-system-secret-key-{os.urandom(8).hex()}
DATABASE_URL=sqlite:///claims.db
UPLOAD_FOLDER=uploads
MAX_UPLOAD_MB=25

# ميزات متقدمة
AI_ENABLED=true
OCR_ENABLED=true
NOTIFICATIONS_ENABLED=true
"""
    
    env_path = Path('.env')
    
    # نسخ احتياطية إذا كان الملف موجود
    if env_path.exists():
        backup_path = Path('.env.backup')
        env_path.rename(backup_path)
        print(f"📁 تم إنشاء نسخة احتياطية: {backup_path}")
    
    # كتابة الملف الجديد
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ تم إنشاء ملف الإعدادات: {env_path.absolute()}")

def test_configuration():
    """اختبار الإعدادات"""
    print("\n🧪 هل تريد اختبار الإعدادات الآن؟")
    test = input("(y/n): ").strip().lower()
    
    if test in ['y', 'yes', 'نعم', 'ن']:
        print("\n🔄 تشغيل اختبار البريد...")
        try:
            os.system('python test_email.py')
        except:
            print("❌ لم أتمكن من تشغيل الاختبار تلقائياً")
            print("💡 يمكنك تشغيله يدوياً: python test_email.py")

def main():
    """الدالة الرئيسية"""
    print_header()
    
    # التحقق من وجود ملف .env
    if Path('.env').exists():
        print("⚠️  يوجد ملف إعدادات حالي (.env)")
        overwrite = input("هل تريد استبداله؟ (y/n): ").strip().lower()
        if overwrite not in ['y', 'yes', 'نعم', 'ن']:
            print("❌ تم إلغاء العملية")
            return
    
    # عرض تعليمات Gmail
    print_gmail_instructions()
    
    # الحصول على الإعدادات
    config = get_email_config()
    
    # التأكيد
    print("\n📋 ملخص الإعدادات:")
    print(f"   الخادم: {config['server']}")
    print(f"   المنفذ: {config['port']}")
    print(f"   TLS: {config['use_tls']}")
    print(f"   المستخدم: {config['username']}")
    print(f"   المرسل: {config['sender']}")
    print()
    
    confirm = input("هل هذه الإعدادات صحيحة؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم إلغاء العملية")
        return
    
    # إنشاء ملف .env
    create_env_file(config)
    
    # اختبار الإعدادات
    test_configuration()
    
    print("\n🎉 تم إعداد البريد الإلكتروني بنجاح!")
    print("\n🚀 الخطوات التالية:")
    print("1. تشغيل النظام: python app.py")
    print("2. إنشاء مطالبة جديدة")
    print("3. الضغط على 'إرسال' لاختبار الإرسال الفعلي")
    print("\n📧 ستصل المطالبات الآن لشركات التأمين تلقائياً!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ تم إلغاء العملية بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ حدث خطأ: {str(e)}")
        print("💡 تأكد من تشغيل الأداة من مجلد المشروع")