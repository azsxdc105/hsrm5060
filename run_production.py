#!/usr/bin/env python3
"""
Production runner for the Insurance Claims Management System
"""
import os
import sys
import socket
from app import create_app, db
from production_config import ProductionConfig

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def check_port_available(host, port):
    """Check if a port is available"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex((host, port))
        s.close()
        return result != 0
    except Exception:
        return False

def setup_production_environment():
    """Setup production environment"""
    print("🚀 Setting up production environment...")
    
    # Set environment variables if not already set
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'production'
    
    if not os.environ.get('SECRET_KEY'):
        # Generate a random secret key for production
        import secrets
        os.environ['SECRET_KEY'] = secrets.token_hex(32)
        print("✅ Generated new secret key")
    
    # Create necessary directories
    directories = ['logs', 'uploads', 'backups']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
    
    print("✅ Production environment setup complete")

def initialize_database(app):
    """Initialize database with sample data if needed"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Check if we need to create admin user
            from app.models import User
            admin_user = User.query.filter_by(email='admin@insurance.com').first()
            
            if not admin_user:
                print("🔧 Creating default admin user...")
                from werkzeug.security import generate_password_hash
                
                admin = User(
                    email='admin@insurance.com',
                    full_name='مدير النظام',
                    password_hash=generate_password_hash('admin123'),
                    role='admin',
                    active=True
                )
                
                db.session.add(admin)
                db.session.commit()
                print("✅ Default admin user created")
                print("   📧 Email: admin@insurance.com")
                print("   🔑 Password: admin123")
                print("   ⚠️  Please change the password after first login!")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            return False
    
    return True

def display_access_info(host, port):
    """Display access information"""
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print("🎉 Insurance Claims Management System is running!")
    print("="*60)
    print(f"🌐 Local access:     http://localhost:{port}")
    print(f"🌐 Network access:   http://{local_ip}:{port}")
    print(f"🌐 All interfaces:   http://{host}:{port}")
    print("\n📱 Mobile/Tablet access:")
    print(f"   Use: http://{local_ip}:{port}")
    print("\n👥 For other users on the same network:")
    print(f"   Share this URL: http://{local_ip}:{port}")
    print("\n🔐 Default admin login:")
    print("   📧 Email: admin@insurance.com")
    print("   🔑 Password: admin123")
    print("\n⚠️  Security Notes:")
    print("   • Change default password immediately")
    print("   • This is running in production mode")
    print("   • Make sure your firewall allows the port")
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print("="*60)

def main():
    """Main function to run the production server"""
    print("🚀 Starting Insurance Claims Management System...")
    
    # Setup production environment
    setup_production_environment()
    
    # Create Flask app with production config
    app = create_app()
    app.config.from_object(ProductionConfig)
    
    # Initialize production settings
    ProductionConfig.init_app(app)
    
    # Initialize database
    if not initialize_database(app):
        print("❌ Failed to initialize database. Exiting...")
        sys.exit(1)
    
    # Get configuration
    host = ProductionConfig.HOST
    port = ProductionConfig.PORT
    
    # Check if port is available
    if not check_port_available(host, port):
        print(f"❌ Port {port} is already in use!")
        print("   Try using a different port:")
        print(f"   python run_production.py --port 8080")
        sys.exit(1)
    
    # Display access information
    display_access_info(host, port)
    
    try:
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=False,  # Disable debug in production
            threaded=True,  # Enable threading for better performance
            use_reloader=False  # Disable auto-reloader in production
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Handle command line arguments
    if len(sys.argv) > 1:
        if '--port' in sys.argv:
            try:
                port_index = sys.argv.index('--port') + 1
                ProductionConfig.PORT = int(sys.argv[port_index])
            except (ValueError, IndexError):
                print("❌ Invalid port number")
                sys.exit(1)
        
        if '--host' in sys.argv:
            try:
                host_index = sys.argv.index('--host') + 1
                ProductionConfig.HOST = sys.argv[host_index]
            except IndexError:
                print("❌ Invalid host")
                sys.exit(1)
    
    main()
