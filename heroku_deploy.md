# 🟣 نشر الموقع على Heroku (الأشهر)

## لماذا Heroku؟
- ✅ **مجاني** (550 ساعة شهرياً)
- ✅ **الأشهر عالمياً**
- ✅ **دعم ممتاز**
- ✅ **إضافات كثيرة**

## الخطوات:

### 1. إنشاء حساب
1. اذهب إلى: https://heroku.com
2. انقر "Sign up"
3. أكمل التسجيل

### 2. تثبيت Heroku CLI
1. اذهب إلى: https://devcenter.heroku.com/articles/heroku-cli
2. حمّل وثبّت Heroku CLI
3. أعد تشغيل الكمبيوتر

### 3. تسجيل الدخول
```bash
heroku login
```

### 4. إنشاء التطبيق
```bash
cd your-project-folder
heroku create claims-system-app
```

### 5. إعداد متغيرات البيئة
```bash
heroku config:set MAIL_SERVER=smtp.gmail.com
heroku config:set MAIL_PORT=587
heroku config:set MAIL_USE_TLS=True
heroku config:set MAIL_USERNAME=your-email@gmail.com
heroku config:set MAIL_PASSWORD=your-app-password
heroku config:set MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### 6. النشر
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### 7. فتح الموقع
```bash
heroku open
```