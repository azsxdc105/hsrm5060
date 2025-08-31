#!/usr/bin/env python3
"""
Simple script to get and display local IP address
"""
import socket
import platform
import subprocess
import sys

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Method 1: Connect to external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        pass
    
    try:
        # Method 2: Get hostname IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip.startswith("127."):
            raise Exception("Loopback address")
        return local_ip
    except Exception:
        pass
    
    return "127.0.0.1"

def get_all_network_interfaces():
    """Get all network interfaces and their IPs"""
    interfaces = []
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows command
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp1256')
            lines = result.stdout.split('\n')
            
            current_adapter = ""
            for line in lines:
                line = line.strip()
                if "adapter" in line.lower() or "محول" in line:
                    current_adapter = line
                elif "IPv4" in line or "عنوان IPv4" in line:
                    ip = line.split(':')[-1].strip()
                    if ip and not ip.startswith("127."):
                        interfaces.append((current_adapter, ip))
        
        elif system in ["linux", "darwin"]:  # Linux or macOS
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            current_interface = ""
            for line in lines:
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    current_interface = line.split(':')[0]
                elif "inet " in line and "127.0.0.1" not in line:
                    ip = line.split()[1]
                    if "addr:" in ip:
                        ip = ip.split(':')[1]
                    interfaces.append((current_interface, ip))
    
    except Exception as e:
        print(f"Error getting network interfaces: {e}")
    
    return interfaces

def display_network_info():
    """Display network information"""
    print("🌐 معلومات الشبكة - Network Information")
    print("=" * 50)
    
    # Get primary local IP
    local_ip = get_local_ip()
    print(f"🎯 العنوان الأساسي - Primary IP: {local_ip}")
    
    # Get all interfaces
    interfaces = get_all_network_interfaces()
    
    if interfaces:
        print("\n📡 جميع واجهات الشبكة - All Network Interfaces:")
        print("-" * 50)
        for adapter, ip in interfaces:
            print(f"   {adapter}: {ip}")
    
    print("\n🌐 روابط الوصول - Access URLs:")
    print("-" * 50)
    print(f"   المحلي - Local:     http://localhost:5000")
    print(f"   الشبكة - Network:   http://{local_ip}:5000")
    
    if interfaces:
        print("\n📱 للأجهزة الأخرى - For Other Devices:")
        print("-" * 50)
        for adapter, ip in interfaces:
            if not ip.startswith("127.") and not ip.startswith("169.254"):
                print(f"   http://{ip}:5000")
    
    print("\n📋 معلومات النظام - System Information:")
    print("-" * 50)
    print(f"   النظام - OS: {platform.system()} {platform.release()}")
    print(f"   المعالج - Processor: {platform.processor()}")
    print(f"   اسم الجهاز - Hostname: {socket.gethostname()}")
    
    print("\n🔐 بيانات الدخول الافتراضية - Default Login:")
    print("-" * 50)
    print("   📧 البريد الإلكتروني - Email: admin@insurance.com")
    print("   🔑 كلمة المرور - Password: admin123")
    
    print("\n⚠️  ملاحظات مهمة - Important Notes:")
    print("-" * 50)
    print("   • تأكد من أن جميع الأجهزة متصلة بنفس الشبكة")
    print("   • Make sure all devices are on the same network")
    print("   • قم بتغيير كلمة المرور الافتراضية فوراً")
    print("   • Change the default password immediately")
    print("   • تأكد من فتح المنفذ 5000 في جدار الحماية")
    print("   • Make sure port 5000 is open in firewall")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        # Simple output for scripts
        print(get_local_ip())
    else:
        # Detailed output for users
        display_network_info()

if __name__ == "__main__":
    main()
