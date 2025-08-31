#!/usr/bin/env python3
"""
Test OCR functionality
"""
from app import create_app
from app.ocr_utils import (
    extract_text_from_image, 
    extract_claim_data_from_text, 
    get_ocr_status, 
    is_ocr_available,
    extract_claim_data_from_file
)

def test_ocr_functionality():
    """Test OCR functionality"""
    app = create_app()
    
    with app.app_context():
        print("🔍 اختبار ميزة OCR")
        print("=" * 50)
        
        # Test 1: Check OCR status
        print("1️⃣ فحص حالة OCR:")
        status = get_ocr_status()
        print(f"   - متاح: {is_ocr_available()}")
        print(f"   - المحركات المتاحة: {status.get('engines', [])}")
        print(f"   - Google Vision: {status.get('google_vision', False)}")
        print(f"   - Tesseract: {status.get('tesseract', False)}")
        print()
        
        # Test 2: Extract data from sample text
        print("2️⃣ اختبار استخراج البيانات من النص:")
        sample_text = """
        تقرير حادث مروري
        رقم الحادث: ACC-2025-001
        التاريخ: 2025-01-21
        اسم المؤمن له: محمد أحمد السعيد
        رقم الهوية: 1234567890
        رقم الوثيقة: POL-2025-12345
        مبلغ الضرر: 25000 ريال سعودي
        نوع التغطية: شامل
        المدينة: الرياض
        وصف الحادث: تصادم مع مركبة أخرى
        """
        
        result = extract_claim_data_from_text(sample_text)
        if result.get('success'):
            data = result['data']
            print(f"   ✅ نجح الاستخراج!")
            print(f"   - اسم العميل: {data.get('client_name', 'غير محدد')}")
            print(f"   - رقم الهوية: {data.get('client_national_id', 'غير محدد')}")
            print(f"   - رقم الوثيقة: {data.get('policy_number', 'غير محدد')}")
            print(f"   - رقم الحادث: {data.get('incident_number', 'غير محدد')}")
            print(f"   - مستوى الثقة: {data.get('confidence', 0):.1f}%")
            print(f"   - الحقول المستخرجة: {result.get('extracted_fields', 0)}/{result.get('total_fields', 0)}")
        else:
            print(f"   ❌ فشل الاستخراج: {result.get('error', 'خطأ غير معروف')}")
        print()
        
        # Test 3: Test image OCR (mock)
        print("3️⃣ اختبار OCR للصور:")
        # Since we don't have a real image, we'll test with a non-existent file
        # This will trigger the pattern matching fallback
        image_result = extract_text_from_image("non_existent_image.jpg")
        if image_result.get('success'):
            print(f"   ✅ نجح OCR للصورة!")
            print(f"   - الطريقة المستخدمة: {image_result.get('method', 'غير محدد')}")
            print(f"   - مستوى الثقة: {image_result.get('confidence', 0):.1f}")
            print(f"   - طول النص: {len(image_result.get('text', ''))}")
        else:
            print(f"   ❌ فشل OCR للصورة: {image_result.get('error', 'خطأ غير معروف')}")
        print()
        
        # Test 4: Test file processing
        print("4️⃣ اختبار معالجة الملفات:")
        file_result = extract_claim_data_from_file("non_existent_file.jpg")
        if file_result.get('success'):
            print(f"   ✅ نجحت معالجة الملف!")
            print(f"   - الطريقة: {file_result.get('ocr_method', 'غير محدد')}")
            print(f"   - البيانات المستخرجة: {len(file_result.get('extracted_data', {}))}")
        else:
            print(f"   ❌ فشلت معالجة الملف: {file_result.get('error', 'خطأ غير معروف')}")
        print()
        
        print("=" * 50)
        print("✅ انتهى اختبار OCR")

if __name__ == "__main__":
    test_ocr_functionality()
