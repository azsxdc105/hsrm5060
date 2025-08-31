import os
import zipfile
from datetime import datetime

print("📦 إنشاء ملف مضغوط للمشروع...")

# Create archive name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
archive_name = f"Insurance_Claims_System_{timestamp}.zip"

# Files to exclude
exclude = {'__pycache__', '.git', 'logs', '.env', 'node_modules'}

try:
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        count = 0
        for root, dirs, files in os.walk('.'):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude]
            
            for file in files:
                if file == archive_name:  # Skip the archive itself
                    continue
                if file.endswith('.pyc') or file.endswith('.log'):
                    continue
                    
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, '.')
                
                zipf.write(file_path, arc_path)
                count += 1
                
                if count % 10 == 0:
                    print(f"تمت إضافة {count} ملف...")
    
    size = os.path.getsize(archive_name) / (1024*1024)
    print(f"✅ تم إنشاء الملف: {archive_name}")
    print(f"📊 عدد الملفات: {count}")
    print(f"💾 حجم الملف: {size:.2f} MB")
    print(f"📍 المسار: {os.path.abspath(archive_name)}")
    
except Exception as e:
    print(f"❌ خطأ: {e}")
