#!/usr/bin/env python3
"""
Create employee user for testing
"""
from app import create_app, db
from app.models import User

def create_employee():
    """Create employee user"""
    app = create_app()
    
    with app.app_context():
        # Check if employee already exists
        employee = User.query.filter_by(email='employee@example.com').first()
        
        if employee:
            print("✅ الموظف موجود بالفعل")
            print(f"   - الاسم: {employee.full_name}")
            print(f"   - البريد: {employee.email}")
            print(f"   - الدور: {employee.role}")
            print(f"   - نشط: {employee.active}")
        else:
            # Create new employee
            employee = User(
                full_name='أحمد محمد الموظف',
                email='employee@example.com',
                role='claims_agent',
                active=True
            )
            employee.set_password('123456')
            
            db.session.add(employee)
            db.session.commit()
            
            print("✅ تم إنشاء حساب الموظف بنجاح!")
            print(f"   - الاسم: {employee.full_name}")
            print(f"   - البريد: {employee.email}")
            print(f"   - كلمة المرور: 123456")
            print(f"   - الدور: {employee.role}")
        
        print("\n🔗 روابط الموظف:")
        print("   - الرابط العام: http://127.0.0.1:5000")
        print("   - لوحة الموظف: http://127.0.0.1:5000/employee")
        print("   - تسجيل الدخول: http://127.0.0.1:5000/auth/login")
        
        print("\n📋 بيانات تسجيل الدخول:")
        print("   - البريد الإلكتروني: employee@example.com")
        print("   - كلمة المرور: 123456")

if __name__ == "__main__":
    create_employee()
