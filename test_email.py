#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 أداة اختبار البريد الإلكتروني
تستخدم لاختبار إعدادات البريد قبل تشغيل النظام
"""

import os
import sys
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_email_config():
    """تحميل إعدادات البريد من ملف .env"""
    load_dotenv()
    
    config = {
        'server': os.getenv('MAIL_SERVER'),
        'port': int(os.getenv('MAIL_PORT', 587)),
        'use_tls': os.getenv('MAIL_USE_TLS', 'True').lower() == 'true',
        'username': os.getenv('MAIL_USERNAME'),
        'password': os.getenv('MAIL_PASSWORD'),
        'sender': os.getenv('MAIL_DEFAULT_SENDER')
    }
    
    return config

def test_email_connection(config):
    """اختبار الاتصال بخادم البريد"""
    print("🔍 اختبار الاتصال بخادم البريد...")
    
    try:
        # إنشاء اتصال SMTP
        server = smtplib.SMTP(config['server'], config['port'])
        
        if config['use_tls']:
            server.starttls()
        
        # تسجيل الدخول
        server.login(config['username'], config['password'])
        
        print("✅ نجح الاتصال بخادم البريد!")
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ فشل الاتصال: {str(e)}")
        return False

def send_test_email(config, recipient=None):
    """إرسال إيميل تجريبي"""
    if not recipient:
        recipient = config['username']  # إرسال لنفس البريد
    
    print(f"📧 إرسال إيميل تجريبي إلى: {recipient}")
    
    try:
        # إنشاء الرسالة
        msg = MIMEMultipart()
        msg['From'] = config['sender']
        msg['To'] = recipient
        msg['Subject'] = "🧪 اختبار نظام المطالبات - Test Email"
        
        body = """
        مرحباً!
        
        هذا إيميل تجريبي من نظام إدارة المطالبات.
        
        إذا وصلك هذا الإيميل، فهذا يعني أن إعدادات البريد الإلكتروني تعمل بشكل صحيح! ✅
        
        تفاصيل الاختبار:
        - الخادم: {server}
        - المنفذ: {port}
        - TLS: {tls}
        - المرسل: {sender}
        
        مع أطيب التحيات,
        نظام إدارة المطالبات 🚀
        
        ---
        
        Hello!
        
        This is a test email from the Claims Management System.
        
        If you received this email, it means your email settings are working correctly! ✅
        
        Test Details:
        - Server: {server}
        - Port: {port}
        - TLS: {tls}
        - Sender: {sender}
        
        Best regards,
        Claims Management System 🚀
        """.format(
            server=config['server'],
            port=config['port'],
            tls="نعم" if config['use_tls'] else "لا",
            sender=config['sender']
        )
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # إرسال الإيميل
        server = smtplib.SMTP(config['server'], config['port'])
        
        if config['use_tls']:
            server.starttls()
        
        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()
        
        print("✅ تم إرسال الإيميل التجريبي بنجاح!")
        print(f"📬 تحقق من صندوق الوارد: {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ فشل إرسال الإيميل: {str(e)}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🧪 أداة اختبار البريد الإلكتروني")
    print("=" * 50)
    
    # تحميل الإعدادات
    config = load_email_config()
    
    # التحقق من الإعدادات
    missing_configs = []
    for key, value in config.items():
        if not value:
            missing_configs.append(key)
    
    if missing_configs:
        print("❌ إعدادات مفقودة:")
        for key in missing_configs:
            print(f"   - {key}")
        print("\n💡 تأكد من تعديل ملف .env بالمعلومات الصحيحة")
        return
    
    print("📋 الإعدادات المحملة:")
    print(f"   - الخادم: {config['server']}")
    print(f"   - المنفذ: {config['port']}")
    print(f"   - TLS: {'نعم' if config['use_tls'] else 'لا'}")
    print(f"   - المستخدم: {config['username']}")
    print(f"   - كلمة المرور: {'محددة' if config['password'] else 'غير محددة'}")
    print(f"   - المرسل: {config['sender']}")
    print()
    
    # اختبار الاتصال
    if not test_email_connection(config):
        print("\n💡 نصائح لحل المشكلة:")
        print("1. تأكد من صحة بريدك الإلكتروني وكلمة المرور")
        print("2. إذا كنت تستخدم Gmail، تأكد من استخدام App Password")
        print("3. تأكد من تفعيل المصادقة الثنائية في Gmail")
        print("4. تحقق من اتصالك بالإنترنت")
        return
    
    # إرسال إيميل تجريبي
    print()
    send_test = input("هل تريد إرسال إيميل تجريبي؟ (y/n): ").lower().strip()
    
    if send_test in ['y', 'yes', 'نعم', 'ن']:
        recipient = input(f"أدخل البريد المستلم (اتركه فارغاً لاستخدام {config['username']}): ").strip()
        if not recipient:
            recipient = config['username']
        
        if send_test_email(config, recipient):
            print("\n🎉 تم الاختبار بنجاح!")
            print("✅ يمكنك الآن تشغيل النظام وسيعمل إرسال المطالبات بشكل طبيعي")
        else:
            print("\n❌ فشل الاختبار")
    
    print("\n🚀 لتشغيل النظام:")
    print("   python app.py")

if __name__ == "__main__":
    main()