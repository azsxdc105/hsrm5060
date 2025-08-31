#!/usr/bin/env python3
"""
Script to create sample claims for testing
"""
from app import create_app, db
from app.models import Claim, InsuranceCompany, User
from datetime import datetime, timedelta
import uuid

def create_sample_claims():
    """Create sample claims for testing"""
    app = create_app()
    
    with app.app_context():
        # Get admin user and first insurance company
        admin_user = User.query.filter_by(email='admin@claims.com').first()
        insurance_company = InsuranceCompany.query.first()
        
        if not admin_user or not insurance_company:
            print("❌ Admin user or insurance company not found!")
            return
        
        # Sample claims data
        sample_claims = [
            {
                'client_name': 'أحمد محمد السعيد',
                'client_national_id': '1234567890',
                'policy_number': 'POL-2024-001',
                'incident_number': 'INC-2024-001',
                'claim_amount': 15000.00,
                'incident_date': (datetime.now() - timedelta(days=5)).date(),
                'claim_details': 'حادث مروري بسيط في شارع الملك فهد',
                'coverage_type': 'comprehensive',
                'city': 'الرياض',
                'status': 'draft'
            },
            {
                'client_name': 'فاطمة علي الزهراني',
                'client_national_id': '2345678901',
                'policy_number': 'POL-2024-002',
                'incident_number': 'INC-2024-002',
                'claim_amount': 8500.00,
                'incident_date': (datetime.now() - timedelta(days=3)).date(),
                'claim_details': 'كسر في الزجاج الأمامي للسيارة',
                'coverage_type': 'comprehensive',
                'city': 'جدة',
                'status': 'draft'
            },
            {
                'client_name': 'خالد عبدالله النمر',
                'client_national_id': '3456789012',
                'policy_number': 'POL-2024-003',
                'incident_number': 'INC-2024-003',
                'claim_amount': 25000.00,
                'incident_date': (datetime.now() - timedelta(days=7)).date(),
                'claim_details': 'حادث تصادم في تقاطع طريق الملك عبدالعزيز',
                'coverage_type': 'comprehensive',
                'city': 'الدمام',
                'status': 'sent'
            }
        ]
        
        print("📝 Creating sample claims...")
        
        for claim_data in sample_claims:
            # Create claim
            claim = Claim(
                id=str(uuid.uuid4()),
                client_name=claim_data['client_name'],
                client_national_id=claim_data['client_national_id'],
                policy_number=claim_data['policy_number'],
                incident_number=claim_data['incident_number'],
                claim_amount=claim_data['claim_amount'],
                incident_date=claim_data['incident_date'],
                claim_details=claim_data['claim_details'],
                coverage_type=claim_data['coverage_type'],
                city=claim_data['city'],
                status=claim_data['status'],
                company_id=insurance_company.id,
                created_by_user_id=admin_user.id,
                created_at=datetime.now()
            )
            
            db.session.add(claim)
            print(f"   ✓ Created claim for: {claim_data['client_name']}")
        
        # Commit all changes
        db.session.commit()
        
        print("=" * 50)
        print("✅ Sample claims created successfully!")
        print(f"   📊 Total claims in system: {Claim.query.count()}")
        print("=" * 50)
        print("🌐 You can now view them at: http://127.0.0.1:5000")

if __name__ == '__main__':
    create_sample_claims()
