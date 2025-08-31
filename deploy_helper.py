#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 أداة مساعدة للنشر
تساعدك في تحضير المشروع للنشر على المنصات المختلفة
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header():
    """طباعة رأس البرنامج"""
    print("=" * 60)
    print("🚀 أداة مساعدة النشر - نظام إدارة المطالبات")
    print("=" * 60)
    print()

def check_requirements():
    """التحقق من المتطلبات"""
    print("🔍 فحص المتطلبات...")
    
    required_files = [
        'requirements.txt',
        'Procfile', 
        'runtime.txt',
        '.env'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ ملفات مفقودة:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ جميع الملفات المطلوبة موجودة")
    return True

def check_git():
    """التحقق من Git"""
    print("\n🔍 فحص Git...")
    
    try:
        # Check if git is installed
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        
        # Check if this is a git repository
        if not Path('.git').exists():
            print("❌ هذا ليس مستودع Git")
            print("💡 تشغيل: git init")
            return False
        
        # Check if there are uncommitted changes
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if result.stdout.strip():
            print("⚠️  يوجد تغييرات غير محفوظة")
            print("💡 تشغيل: git add . && git commit -m 'Prepare for deployment'")
            return False
        
        print("✅ Git جاهز")
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Git غير مثبت")
        print("💡 حمّل Git من: https://git-scm.com/")
        return False

def setup_git():
    """إعداد Git"""
    print("\n🔧 إعداد Git...")
    
    try:
        if not Path('.git').exists():
            subprocess.run(['git', 'init'], check=True)
            print("✅ تم إنشاء مستودع Git")
        
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit
        subprocess.run(['git', 'commit', '-m', 'Prepare for deployment'], check=True)
        print("✅ تم حفظ التغييرات")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في Git: {e}")
        return False

def show_deployment_options():
    """عرض خيارات النشر"""
    print("\n🎯 خيارات النشر المتاحة:")
    print()
    
    options = [
        {
            'name': 'Railway',
            'difficulty': '⭐ سهل جداً',
            'free_hours': '500 ساعة/شهر',
            'url': 'https://railway.app',
            'steps': [
                '1. اذهب إلى railway.app',
                '2. سجل دخول بـ GitHub',
                '3. انقر "Deploy from GitHub repo"',
                '4. اختر مشروعك',
                '5. أضف متغيرات البيئة',
                '6. انتظر النشر!'
            ]
        },
        {
            'name': 'Render',
            'difficulty': '⭐⭐ سهل',
            'free_hours': '750 ساعة/شهر',
            'url': 'https://render.com',
            'steps': [
                '1. اذهب إلى render.com',
                '2. انقر "New +" → "Web Service"',
                '3. اربط GitHub واختر المشروع',
                '4. Build Command: pip install -r requirements.txt',
                '5. Start Command: python app.py',
                '6. أضف متغيرات البيئة',
                '7. انقر "Create Web Service"'
            ]
        },
        {
            'name': 'Heroku',
            'difficulty': '⭐⭐⭐ متوسط',
            'free_hours': '550 ساعة/شهر',
            'url': 'https://heroku.com',
            'steps': [
                '1. إنشاء حساب في heroku.com',
                '2. تثبيت Heroku CLI',
                '3. heroku login',
                '4. heroku create your-app-name',
                '5. إعداد متغيرات البيئة',
                '6. git push heroku main'
            ]
        }
    ]
    
    for i, option in enumerate(options, 1):
        print(f"🥇 {option['name']}")
        print(f"   الصعوبة: {option['difficulty']}")
        print(f"   مجاني: {option['free_hours']}")
        print(f"   الرابط: {option['url']}")
        print("   الخطوات:")
        for step in option['steps']:
            print(f"      {step}")
        print()

def show_environment_variables():
    """عرض متغيرات البيئة المطلوبة"""
    print("⚙️ متغيرات البيئة المطلوبة:")
    print("-" * 40)
    
    variables = {
        'MAIL_SERVER': 'smtp.gmail.com',
        'MAIL_PORT': '587',
        'MAIL_USE_TLS': 'True',
        'MAIL_USERNAME': 'your-email@gmail.com',
        'MAIL_PASSWORD': 'your-16-digit-app-password',
        'MAIL_DEFAULT_SENDER': 'your-email@gmail.com',
        'SECRET_KEY': 'your-secret-key-here'
    }
    
    for key, example in variables.items():
        print(f"{key}={example}")
    
    print()
    print("⚠️  هام: استبدل القيم بمعلوماتك الحقيقية!")
    print("🔑 للحصول على App Password:")
    print("   1. https://myaccount.google.com/security")
    print("   2. فعّل 'التحقق بخطوتين'")
    print("   3. https://myaccount.google.com/apppasswords")
    print("   4. اختر Mail → Other → Claims System")

def create_deployment_checklist():
    """إنشاء قائمة مراجعة النشر"""
    checklist = """
# ✅ قائمة مراجعة النشر

## قبل النشر:
- [ ] تم إعداد البريد الإلكتروني محلياً
- [ ] تم اختبار النظام محلياً
- [ ] تم إنشاء App Password لـ Gmail
- [ ] تم حفظ جميع التغييرات في Git

## أثناء النشر:
- [ ] تم اختيار المنصة (Railway موصى به)
- [ ] تم ربط مستودع GitHub
- [ ] تم إضافة متغيرات البيئة
- [ ] تم انتظار اكتمال النشر

## بعد النشر:
- [ ] تم فتح الرابط والتأكد من عمل الموقع
- [ ] تم تسجيل الدخول (admin@claims.com / admin123)
- [ ] تم إنشاء مطالبة تجريبية
- [ ] تم اختبار إرسال المطالبة
- [ ] تم التأكد من وصول الإيميل

## في حالة المشاكل:
- [ ] مراجعة logs المنصة
- [ ] التأكد من متغيرات البيئة
- [ ] اختبار الإعدادات محلياً
- [ ] مراجعة دليل حل المشاكل

## معلومات مهمة للحفظ:
- رابط الموقع: ________________
- اسم المشروع: ________________
- المنصة المستخدمة: ________________
- تاريخ النشر: ________________
"""
    
    with open('deployment_checklist.md', 'w', encoding='utf-8') as f:
        f.write(checklist)
    
    print("📋 تم إنشاء قائمة مراجعة النشر: deployment_checklist.md")

def main():
    """الدالة الرئيسية"""
    print_header()
    
    # Check requirements
    if not check_requirements():
        print("\n💡 تشغيل أولاً: python setup_email.py")
        return
    
    # Check Git
    git_ready = check_git()
    if not git_ready:
        setup_git_now = input("\nهل تريد إعداد Git الآن؟ (y/n): ").lower().strip()
        if setup_git_now in ['y', 'yes', 'نعم', 'ن']:
            if not setup_git():
                return
        else:
            print("❌ Git مطلوب للنشر")
            return
    
    # Show deployment options
    show_deployment_options()
    
    # Show environment variables
    print()
    show_environment_variables()
    
    # Create checklist
    print()
    create_checklist = input("هل تريد إنشاء قائمة مراجعة النشر؟ (y/n): ").lower().strip()
    if create_checklist in ['y', 'yes', 'نعم', 'ن']:
        create_deployment_checklist()
    
    print("\n🎉 المشروع جاهز للنشر!")
    print("\n🚀 الخطوات التالية:")
    print("1. اختر منصة النشر (Railway موصى به)")
    print("2. اتبع الخطوات المذكورة أعلاه")
    print("3. أضف متغيرات البيئة")
    print("4. انتظر اكتمال النشر")
    print("5. اختبر الموقع")
    
    print("\n💡 للمساعدة:")
    print("- اقرأ DEPLOY_GUIDE.md")
    print("- راجع deployment_checklist.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ تم إلغاء العملية")
    except Exception as e:
        print(f"\n❌ حدث خطأ: {str(e)}")