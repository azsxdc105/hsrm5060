# برنامج إرسال الملفات عبر البريد الإلكتروني / Email File Sender

هذا البرنامج يقوم بإرسال جميع الملفات من مجلد محدد إلى بريد إلكتروني عبر Gmail SMTP.

This program sends all files from a specified folder to an email via Gmail SMTP.

## المتطلبات / Requirements

- Python 3.6 أو أحدث / Python 3.6 or newer
- حساب Gmail مع تفعيل "كلمات المرور للتطبيقات" / Gmail account with "App Passwords" enabled

## الإعداد / Setup

### 1. إعداد Gmail / Gmail Setup

1. اذهب إلى إعدادات حساب Google / Go to Google Account settings
2. فعل المصادقة الثنائية / Enable 2-Factor Authentication
3. انتقل إلى "الأمان" > "كلمات المرور للتطبيقات" / Go to "Security" > "App Passwords"
4. أنشئ كلمة مرور جديدة للتطبيق / Create a new app password
5. احفظ كلمة المرور هذه / Save this password

### 2. إعداد البرنامج / Program Setup

1. افتح ملف `email_sender.py` / Open `email_sender.py`
2. عدل المتغيرات التالية / Edit the following variables:
   ```python
   FOLDER_PATH = "./files_to_send"  # مسار المجلد / Folder path
   RECIPIENT_EMAIL = "recipient@example.com"  # البريد المرسل إليه / Recipient email
   SENDER_EMAIL = "your_email@gmail.com"  # بريدك الإلكتروني / Your email
   ```

### 3. إعداد كلمة المرور / Password Setup

#### الطريقة 1: متغير البيئة / Method 1: Environment Variable
```bash
export EMAIL_PASSWORD="your_app_password_here"
