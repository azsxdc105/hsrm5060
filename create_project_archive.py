#!/usr/bin/env python3
"""
Create Project Archive - Insurance Claims Management System
إنشاء أرشيف مضغوط للمشروع
"""
import os
import zipfile
import shutil
from datetime import datetime
import sys

def create_project_archive():
    """Create a compressed archive of the entire project"""
    
    print("📦 إنشاء أرشيف مضغوط لنظام إدارة مطالبات التأمين")
    print("=" * 60)
    
    # Get current directory (project root)
    project_root = os.getcwd()
    project_name = os.path.basename(project_root)
    
    # Create archive filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"Insurance_Claims_System_{timestamp}.zip"
    
    print(f"📁 مجلد المشروع: {project_root}")
    print(f"📦 اسم الأرشيف: {archive_name}")
    print()
    
    # Files and directories to exclude
    exclude_patterns = {
        '__pycache__',
        '.git',
        '.gitignore',
        'node_modules',
        '.env',
        '*.pyc',
        '*.pyo',
        '*.log',
        'logs',
        '.DS_Store',
        'Thumbs.db',
        '.vscode',
        '.idea',
        '*.tmp',
        '*.temp'
    }
    
    # Files to definitely include (important files)
    important_files = [
        'run.py',
        'run_global.py',
        'config.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'docker-compose-simple.yml',
        'Procfile',
        'runtime.txt',
        '.env.example',
        'README.md',
        'README_SYSTEM.md',
        'USER_MANUAL.md',
        'GLOBAL_ACCESS_GUIDE.md',
        'WHATSAPP_INTEGRATION_GUIDE.md',
        'FINAL_SYSTEM_REPORT.md',
        'CLOUD_DEPLOYMENT_GUIDE.md',
        'GLOBAL_ACCESS_SUMMARY.md',
        'NETWORK_ACCESS_GUIDE.md'
    ]
    
    def should_exclude(file_path, filename):
        """Check if file should be excluded"""
        # Check exclude patterns
        for pattern in exclude_patterns:
            if pattern in file_path or pattern in filename:
                if not pattern.startswith('*'):
                    return True
                elif pattern.startswith('*.') and filename.endswith(pattern[1:]):
                    return True
        
        # Always include important files
        if filename in important_files:
            return False
            
        return False
    
    try:
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            files_added = 0
            total_size = 0
            
            print("📂 إضافة الملفات للأرشيف...")
            
            for root, dirs, files in os.walk(project_root):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_root)
                    
                    # Skip the archive file itself
                    if file == archive_name:
                        continue
                    
                    # Check if file should be excluded
                    if should_exclude(relative_path, file):
                        continue
                    
                    try:
                        # Add file to archive
                        zipf.write(file_path, relative_path)
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        files_added += 1
                        
                        # Show progress for important files
                        if file in important_files or files_added % 50 == 0:
                            print(f"   ✅ {relative_path}")
                            
                    except Exception as e:
                        print(f"   ⚠️ تخطي {relative_path}: {e}")
            
            print(f"\n📊 إحصائيات الأرشيف:")
            print(f"   📁 عدد الملفات: {files_added}")
            print(f"   💾 الحجم الإجمالي: {total_size / (1024*1024):.2f} MB")
            
        # Get archive size
        archive_size = os.path.getsize(archive_name)
        compression_ratio = (1 - archive_size / total_size) * 100 if total_size > 0 else 0
        
        print(f"   🗜️ حجم الأرشيف: {archive_size / (1024*1024):.2f} MB")
        print(f"   📉 نسبة الضغط: {compression_ratio:.1f}%")
        
        print(f"\n✅ تم إنشاء الأرشيف بنجاح!")
        print(f"📦 اسم الملف: {archive_name}")
        print(f"📍 المسار الكامل: {os.path.abspath(archive_name)}")
        
        # Create info file
        create_archive_info(archive_name, files_added, total_size, archive_size)
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الأرشيف: {e}")
        return False

def create_archive_info(archive_name, files_count, total_size, archive_size):
    """Create information file about the archive"""
    info_filename = archive_name.replace('.zip', '_INFO.txt')
    
    try:
        with open(info_filename, 'w', encoding='utf-8') as f:
            f.write("📦 معلومات أرشيف نظام إدارة مطالبات التأمين\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"📅 تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"📦 اسم الأرشيف: {archive_name}\n")
            f.write(f"📁 عدد الملفات: {files_count}\n")
            f.write(f"💾 الحجم الأصلي: {total_size / (1024*1024):.2f} MB\n")
            f.write(f"🗜️ حجم الأرشيف: {archive_size / (1024*1024):.2f} MB\n")
            f.write(f"📉 نسبة الضغط: {((1 - archive_size / total_size) * 100):.1f}%\n\n")
            
            f.write("📋 محتويات المشروع:\n")
            f.write("-" * 25 + "\n")
            f.write("✅ نظام إدارة مطالبات التأمين الكامل\n")
            f.write("✅ تكامل الواتساب للإشعارات\n")
            f.write("✅ الذكاء الاصطناعي لتصنيف المطالبات\n")
            f.write("✅ نظام الإشعارات المتقدم\n")
            f.write("✅ إعدادات الوصول العالمي\n")
            f.write("✅ ملفات Docker للنشر\n")
            f.write("✅ أدلة الاستخدام الشاملة\n")
            f.write("✅ سكريبتات التشغيل والإعداد\n\n")
            
            f.write("🚀 طرق التشغيل:\n")
            f.write("-" * 15 + "\n")
            f.write("1. فك الضغط عن الملف\n")
            f.write("2. تثبيت المتطلبات: pip install -r requirements.txt\n")
            f.write("3. تشغيل النظام: python run.py\n")
            f.write("4. فتح المتصفح: http://127.0.0.1:5000\n")
            f.write("5. تسجيل الدخول: admin@insurance.com / admin123\n\n")
            
            f.write("🌍 للوصول العالمي:\n")
            f.write("-" * 17 + "\n")
            f.write("- استخدم ngrok: ngrok http 5000\n")
            f.write("- أو انشر على Railway/Render/Heroku\n")
            f.write("- راجع GLOBAL_ACCESS_GUIDE.md\n\n")
            
            f.write("📱 اختبار الواتساب:\n")
            f.write("-" * 17 + "\n")
            f.write("- اذهب إلى: /advanced-notifications/whatsapp-test\n")
            f.write("- أدخل رقم الواتساب واختبر الإرسال\n\n")
            
            f.write("📚 الأدلة المتاحة:\n")
            f.write("-" * 16 + "\n")
            f.write("- USER_MANUAL.md - دليل المستخدم\n")
            f.write("- GLOBAL_ACCESS_GUIDE.md - دليل الوصول العالمي\n")
            f.write("- WHATSAPP_INTEGRATION_GUIDE.md - دليل الواتساب\n")
            f.write("- CLOUD_DEPLOYMENT_GUIDE.md - دليل النشر السحابي\n")
            f.write("- FINAL_SYSTEM_REPORT.md - التقرير الفني\n\n")
            
            f.write("⚠️ ملاحظات مهمة:\n")
            f.write("-" * 15 + "\n")
            f.write("- غير كلمة المرور الافتراضية للأمان\n")
            f.write("- راجع ملف .env.example للإعدادات\n")
            f.write("- تأكد من تثبيت Python 3.8+\n")
            f.write("- للدعم الفني راجع الأدلة المرفقة\n\n")
            
            f.write("🎉 النظام جاهز للاستخدام الفوري!\n")
        
        print(f"📄 تم إنشاء ملف المعلومات: {info_filename}")
        
    except Exception as e:
        print(f"⚠️ لم يتم إنشاء ملف المعلومات: {e}")

def main():
    """Main function"""
    print("🏢 نظام إدارة مطالبات التأمين")
    print("📦 أداة إنشاء الأرشيف المضغوط")
    print()
    
    # Confirm with user
    response = input("هل تريد إنشاء أرشيف مضغوط للمشروع؟ (y/n): ").lower().strip()
    
    if response in ['y', 'yes', 'نعم', 'ن']:
        success = create_project_archive()
        
        if success:
            print("\n🎉 تم إنشاء الأرشيف بنجاح!")
            print("📦 يمكنك الآن مشاركة الملف المضغوط مع الآخرين")
            print("🚀 النظام جاهز للتشغيل فور فك الضغط")
        else:
            print("\n❌ فشل في إنشاء الأرشيف")
            return 1
    else:
        print("❌ تم إلغاء العملية")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
