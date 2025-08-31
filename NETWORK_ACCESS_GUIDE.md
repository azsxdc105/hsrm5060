# 🌐 دليل الوصول للشبكة - Network Access Guide

## نظام إدارة مطالبات التأمين
### Insurance Claims Management System

---

## 🚀 طرق تشغيل النظام للآخرين

### الطريقة الأولى: الشبكة المحلية (الأسهل)

#### للمشغل (صاحب الجهاز):

1. **تشغيل السيرفر:**
   ```bash
   # الطريقة الأولى - استخدام الملف المباشر
   python run_production.py
   
   # الطريقة الثانية - على Windows
   double-click على start_server.bat
   ```

2. **معرفة عنوان IP الخاص بك:**
   - سيظهر العنوان تلقائياً عند تشغيل السيرفر
   - أو استخدم الأمر: `ipconfig` (Windows) أو `ifconfig` (Mac/Linux)

#### للمستخدمين الآخرين:

1. **تأكد من الاتصال بنفس الشبكة** (نفس الواي فاي)
2. **افتح المتصفح واذهب إلى:**
   ```
   http://[IP_ADDRESS]:5000
   
   مثال:
   http://192.168.1.100:5000
   ```

3. **بيانات الدخول الافتراضية:**
   - البريد الإلكتروني: `admin@insurance.com`
   - كلمة المرور: `admin123`

---

## 🔧 إعدادات الشبكة والأمان

### فتح المنافذ في جدار الحماية (Windows):

1. اذهب إلى **Control Panel** → **System and Security** → **Windows Defender Firewall**
2. اضغط على **Advanced settings**
3. اضغط على **Inbound Rules** → **New Rule**
4. اختر **Port** → **TCP** → **Specific local ports: 5000**
5. اختر **Allow the connection**
6. اختر **Domain, Private, Public**
7. اعطِ اسماً للقاعدة: "Insurance Claims System"

### للماك (macOS):
```bash
# السماح بالمنفذ 5000
sudo pfctl -f /etc/pf.conf
```

### للينكس (Linux):
```bash
# فتح المنفذ 5000
sudo ufw allow 5000
```

---

## 🌍 الطريقة الثانية: الوصول عبر الإنترنت

### استخدام ngrok (مجاني):

1. **تحميل ngrok:**
   - اذهب إلى: https://ngrok.com/
   - قم بالتسجيل وتحميل البرنامج

2. **تشغيل النظام محلياً:**
   ```bash
   python run_production.py
   ```

3. **في terminal جديد، شغل ngrok:**
   ```bash
   ngrok http 5000
   ```

4. **انسخ الرابط العام:**
   ```
   https://abc123.ngrok.io
   ```

5. **شارك هذا الرابط مع الآخرين**

### استخدام Heroku (للنشر الدائم):

1. **إنشاء حساب Heroku:**
   - اذهب إلى: https://heroku.com/
   - قم بإنشاء حساب مجاني

2. **تثبيت Heroku CLI:**
   ```bash
   # تحميل من: https://devcenter.heroku.com/articles/heroku-cli
   ```

3. **نشر التطبيق:**
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

---

## 📱 الوصول من الأجهزة المحمولة

### الهواتف والتابلت:

1. **تأكد من الاتصال بنفس الشبكة**
2. **افتح المتصفح (Chrome, Safari, Firefox)**
3. **اذهب إلى العنوان:**
   ```
   http://[IP_ADDRESS]:5000
   ```

### تطبيق PWA (Progressive Web App):

1. **افتح الموقع في المتصفح**
2. **اضغط على "Add to Home Screen"**
3. **سيصبح التطبيق متاحاً كتطبيق منفصل**

---

## 🔐 الأمان والخصوصية

### إعدادات الأمان المهمة:

1. **تغيير كلمة المرور الافتراضية فوراً**
2. **إنشاء حسابات منفصلة للمستخدمين**
3. **تفعيل HTTPS في الإنتاج**
4. **استخدام قاعدة بيانات آمنة**

### متغيرات البيئة للأمان:
```bash
# إنشاء ملف .env
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=your-database-url
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

---

## 🛠️ استكشاف الأخطاء

### المشاكل الشائعة:

#### 1. لا يمكن الوصول من أجهزة أخرى:
- ✅ تأكد من أن الأجهزة على نفس الشبكة
- ✅ تأكد من فتح المنفذ 5000 في جدار الحماية
- ✅ تأكد من تشغيل السيرفر بـ `host='0.0.0.0'`

#### 2. السيرفر لا يعمل:
- ✅ تأكد من تثبيت Python 3.8+
- ✅ تأكد من تثبيت المتطلبات: `pip install -r requirements.txt`
- ✅ تحقق من المنفذ: `netstat -an | findstr :5000`

#### 3. مشاكل قاعدة البيانات:
- ✅ احذف ملف `insurance_claims.db` وأعد التشغيل
- ✅ شغل: `python init_ai_features.py`

#### 4. مشاكل الأذونات:
- ✅ تأكد من تشغيل الـ terminal كـ Administrator
- ✅ تأكد من أذونات الكتابة في مجلد المشروع

---

## 📞 الدعم والمساعدة

### للحصول على المساعدة:

1. **تحقق من ملف logs/insurance_claims.log**
2. **راجع رسائل الخطأ في Terminal**
3. **تأكد من إصدار Python:** `python --version`
4. **تأكد من المتطلبات:** `pip list`

### معلومات النظام:
- **Python Version:** 3.8+
- **Flask Version:** 2.3+
- **Database:** SQLite (افتراضي) / PostgreSQL (إنتاج)
- **Supported Browsers:** Chrome, Firefox, Safari, Edge

---

## 🎯 نصائح للأداء الأفضل

### للشبكة المحلية:
- استخدم كابل إيثرنت بدلاً من الواي فاي للسرعة
- تأكد من قوة إشارة الواي فاي
- أغلق التطبيقات غير المستخدمة

### للخادم:
- استخدم SSD بدلاً من HDD
- تأكد من وجود ذاكرة كافية (4GB+)
- أغلق البرامج الثقيلة أثناء التشغيل

---

## 📋 قائمة التحقق السريعة

- [ ] Python 3.8+ مثبت
- [ ] المتطلبات مثبتة (`pip install -r requirements.txt`)
- [ ] المنفذ 5000 مفتوح في جدار الحماية
- [ ] الأجهزة متصلة بنفس الشبكة
- [ ] السيرفر يعمل بـ `host='0.0.0.0'`
- [ ] تم تغيير كلمة المرور الافتراضية
- [ ] تم إنشاء حسابات للمستخدمين

---

**🎉 مبروك! النظام جاهز للاستخدام من قبل عدة أشخاص!**
