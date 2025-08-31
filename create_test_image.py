#!/usr/bin/env python3
"""
Create a test image with Arabic text for OCR testing
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    """Create a test image with Arabic claim data"""
    try:
        # Create a white image
        width, height = 800, 600
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Try to use a font that supports Arabic
        try:
            # Try to find Arial font (usually supports Arabic)
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_medium = ImageFont.truetype("arial.ttf", 18)
        except:
            try:
                # Fallback to default font
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
            except:
                font_large = None
                font_medium = None
        
        # Arabic text content
        text_lines = [
            "تقرير حادث مروري",
            "",
            "رقم الحادث: ACC-2025-001",
            "التاريخ: 2025-01-21",
            "اسم المؤمن له: محمد أحمد السعيد",
            "رقم الهوية: 1234567890",
            "رقم الوثيقة: POL-2025-12345",
            "مبلغ الضرر: 25000 ريال سعودي",
            "نوع التغطية: شامل",
            "المدينة: الرياض",
            "",
            "وصف الحادث:",
            "تصادم مع مركبة أخرى في تقاطع الملك فهد",
            "أثناء التوقف عند الإشارة الضوئية"
        ]
        
        # Draw text on image
        y_position = 50
        for i, line in enumerate(text_lines):
            if line.strip():  # Skip empty lines
                font_to_use = font_large if i == 0 else font_medium
                if font_to_use:
                    draw.text((50, y_position), line, fill='black', font=font_to_use)
                else:
                    draw.text((50, y_position), line, fill='black')
            y_position += 35
        
        # Add a border
        draw.rectangle([(10, 10), (width-10, height-10)], outline='black', width=2)
        
        # Save the image
        image_path = os.path.join('uploads', 'test_claim_document.png')
        os.makedirs('uploads', exist_ok=True)
        image.save(image_path)
        
        print(f"✅ تم إنشاء صورة الاختبار: {image_path}")
        return image_path
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الصورة: {e}")
        return None

def test_ocr_with_image():
    """Test OCR with the created image"""
    from app import create_app
    from app.ocr_utils import extract_text_from_image, extract_claim_data_from_file
    
    app = create_app()
    
    with app.app_context():
        # Create test image
        image_path = create_test_image()
        
        if image_path and os.path.exists(image_path):
            print("\n🔍 اختبار OCR مع الصورة المُنشأة:")
            print("=" * 50)
            
            # Test OCR on the image
            result = extract_text_from_image(image_path)
            
            if result.get('success'):
                print(f"✅ نجح OCR!")
                print(f"   - الطريقة: {result.get('method', 'غير محدد')}")
                print(f"   - مستوى الثقة: {result.get('confidence', 0):.1f}")
                print(f"   - النص المستخرج:")
                print("   " + "-" * 30)
                for line in result.get('text', '').split('\n')[:10]:  # Show first 10 lines
                    if line.strip():
                        print(f"   {line.strip()}")
                print("   " + "-" * 30)
                
                # Test claim data extraction
                print("\n📋 اختبار استخراج بيانات المطالبة:")
                file_result = extract_claim_data_from_file(image_path)
                
                if file_result.get('success'):
                    print("✅ نجح استخراج البيانات!")
                    data = file_result.get('extracted_data', {})
                    print(f"   - اسم العميل: {data.get('client_name', 'غير محدد')}")
                    print(f"   - رقم الهوية: {data.get('client_national_id', 'غير محدد')}")
                    print(f"   - رقم الوثيقة: {data.get('policy_number', 'غير محدد')}")
                    print(f"   - رقم الحادث: {data.get('incident_number', 'غير محدد')}")
                    print(f"   - مستوى الثقة: {file_result.get('extraction_confidence', 0):.1f}%")
                else:
                    print(f"❌ فشل استخراج البيانات: {file_result.get('error', 'خطأ غير معروف')}")
                    
            else:
                print(f"❌ فشل OCR: {result.get('error', 'خطأ غير معروف')}")
            
            print("=" * 50)
        else:
            print("❌ لم يتم إنشاء الصورة")

if __name__ == "__main__":
    test_ocr_with_image()
