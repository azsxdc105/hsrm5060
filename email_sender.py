#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
برنامج إرسال الملفات عبر البريد الإلكتروني
Email File Sender Script

هذا البرنامج يقوم بإرسال جميع الملفات من مجلد محدد إلى بريد إلكتروني عبر Gmail SMTP
This program sends all files from a specified folder to an email via Gmail SMTP
"""

import os
import smtplib
import getpass
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
السلام عليكم



from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import sys

# ========== إعدادات قابلة للتعديل / Configurable Settings ==========

# مجلد الملفات المراد إرسالها / Folder containing files to send
FOLDER_PATH = "./files_to_send"

# البريد الإلكتروني المرسل إليه / Recipient email address
RECIPIENT_EMAIL = "recipient@example.com"

# البريد الإلكتروني المرسل منه / Sender email address
SENDER_EMAIL = "your_email@gmail.com"

# موضوع الإيميل / Email subject
EMAIL_SUBJECT = "مطالبة جديدة - الملفات مرفقة"

# نص الإيميل / Email body
EMAIL_BODY = """السلام عليكم،

أرفق لكم الملفات المطلوبة.

شكراً."""

# إعدادات Gmail SMTP / Gmail SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# ========== الدوال المساعدة / Helper Functions ==========

def get_email_password():
    """
    الحصول على كلمة مرور البريد الإلكتروني
    Get email password from environment variable or user input
    """
    password = os.getenv("EMAIL_PASSWORD")
    if not password:
        print("لم يتم العثور على كلمة المرور في متغيرات البيئة")
        print("Email password not found in environment variables")
        password = getpass.getpass("أدخل كلمة مرور البريد الإلكتروني / Enter email password: ")
    return password

def get_files_from_folder(folder_path):
    """
    الحصول على جميع الملفات من المجلد المحدد
    Get all files from the specified folder
    """
    try:
        folder = Path(folder_path)
        if not folder.exists():
            print(f"خطأ: المجلد غير موجود: {folder_path}")
            print(f"Error: Folder does not exist: {folder_path}")
            return []
        
        files = []
        for file_path in folder.iterdir():
            if file_path.is_file():
                files.append(file_path)
        
        return files
    except Exception as e:
        print(f"خطأ في قراءة الملفات: {str(e)}")
        print(f"Error reading files: {str(e)}")
        return []

def create_email_message(sender_email, recipient_email, subject, body, files):
    """
    إنشاء رسالة البريد الإلكتروني مع المرفقات
    Create email message with attachments
    """
    try:
        # إنشاء رسالة متعددة الأجزاء / Create multipart message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # إضافة نص الرسالة / Add email body
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # إضافة المرفقات / Add attachments
        for file_path in files:
            try:
                with open(file_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {file_path.name}'
                )
                msg.attach(part)
                
                print(f"تم إرفاق الملف: {file_path.name}")
                print(f"File attached: {file_path.name}")
                
            except Exception as e:
                print(f"خطأ في إرفاق الملف {file_path.name}: {str(e)}")
                print(f"Error attaching file {file_path.name}: {str(e)}")
        
        return msg
    
    except Exception as e:
        print(f"خطأ في إنشاء الرسالة: {str(e)}")
        print(f"Error creating message: {str(e)}")
        return None

def send_email(sender_email, password, recipient_email, message):
    """
    إرسال البريد الإلكتروني عبر Gmail SMTP
    Send email via Gmail SMTP
    """
    try:
        # إنشاء اتصال SSL مع خادم Gmail / Create SSL connection with Gmail server
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        
        # تسجيل الدخول / Login
        server.login(sender_email, password)
        
        # إرسال الرسالة / Send message
        server.send_message(message)
        
        # إغلاق الاتصال / Close connection
        server.quit()
        
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("خطأ في المصادقة: تحقق من البريد الإلكتروني وكلمة المرور")
        print("Authentication error: Check email and password")
        print("تأكد من تفعيل 'كلمات المرور للتطبيقات' في إعدادات Gmail")
        print("Make sure 'App Passwords' is enabled in Gmail settings")
        return False
        
    except smtplib.SMTPException as e:
        print(f"خطأ في إرسال البريد: {str(e)}")
        print(f"SMTP error: {str(e)}")
        return False
        
    except Exception as e:
        print(f"خطأ غير متوقع: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        return False

def main():
    """
    الدالة الرئيسية للبرنامج
    Main program function
    """
    print("=" * 50)
    print("برنامج إرسال الملفات عبر البريد الإلكتروني")
    print("Email File Sender")
    print("=" * 50)
    
    # التحقق من وجود المجلد / Check if folder exists
    if not os.path.exists(FOLDER_PATH):
        print(f"خطأ: المجلد المحدد غير موجود: {FOLDER_PATH}")
        print(f"Error: Specified folder does not exist: {FOLDER_PATH}")
        print("يرجى التأكد من المسار في متغير FOLDER_PATH")
        print("Please check the path in FOLDER_PATH variable")
        return
    
    # الحصول على الملفات / Get files
    print(f"البحث عن الملفات في: {FOLDER_PATH}")
    print(f"Searching for files in: {FOLDER_PATH}")
    
    files = get_files_from_folder(FOLDER_PATH)
    
    if not files:
        print("لم يتم العثور على أي ملفات في المجلد")
        print("No files found in the folder")
        return
    
    print(f"تم العثور على {len(files)} ملف(ات)")
    print(f"Found {len(files)} file(s)")
    
    # عرض الملفات / Display files
    print("\nالملفات المراد إرسالها / Files to be sent:")
    for i, file_path in enumerate(files, 1):
        print(f"{i}. {file_path.name}")
    
    # طلب تأكيد من المستخدم / Ask for user confirmation
    print(f"\nسيتم إرسال الملفات إلى: {RECIPIENT_EMAIL}")
    print(f"Files will be sent to: {RECIPIENT_EMAIL}")
    
    confirm = input("هل تريد المتابعة؟ (y/n) / Continue? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("تم إلغاء العملية / Operation cancelled")
        return
    
    # الحصول على كلمة المرور / Get password
    password = get_email_password()
    if not password:
        print("لم يتم إدخال كلمة المرور / No password provided")
        return
    
    # إنشاء رسالة البريد الإلكتروني / Create email message
    print("\nإنشاء رسالة البريد الإلكتروني...")
    print("Creating email message...")
    
    message = create_email_message(
        SENDER_EMAIL, 
        RECIPIENT_EMAIL, 
        EMAIL_SUBJECT, 
        EMAIL_BODY, 
        files
    )
    
    if not message:
        print("فشل في إنشاء الرسالة / Failed to create message")
        return
    
    # إرسال البريد الإلكتروني / Send email
    print("\nإرسال البريد الإلكتروني...")
    print("Sending email...")
    
    success = send_email(SENDER_EMAIL, password, RECIPIENT_EMAIL, message)
    
    if success:
        print("\n" + "=" * 50)
        print("✅ تم إرسال جميع الملفات بنجاح!")
        print("✅ All files sent successfully!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ فشل في إرسال البريد الإلكتروني")
        print("❌ Failed to send email")
        print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nتم إيقاف البرنامج بواسطة المستخدم")
        print("Program stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nخطأ غير متوقع: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)
