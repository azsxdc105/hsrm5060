# 📧 دليل إعداد البريد الإلكتروني السريع

## 🚀 الطريقة السهلة (موصى بها)

### تشغيل أداة الإعداد التفاعلية:
```bash
python setup_email.py
```

هذه الأداة ستقوم بـ:
- ✅ إرشادك خطوة بخطوة
- ✅ إنشاء ملف الإعدادات تلقائياً
- ✅ اختبار الإعدادات
- ✅ التأكد من عمل كل شيء

---

## 🔧 الطريقة اليدوية

### 1. إعداد Gmail (الأسهل):

#### أ) تفعيل المصادقة الثنائية:
1. اذهب إلى: https://myaccount.google.com/security
2. فعّل "التحقق بخطوتين"

#### ب) إنشاء App Password:
1. اذهب إلى: https://myaccount.google.com/apppasswords
2. اختر "Mail" → "Other"
3. اكتب: "Claims System"
4. احفظ كلمة المرور (16 رقم)

#### ج) تعديل ملف .env:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-digit-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### 2. اختبار الإعدادات:
```bash
python test_email.py
```

### 3. تشغيل النظام:
```bash
python app.py
```

---

## 🏢 إعدادات أخرى

### Outlook/Hotmail:
```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-email@outlook.com
```

### Yahoo:
```env
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@yahoo.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@yahoo.com
```

---

## 🧪 اختبار النظام

### 1. اختبار الاتصال:
```bash
python test_email.py
```

### 2. اختبار إرسال مطالبة:
1. تشغيل النظام: `python app.py`
2. تسجيل الدخول: admin@claims.com / admin123
3. إنشاء مطالبة جديدة
4. إضافة مرفقات
5. الضغط على "إرسال"

---

## ❓ حل المشاكل الشائعة

### Gmail لا يعمل:
- ✅ تأكد من تفعيل المصادقة الثنائية
- ✅ استخدم App Password وليس كلمة المرور العادية
- ✅ تأكد من صحة البريد الإلكتروني

### Outlook لا يعمل:
- ✅ تأكد من تفعيل SMTP في إعدادات Outlook
- ✅ قد تحتاج App Password أيضاً

### خطأ "Authentication failed":
- ✅ تحقق من اسم المستخدم وكلمة المرور
- ✅ تأكد من تفعيل "Less secure app access" (إذا لزم الأمر)

### خطأ "Connection refused":
- ✅ تحقق من عنوان الخادم والمنفذ
- ✅ تأكد من اتصالك بالإنترنت
- ✅ تحقق من إعدادات الجدار الناري

---

## 📞 الدعم

إذا واجهت أي مشكلة:
1. شغّل `python test_email.py` للتشخيص
2. تحقق من الرسائل في وحدة التحكم
3. تأكد من صحة جميع الإعدادات

---

## 🎉 بعد الإعداد

عند نجاح الإعداد:
- ✅ ستُرسل المطالبات تلقائياً لشركات التأمين
- ✅ ستحصل على تأكيد الإرسال
- ✅ سيتم تسجيل كل عملية إرسال
- ✅ يمكن إعادة الإرسال في حالة الفشل

**🚀 النظام جاهز للاستخدام الاحترافي!**