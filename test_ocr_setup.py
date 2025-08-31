#!/usr/bin/env python3
"""
Test OCR setup and functionality
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_image():
    """Create a test image with Arabic and English text"""
    # Create image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font that supports Arabic
    try:
        # Try to find Arial font (usually supports Arabic)
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_medium = ImageFont.truetype("arial.ttf", 18)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # Add text content
    texts = [
        ("تقرير حادث مروري", 50, 50),
        ("Traffic Accident Report", 50, 80),
        ("رقم الحادث: ACC-2025-001", 50, 120),
        ("Incident Number: ACC-2025-001", 50, 150),
        ("التاريخ: 2025-01-21", 50, 190),
        ("Date: 2025-01-21", 50, 220),
        ("اسم المؤمن له: محمد أحمد السعيد", 50, 260),
        ("Insured Name: Mohammed Ahmed Al-Saeed", 50, 290),
        ("رقم الهوية: 1234567890", 50, 330),
        ("National ID: 1234567890", 50, 360),
        ("رقم الوثيقة: POL-2025-12345", 50, 400),
        ("Policy Number: POL-2025-12345", 50, 430),
        ("مبلغ الضرر: 25000 ريال سعودي", 50, 470),
        ("Damage Amount: 25000 SAR", 50, 500),
        ("المدينة: الرياض", 50, 540),
        ("City: Riyadh", 50, 570)
    ]
    
    for text, x, y in texts:
        try:
            draw.text((x, y), text, fill='black', font=font_medium)
        except:
            # Fallback for Arabic text issues
            draw.text((x, y), text.encode('utf-8').decode('utf-8'), fill='black', font=font_medium)
    
    # Save test image
    test_image_path = "test_ocr_image.png"
    img.save(test_image_path)
    print(f"Test image created: {test_image_path}")
    return test_image_path

def test_ocr_engines():
    """Test available OCR engines"""
    print("Testing OCR engines...")
    print("=" * 50)
    
    # Test simple OCR
    try:
        from app.simple_ocr import simple_ocr
        print("✅ Simple OCR: Available")
        print(f"   Status: {simple_ocr.is_available()}")
    except Exception as e:
        print(f"❌ Simple OCR: Failed - {e}")
    
    # Test Tesseract OCR
    try:
        from app.tesseract_ocr import tesseract_ocr
        print(f"✅ Tesseract OCR: {'Available' if tesseract_ocr.is_available() else 'Not Available'}")
        if tesseract_ocr.is_available():
            print(f"   Path: {tesseract_ocr.tesseract_path}")
            try:
                langs = tesseract_ocr.get_available_languages()
                print(f"   Languages: {langs[:5]}...")  # Show first 5 languages
            except:
                print("   Languages: Could not retrieve")
    except Exception as e:
        print(f"❌ Tesseract OCR: Failed - {e}")
    
    # Test Enhanced OCR
    try:
        from app.ocr_utils import enhanced_ocr
        status = enhanced_ocr.get_status()
        print("✅ Enhanced OCR: Available")
        print(f"   Engines: {status['engines']}")
        print(f"   Google Vision: {status['google_vision']}")
        print(f"   Tesseract: {status['tesseract']}")
    except Exception as e:
        print(f"❌ Enhanced OCR: Failed - {e}")

def test_ocr_processing():
    """Test OCR processing with test image"""
    print("\nTesting OCR processing...")
    print("=" * 50)
    
    # Create test image
    test_image = create_test_image()
    
    if not os.path.exists(test_image):
        print("❌ Test image not created")
        return
    
    # Test with different OCR engines
    engines_to_test = [
        ("Simple OCR", "app.simple_ocr", "process_document"),
        ("Tesseract OCR", "app.tesseract_ocr", "process_document"),
        ("Enhanced OCR", "app.ocr_utils", "extract_text_from_image")
    ]
    
    for engine_name, module_name, function_name in engines_to_test:
        try:
            print(f"\n🔍 Testing {engine_name}...")
            
            # Import module and function
            module = __import__(module_name, fromlist=[function_name])
            ocr_function = getattr(module, function_name)
            
            # Process image
            result = ocr_function(test_image)
            
            if result.get('success', False):
                print(f"✅ {engine_name}: Success")
                print(f"   Method: {result.get('method', 'unknown')}")
                print(f"   Confidence: {result.get('confidence', result.get('ocr_confidence', 0))}")
                
                # Show extracted text (first 200 chars)
                text = result.get('text', result.get('ocr_text', ''))
                if text:
                    print(f"   Text preview: {text[:200]}...")
                
                # Show extracted data if available
                if 'extracted_data' in result:
                    data = result['extracted_data']
                    print(f"   Extracted fields: {sum(1 for v in data.values() if v and v != '')}")
                    
            else:
                print(f"❌ {engine_name}: Failed")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ {engine_name}: Exception - {e}")
    
    # Clean up
    try:
        os.remove(test_image)
        print(f"\n🧹 Cleaned up test image: {test_image}")
    except:
        pass

def main():
    """Main test function"""
    print("OCR Setup Test")
    print("=" * 50)
    
    # Test OCR engines availability
    test_ocr_engines()
    
    # Test OCR processing
    test_ocr_processing()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    
    # Instructions
    print("\n📋 Instructions:")
    print("1. For Tesseract OCR:")
    print("   - Download from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   - Install with Arabic language pack")
    print("   - Add to system PATH")
    
    print("\n2. For Google Vision API:")
    print("   - Create Google Cloud project")
    print("   - Enable Vision API")
    print("   - Create service account or API key")
    print("   - Update .env file with credentials")

if __name__ == "__main__":
    main()