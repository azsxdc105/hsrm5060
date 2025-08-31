@echo off
echo 🌍 بدء تشغيل نظام إدارة مطالبات التأمين للوصول العالمي
echo ================================================================

echo.
echo 🔍 فحص حالة السيرفر...
python -c "import requests; print('✅ السيرفر يعمل' if requests.get('http://127.0.0.1:5000', timeout=3).status_code == 200 else '❌ السيرفر متوقف')" 2>nul

if %errorlevel% neq 0 (
    echo 🚀 بدء تشغيل السيرفر...
    start "Insurance Server" python run.py
    echo ⏳ انتظار بدء السيرفر...
    timeout /t 10 /nobreak >nul
)

echo.
echo 🔍 فحص ngrok...
ngrok version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ngrok غير مثبت
    echo.
    echo 📥 يرجى تحميل ngrok من:
    echo    https://ngrok.com/download
    echo.
    echo 📋 خطوات التثبيت:
    echo 1. حمل ngrok من الرابط أعلاه
    echo 2. فك الضغط في هذا المجلد
    echo 3. سجل حساب مجاني في ngrok.com
    echo 4. احصل على authtoken
    echo 5. شغل: ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

echo ✅ ngrok مثبت ومتاح

echo.
echo 🌐 بدء نفق ngrok...
echo ⚠️ ملاحظة: سيتم فتح نافذة جديدة لـ ngrok
echo.

start "ngrok Tunnel" ngrok http 5000

echo ⏳ انتظار إنشاء النفق...
timeout /t 5 /nobreak >nul

echo.
echo 🔍 الحصول على الرابط العام...
python -c "
import requests
import json
import time

for i in range(10):
    try:
        response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=2)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                public_url = tunnels[0]['public_url']
                print('✅ تم إنشاء النفق بنجاح!')
                print(f'🌍 الرابط العام: {public_url}')
                print(f'📱 اختبار الواتساب: {public_url}/advanced-notifications/whatsapp-test')
                print(f'🔐 لوحة الإدارة: {public_url}/admin')
                print()
                print('👤 بيانات تسجيل الدخول:')
                print('   📧 البريد الإلكتروني: admin@insurance.com')
                print('   🔑 كلمة المرور: admin123')
                print()
                
                # Save to file
                with open('public_url.txt', 'w', encoding='utf-8') as f:
                    f.write(f'Public URL: {public_url}\n')
                    f.write(f'WhatsApp Test: {public_url}/advanced-notifications/whatsapp-test\n')
                    f.write(f'Admin Panel: {public_url}/admin\n')
                    f.write(f'Login: admin@insurance.com / admin123\n')
                
                print('📄 تم حفظ الرابط في ملف public_url.txt')
                break
        time.sleep(1)
    except:
        time.sleep(1)
else:
    print('❌ فشل في الحصول على الرابط العام')
    print('💡 تحقق من نافذة ngrok للحصول على الرابط يدوياً')
"

echo.
echo 🎉 النظام متاح الآن عالمياً!
echo.
echo ⚠️ ملاحظات مهمة:
echo - هذا الرابط مؤقت وسيتغير عند إعادة تشغيل ngrok
echo - لا تشارك بيانات حساسة عبر ngrok
echo - غير كلمة المرور الافتراضية للأمان
echo.
echo 🔄 لإيقاف النظام: أغلق نوافذ ngrok والسيرفر
echo.
pause
