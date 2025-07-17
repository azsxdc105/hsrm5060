#!/usr/bin/env python3
"""
Seed script for insurance companies and initial admin user
"""
from app import create_app, db
from app.models import User, InsuranceCompany, SystemSettings
from config import Config

def seed_insurance_companies():
    """Seed insurance companies data"""
    companies_data = [
        {
            'name_ar': 'التعاونية للتأمين',
            'name_en': 'Tawuniya',
            'claims_email_primary': 'claims@tawuniya.com.sa'
        },
        {
            'name_ar': 'ميدغلف',
            'name_en': 'Medgulf',
            'claims_email_primary': 'claims@medgulf.com.sa'
        },
        {
            'name_ar': 'بوبا العربية',
            'name_en': 'Bupa Arabia',
            'claims_email_primary': 'claims@bupa.com.sa'
        },
        {
            'name_ar': 'ولاء للتأمين',
            'name_en': 'Walaa',
            'claims_email_primary': 'claims@walaa.com'
        },
        {
            'name_ar': 'أسيج',
            'name_en': 'ACIG',
            'claims_email_primary': 'claims@acig.com.sa'
        },
        {
            'name_ar': 'سلامة',
            'name_en': 'Salama',
            'claims_email_primary': 'claims@salama.com'
        },
        {
            'name_ar': 'الخليجية العامة',
            'name_en': 'GIG Saudi',
            'claims_email_primary': 'claims@gig.com.sa'
        },
        {
            'name_ar': 'ملاذ للتأمين',
            'name_en': 'Malath',
            'claims_email_primary': 'claims@malath.com.sa'
        },
        {
            'name_ar': 'الدرع العربي',
            'name_en': 'Arabian Shield',
            'claims_email_primary': 'claims@arabianshield.com'
        },
        {
            'name_ar': 'سايكو',
            'name_en': 'SAICO',
            'claims_email_primary': 'claims@saico.com.sa'
        },
        {
            'name_ar': 'الاتحاد للتأمين',
            'name_en': 'Al-Etihad',
            'claims_email_primary': 'claims@alethiad.com.sa'
        },
        {
            'name_ar': 'أمانة',
            'name_en': 'Amana',
            'claims_email_primary': 'claims@amana.com.sa'
        },
        {
            'name_ar': 'المتحدة',
            'name_en': 'TUIC',
            'claims_email_primary': 'claims@tuic.com.sa'
        },
        {
            'name_ar': 'العربية للتأمين',
            'name_en': 'AIC',
            'claims_email_primary': 'claims@aic.com.sa'
        },
        {
            'name_ar': 'الأهلي طوكيو مارين',
            'name_en': 'Al Ahli Takaful',
            'claims_email_primary': 'claims@alahli-takaful.com.sa'
        },
        {
            'name_ar': 'الراجحي للتأمين التعاوني',
            'name_en': 'Al Rajhi Takaful',
            'claims_email_primary': 'claims@alrajhi-takaful.com.sa'
        },
        {
            'name_ar': 'اتحاد الخليج',
            'name_en': 'Gulf Union',
            'claims_email_primary': 'claims@gulfunion.com.sa'
        },
        {
            'name_ar': 'الصقر للتأمين',
            'name_en': 'Al-Sagr Insurance',
            'claims_email_primary': 'claims@alsagr.com.sa'
        }
    ]
    
    print("🏢 Adding insurance companies...")
    for company_data in companies_data:
        existing = InsuranceCompany.query.filter_by(name_ar=company_data['name_ar']).first()
        if not existing:
            company = InsuranceCompany(**company_data)
            db.session.add(company)
            print(f"   ✓ Added: {company_data['name_ar']}")
        else:
            print(f"   ⚠ Skipped (exists): {company_data['name_ar']}")
    
    print(f"📊 Total insurance companies: {InsuranceCompany.query.count()}")

def seed_admin_user():
    """Create initial admin user"""
    admin_email = Config.ADMIN_EMAIL
    admin_password = Config.ADMIN_PASSWORD
    
    print(f"👤 Creating admin user...")
    existing_admin = User.query.filter_by(email=admin_email).first()
    
    if not existing_admin:
        admin_user = User(
            full_name='مدير النظام',
            email=admin_email,
            role='admin',
            active=True
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        print(f"   ✓ Created admin user: {admin_email}")
    else:
        print(f"   ⚠ Admin user already exists: {admin_email}")
    
    print(f"👥 Total users: {User.query.count()}")

def seed_system_settings():
    """Create initial system settings"""
    print("⚙️ Creating system settings...")
    
    settings_data = [
        {
            'key': 'MAIL_SERVER',
            'value': 'smtp.gmail.com',
            'description': 'SMTP server for sending emails'
        },
        {
            'key': 'MAIL_PORT',
            'value': '587',
            'description': 'SMTP port number'
        },
        {
            'key': 'MAIL_USE_TLS',
            'value': 'True',
            'description': 'Use TLS for email encryption'
        },
        {
            'key': 'MAIL_USE_SSL',
            'value': 'False',
            'description': 'Use SSL for email encryption'
        },
        {
            'key': 'MAX_UPLOAD_MB',
            'value': '25',
            'description': 'Maximum file upload size in MB'
        },
        {
            'key': 'AI_ENABLED',
            'value': 'False',
            'description': 'Enable AI features'
        },
        {
            'key': 'OCR_ENABLED',
            'value': 'False',
            'description': 'Enable OCR text extraction'
        }
    ]
    
    for setting_data in settings_data:
        existing = SystemSettings.query.filter_by(key=setting_data['key']).first()
        if not existing:
            setting = SystemSettings(**setting_data)
            db.session.add(setting)
            print(f"   ✓ Added setting: {setting_data['key']}")
        else:
            print(f"   ⚠ Setting exists: {setting_data['key']}")

def main():
    """Main seeding function"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Starting database seeding...")
        print("=" * 50)
        
        # Create all tables
        print("📋 Creating database tables...")
        db.create_all()
        print("   ✓ Database tables created")
        
        # Seed data
        try:
            seed_insurance_companies()
            seed_admin_user()
            seed_system_settings()
            
            # Commit all changes
            db.session.commit()
            print("=" * 50)
            print("✅ Database seeding completed successfully!")
            print(f"   📊 Insurance companies: {InsuranceCompany.query.count()}")
            print(f"   👥 Users: {User.query.count()}")
            print(f"   ⚙️ System settings: {SystemSettings.query.count()}")
            print("=" * 50)
            print("🚀 You can now start the application!")
            print(f"   📧 Admin email: {Config.ADMIN_EMAIL}")
            print(f"   🔑 Admin password: {Config.ADMIN_PASSWORD}")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    main()