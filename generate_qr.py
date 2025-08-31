#!/usr/bin/env python3
"""
Generate QR Code for easy access to the Insurance Claims System
"""
import socket
import sys
import os

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def generate_qr_code(url, filename="access_qr.png"):
    """Generate QR code for the URL"""
    try:
        import qrcode
        from PIL import Image, ImageDraw, ImageFont
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Create a larger image with text
        img_width = qr_img.width + 100
        img_height = qr_img.height + 150
        
        final_img = Image.new('RGB', (img_width, img_height), 'white')
        
        # Paste QR code
        qr_x = (img_width - qr_img.width) // 2
        qr_y = 50
        final_img.paste(qr_img, (qr_x, qr_y))
        
        # Add text
        draw = ImageDraw.Draw(final_img)
        
        try:
            # Try to use a nice font
            font_title = ImageFont.truetype("arial.ttf", 16)
            font_text = ImageFont.truetype("arial.ttf", 12)
        except:
            # Fallback to default font
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
        
        # Title
        title = "Insurance Claims System"
        title_bbox = draw.textbbox((0, 0), title, font=font_title)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (img_width - title_width) // 2
        draw.text((title_x, 10), title, fill="black", font=font_title)
        
        # URL
        url_bbox = draw.textbbox((0, 0), url, font=font_text)
        url_width = url_bbox[2] - url_bbox[0]
        url_x = (img_width - url_width) // 2
        draw.text((url_x, qr_y + qr_img.height + 20), url, fill="black", font=font_text)
        
        # Instructions
        instructions = [
            "1. Scan with your phone camera",
            "2. Or type the URL above",
            "3. Login: admin@insurance.com",
            "4. Password: admin123"
        ]
        
        y_offset = qr_y + qr_img.height + 50
        for instruction in instructions:
            inst_bbox = draw.textbbox((0, 0), instruction, font=font_text)
            inst_width = inst_bbox[2] - inst_bbox[0]
            inst_x = (img_width - inst_width) // 2
            draw.text((inst_x, y_offset), instruction, fill="black", font=font_text)
            y_offset += 20
        
        # Save the image
        final_img.save(filename)
        return True
        
    except ImportError:
        print("❌ QR code libraries not installed")
        print("   Install with: pip install qrcode[pil]")
        return False
    except Exception as e:
        print(f"❌ Error generating QR code: {e}")
        return False

def create_html_page(url, qr_filename="access_qr.png"):
    """Create an HTML page with QR code and instructions"""
    html_content = f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام إدارة مطالبات التأمين - دليل الوصول</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
            width: 100%;
        }}
        h1 {{
            color: #333;
            margin-bottom: 30px;
            font-size: 24px;
        }}
        .qr-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }}
        .qr-code {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
        }}
        .url {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 10px;
            font-family: monospace;
            font-size: 16px;
            margin: 20px 0;
            word-break: break-all;
        }}
        .instructions {{
            text-align: right;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .instructions h3 {{
            color: #495057;
            margin-bottom: 15px;
        }}
        .instructions ul {{
            list-style-type: none;
            padding: 0;
        }}
        .instructions li {{
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        .instructions li:last-child {{
            border-bottom: none;
        }}
        .login-info {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            margin: 10px;
            transition: background 0.3s;
        }}
        .btn:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 نظام إدارة مطالبات التأمين</h1>
        
        <div class="qr-container">
            <img src="{qr_filename}" alt="QR Code" class="qr-code">
        </div>
        
        <div class="url">
            <strong>رابط الوصول:</strong><br>
            {url}
        </div>
        
        <div class="instructions">
            <h3>📱 طريقة الوصول:</h3>
            <ul>
                <li>🔍 امسح الكود بكاميرا الهاتف</li>
                <li>💻 أو اكتب الرابط في المتصفح</li>
                <li>🌐 تأكد من الاتصال بنفس الشبكة</li>
                <li>🔐 استخدم بيانات الدخول أدناه</li>
            </ul>
        </div>
        
        <div class="login-info">
            <h3>🔐 بيانات الدخول:</h3>
            <p><strong>البريد الإلكتروني:</strong> admin@insurance.com</p>
            <p><strong>كلمة المرور:</strong> admin123</p>
        </div>
        
        <div class="warning">
            <h3>⚠️ تنبيه أمني:</h3>
            <p>يرجى تغيير كلمة المرور فور تسجيل الدخول الأول</p>
        </div>
        
        <a href="{url}" class="btn">🚀 الدخول للنظام</a>
    </div>
</body>
</html>
"""
    
    with open("access_guide.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return "access_guide.html"

def main():
    """Main function"""
    print("🎯 Generating access information...")
    
    # Get local IP and create URL
    local_ip = get_local_ip()
    url = f"http://{local_ip}:5000"
    
    print(f"🌐 System URL: {url}")
    
    # Generate QR code
    qr_filename = "access_qr.png"
    if generate_qr_code(url, qr_filename):
        print(f"✅ QR code generated: {qr_filename}")
    else:
        print("⚠️  QR code generation failed, but continuing...")
    
    # Create HTML guide
    html_file = create_html_page(url, qr_filename)
    print(f"✅ Access guide created: {html_file}")
    
    print("\n" + "="*60)
    print("🎉 Access information generated successfully!")
    print("="*60)
    print(f"📱 QR Code: {qr_filename}")
    print(f"🌐 HTML Guide: {html_file}")
    print(f"🔗 Direct URL: {url}")
    print("\n📋 Share with others:")
    print(f"   1. Send them the HTML file: {html_file}")
    print(f"   2. Or share the URL: {url}")
    print(f"   3. Or let them scan the QR code: {qr_filename}")
    print("="*60)

if __name__ == "__main__":
    main()
