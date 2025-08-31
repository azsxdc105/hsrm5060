# دليل تفعيل OCR - نظام إدارة مطالبات التأمين

## الحالة الحالية ✅
- ✅ **Simple OCR**: يعمل (نصوص تجريبية)
- ✅ **Enhanced OCR**: يعمل (نمط مطابقة)
- ❌ **Tesseract OCR**: غير مفعل
- ❌ **Google Vision API**: غير مفعل

---

## 1. تفعيل Tesseract OCR

### الطريقة الأولى: التحميل اليدوي (مُوصى بها)

1. **تحميل Tesseract:**
   ```
   https://github.com/UB-Mannheim/tesseract/wiki
   ```
   - حمل: `tesseract-ocr-w64-setup-5.3.0.exe`

2. **التثبيت:**
   - شغل الملف كـ Administrator
   - اختر مسار التثبيت: `C:\Program Files\Tesseract-OCR`
   - **مهم**: في Additional Language Data اختر:
     - ✅ Arabic
     - ✅ English
     - ✅ Arabic script detection

3. **إضافة لـ PATH:**
   ```powershell
   # في PowerShell كـ Administrator
   $env:PATH += ";C:\Program Files\Tesseract-OCR"
   [Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\Program Files\Tesseract-OCR", "Machine")
   ```

4. **اختبار التثبيت:**
   ```powershell
   tesseract --version
   tesseract --list-langs
   ```

### الطريقة الثانية: استخدام Chocolatey

```powershell
# تثبيت Chocolatey أولاً
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# تثبيت Tesseract
choco install tesseract
```

---

## 2. تفعيل Google Vision API

### الخطوة 1: إنشاء مشروع Google Cloud

1. اذهب إلى: https://console.cloud.google.com/
2. أنشئ مشروع جديد أو اختر مشروع موجود
3. فعل Google Vision API:
   - APIs & Services > Library
   - ابحث عن "Vision API"
   - اضغط Enable

### الخطوة 2: إنشاء مفاتيح الوصول

#### الطريقة الأولى: Service Account (مُوصى بها)

1. اذهب إلى: IAM & Admin > Service Accounts
2. اضغط "Create Service Account"
3. أدخل اسم الحساب
4. في Roles، اختر: "Cloud Vision API User"
5. اضغط "Create Key" > JSON
6. حمل ملف JSON

#### الطريقة الثانية: API Key

1. اذهب إلى: APIs & Services > Credentials
2. اضغط "Create Credentials" > API Key
3. قيد الـ API Key لـ Vision API فقط

### الخطوة 3: تحديث إعدادات المشروع

```bash
# في ملف .env
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json
# أو
GOOGLE_VISION_API_KEY=your-api-key-here
```

---

## 3. اختبار التفعيل

```bash
# في مجلد المشروع
python test_ocr_setup.py
```

---

## 4. استخدام OCR في النظام

### رفع مستند مع OCR:
1. اذهب إلى: http://localhost:5000/claims/new_with_ocr
2. ارفع صورة أو PDF
3. سيتم استخراج البيانات تلقائياً

### أنواع الملفات المدعومة:
- ✅ PNG, JPG, JPEG
- ✅ PDF (مع Tesseract)
- ✅ TIFF, BMP

### البيانات المستخرجة:
- اسم المؤمن له
- رقم الهوية
- رقم الوثيقة
- رقم الحادث
- تاريخ الحادث
- مبلغ الضرر
- نوع التغطية
- المدينة

---

## 5. استكشاف الأخطاء

### مشكلة: "Tesseract not found"
```bash
# تحقق من التثبيت
where tesseract
tesseract --version

# إضافة لـ PATH يدوياً
set PATH=%PATH%;C:\Program Files\Tesseract-OCR
```

### مشكلة: "Google Vision API failed"
```bash
# تحقق من المتغيرات
echo $GOOGLE_APPLICATION_CREDENTIALS
echo $GOOGLE_VISION_API_KEY

# تحقق من صحة ملف JSON
python -c "import json; print(json.load(open('path/to/key.json')))"
```

### مشكلة: "Arabic text not recognized"
```bash
# تحقق من اللغات المثبتة
tesseract --list-langs

# يجب أن تظهر: ara, eng
```

---

## 6. تحسين الأداء

### لـ Tesseract:
```python
# في config.py
OCR_CONFIG = '--oem 3 --psm 6 -l ara+eng'
OCR_CONFIDENCE_THRESHOLD = 0.7
```

### لـ Google Vision:
```python
# في .env
GOOGLE_VISION_FEATURES=TEXT_DETECTION,DOCUMENT_TEXT_DETECTION
```

---

## 7. الحالة المتوقعة بعد التفعيل

```
✅ Simple OCR: Available
✅ Tesseract OCR: Available
   Path: C:\Program Files\Tesseract-OCR\tesseract.exe
   Languages: ['ara', 'eng', 'osd', ...]
✅ Enhanced OCR: Available
   Engines: ['google_vision', 'tesseract', 'pattern_matching']
   Google Vision: True
   Tesseract: True
```

---

## 8. الدعم والمساعدة

إذا واجهت أي مشاكل:
1. شغل `python test_ocr_setup.py` للتشخيص
2. تحقق من ملفات السجل في `logs/`
3. تأكد من صحة إعدادات `.env`

---

**ملاحظة**: النظام يعمل حالياً بـ OCR أساسي. تفعيل Tesseract و Google Vision سيحسن دقة استخراج النصوص بشكل كبير.