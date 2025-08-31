# 🎨 نشر الموقع على Render (موثوق)

## لماذا Render؟
- ✅ **مجاني** (750 ساعة شهرياً)
- ✅ **موثوق جداً** (99.9% uptime)
- ✅ **سهل الاستخدام**
- ✅ **SSL تلقائي**
- ✅ **نسخ احتياطية**

## الخطوات:

### 1. إنشاء حساب
1. اذهب إلى: https://render.com
2. انقر "Get Started"
3. سجل دخول بـ GitHub

### 2. إنشاء Web Service
1. انقر "New +"
2. اختر "Web Service"
3. اربط مستودع GitHub
4. اختر مشروعك

### 3. الإعدادات
- **Name**: claims-system
- **Environment**: Python 3
- **Build Command**: pip install -r requirements.txt
- **Start Command**: python app.py

### 4. متغيرات البيئة
أضف في "Environment Variables":
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### 5. النشر
- انقر "Create Web Service"
- انتظر 5-10 دقائق
- ستحصل على رابط مثل: https://claims-system.onrender.com