# إعداد Google Vision API

## الخطوات:

### 1. إنشاء مشروع Google Cloud:
1. اذهب إلى: https://console.cloud.google.com/
2. أنشئ مشروع جديد أو اختر مشروع موجود
3. فعل Google Vision API من قائمة APIs & Services

### 2. إنشاء Service Account:
1. اذهب إلى IAM & Admin > Service Accounts
2. أنشئ Service Account جديد
3. أعطه دور "Cloud Vision API User"
4. حمل ملف JSON للمفاتيح

### 3. إعداد المتغيرات:
```bash
# في ملف .env
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
GOOGLE_VISION_API_KEY=your-api-key-here
```

### 4. تثبيت المكتبات:
```bash
pip install google-cloud-vision google-auth
```

## البديل - استخدام API Key:
إذا كنت تفضل استخدام API Key بدلاً من Service Account:

1. اذهب إلى APIs & Services > Credentials
2. أنشئ API Key جديد
3. قيد الـ API Key لـ Vision API فقط
4. أضف الـ API Key في ملف .env:
```
GOOGLE_VISION_API_KEY=your-api-key-here
```