#!/usr/bin/env python3
"""
Initialize AI Features Database Tables
This script creates the new database tables for AI classification and advanced notifications
"""
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, Claim, InsuranceCompany,
    # AI Classification models
    ClaimClassification, FraudIndicator,
    # Advanced Notifications models
    NotificationTemplate, UserNotificationSettings,
    Notification, NotificationQueue,
    NotificationType, NotificationPriority,
    SimpleNotification
)

def init_database():
    """Initialize database with new AI features tables"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Initializing AI Features Database...")
        
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Create default notification templates
            create_default_notification_templates()
            
            # Create default notification settings for existing users
            create_default_user_notification_settings()
            
            print("🎉 AI Features initialization completed successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            return False
    
    return True

def create_default_notification_templates():
    """Create default notification templates"""
    print("📧 Creating default notification templates...")
    
    templates = [
        {
            'name': 'claim_created_email',
            'event_type': 'claim_created',
            'notification_type': NotificationType.EMAIL,
            'subject_ar': 'تم إنشاء مطالبة جديدة - {claim_id}',
            'subject_en': 'New Claim Created - {claim_id}',
            'content_ar': '''
            <h2>تم إنشاء مطالبة جديدة</h2>
            <p>تم إنشاء مطالبة تأمين جديدة:</p>
            <ul>
                <li><strong>رقم المطالبة:</strong> {claim_id}</li>
                <li><strong>العميل:</strong> {client_name}</li>
                <li><strong>المبلغ:</strong> {claim_amount} {currency}</li>
                <li><strong>شركة التأمين:</strong> {company_name}</li>
                <li><strong>أنشأها:</strong> {created_by}</li>
            </ul>
            <p>يرجى مراجعة المطالبة في النظام.</p>
            ''',
            'content_en': '''
            <h2>New Claim Created</h2>
            <p>A new insurance claim has been created:</p>
            <ul>
                <li><strong>Claim ID:</strong> {claim_id}</li>
                <li><strong>Client:</strong> {client_name}</li>
                <li><strong>Amount:</strong> {claim_amount} {currency}</li>
                <li><strong>Company:</strong> {company_name}</li>
                <li><strong>Created by:</strong> {created_by}</li>
            </ul>
            <p>Please review the claim in the system.</p>
            ''',
            'variables': '["claim_id", "client_name", "claim_amount", "currency", "company_name", "created_by"]'
        },
        {
            'name': 'claim_high_risk_detected',
            'event_type': 'claim_high_risk_detected',
            'notification_type': NotificationType.EMAIL,
            'subject_ar': 'تحذير: مطالبة عالية المخاطر - {claim_id}',
            'subject_en': 'Warning: High Risk Claim - {claim_id}',
            'content_ar': '''
            <h2 style="color: #dc3545;">تحذير: مطالبة عالية المخاطر</h2>
            <p>تم اكتشاف مطالبة عالية المخاطر بواسطة نظام الذكاء الاصطناعي:</p>
            <ul>
                <li><strong>رقم المطالبة:</strong> {claim_id}</li>
                <li><strong>العميل:</strong> {client_name}</li>
                <li><strong>المبلغ:</strong> {claim_amount} {currency}</li>
                <li><strong>مستوى المخاطر:</strong> {risk_level}</li>
                <li><strong>احتمالية الاحتيال:</strong> {fraud_probability}%</li>
            </ul>
            <p><strong>يرجى مراجعة هذه المطالبة فوراً.</strong></p>
            ''',
            'content_en': '''
            <h2 style="color: #dc3545;">Warning: High Risk Claim</h2>
            <p>A high risk claim has been detected by the AI system:</p>
            <ul>
                <li><strong>Claim ID:</strong> {claim_id}</li>
                <li><strong>Client:</strong> {client_name}</li>
                <li><strong>Amount:</strong> {claim_amount} {currency}</li>
                <li><strong>Risk Level:</strong> {risk_level}</li>
                <li><strong>Fraud Probability:</strong> {fraud_probability}%</li>
            </ul>
            <p><strong>Please review this claim immediately.</strong></p>
            ''',
            'variables': '["claim_id", "client_name", "claim_amount", "currency", "risk_level", "fraud_probability"]'
        },
        {
            'name': 'claim_sent_sms',
            'event_type': 'claim_sent',
            'notification_type': NotificationType.SMS,
            'subject_ar': 'تم إرسال المطالبة',
            'content_ar': 'تم إرسال المطالبة {claim_id} بنجاح إلى شركة التأمين {company_name}.',
            'content_en': 'Claim {claim_id} has been successfully sent to insurance company {company_name}.',
            'variables': '["claim_id", "company_name"]'
        }
    ]
    
    for template_data in templates:
        existing = NotificationTemplate.query.filter_by(name=template_data['name']).first()
        if not existing:
            template = NotificationTemplate(**template_data)
            db.session.add(template)
    
    db.session.commit()
    print(f"✅ Created {len(templates)} notification templates")

def create_default_user_notification_settings():
    """Create default notification settings for existing users"""
    print("👥 Creating default notification settings for users...")
    
    users = User.query.all()
    created_count = 0
    
    for user in users:
        existing_settings = UserNotificationSettings.query.filter_by(user_id=user.id).first()
        if not existing_settings:
            settings = UserNotificationSettings(
                user_id=user.id,
                email_enabled=True,
                sms_enabled=False,
                push_enabled=True,
                whatsapp_enabled=False,
                in_app_enabled=True
            )
            db.session.add(settings)
            created_count += 1
    
    db.session.commit()
    print(f"✅ Created notification settings for {created_count} users")

def test_ai_classification():
    """Test AI classification on existing claims"""
    print("🧠 Testing AI classification...")
    
    try:
        from app.ai_classification import classify_claim_ai
        
        # Get a few claims to test
        test_claims = Claim.query.limit(3).all()
        
        for claim in test_claims:
            try:
                result = classify_claim_ai(claim)
                print(f"  📋 Claim {claim.id}: {result.category} (confidence: {result.confidence:.2f})")
            except Exception as e:
                print(f"  ❌ Failed to classify claim {claim.id}: {e}")
        
        print("✅ AI classification test completed")
        
    except Exception as e:
        print(f"❌ AI classification test failed: {e}")

def show_statistics():
    """Show database statistics"""
    print("\n📊 Database Statistics:")
    print(f"  👥 Users: {User.query.count()}")
    print(f"  🏢 Insurance Companies: {InsuranceCompany.query.count()}")
    print(f"  📋 Claims: {Claim.query.count()}")
    print(f"  🧠 AI Classifications: {ClaimClassification.query.count()}")
    print(f"  🔔 Notification Templates: {NotificationTemplate.query.count()}")
    print(f"  ⚙️ User Notification Settings: {UserNotificationSettings.query.count()}")
    print(f"  📬 Advanced Notifications: {Notification.query.count()}")
    print(f"  📧 Simple Notifications: {SimpleNotification.query.count()}")

if __name__ == '__main__':
    print("🚀 Starting AI Features Initialization...")
    print("=" * 50)
    
    app = create_app()
    success = init_database()

    if success:
        with app.app_context():
            print("\n🧪 Running tests...")
            test_ai_classification()

            print("\n📊 Final Statistics:")
            show_statistics()
        
        print("\n" + "=" * 50)
        print("🎉 AI Features initialization completed successfully!")
        print("\nNext steps:")
        print("1. Restart your Flask application")
        print("2. Visit /ai-classification to access AI features")
        print("3. Visit /advanced-notifications for notification management")
        print("4. Create new claims to see automatic AI classification")
    else:
        print("\n❌ Initialization failed. Please check the errors above.")
        sys.exit(1)
