# 📧 دليل إعداد Gmail للنظام

## الخطوة 1: تفعيل المصادقة الثنائية
1. اذهب إلى: https://myaccount.google.com/security
2. في قسم "تسجيل الدخول إلى Google"
3. انقر على "التحقق بخطوتين"
4. اتبع التعليمات لتفعيلها

## الخطوة 2: إنشاء App Password
1. بعد تفعيل المصادقة الثنائية
2. اذهب إلى: https://myaccount.google.com/apppasswords
3. اختر "Mail" من القائمة المنسدلة
4. اختر "Windows Computer" أو "Other"
5. اكتب اسم التطبيق: "Claims System"
6. انقر "Generate"
7. **احفظ كلمة المرور المكونة من 16 رقم**

## الخطوة 3: استخدام الإعدادات
- MAIL_SERVER: smtp.gmail.com
- MAIL_PORT: 587
- MAIL_USE_TLS: True
- MAIL_USERNAME: your-email@gmail.com
- MAIL_PASSWORD: [App Password من الخطوة 2]
- MAIL_DEFAULT_SENDER: your-email@gmail.com