from flask import current_app, render_template_string
from flask_mail import Message
from app import mail, db
from app.models import EmailLog
import json
from datetime import datetime

def get_default_email_template(language='ar'):
    """Get default email template for claims"""
    if language == 'ar':
        return {
            'subject': 'مطالبة مالية بخصوص الحادث رقم {{incident_number}}',
            'body': """السادة شركة {{company_name}} المحترمين،

أرفق لكم بيانات المطالبة الخاصة بالحادث رقم {{incident_number}}:

اسم العميل: {{client_name}}
رقم الهوية: {{client_national_id}}
رقم الوثيقة: {{policy_number}}
مبلغ المطالبة: {{claim_amount}} ريال سعودي
تاريخ الحادث: {{incident_date}}
نوع التغطية: {{coverage_type}}

تفاصيل المطالبة:
{{claim_details}}

مرفق مع هذا الإيميل المستندات المطلوبة.

شاكرين تعاونكم.

مع أطيب التحيات،
فريق المطالبات"""
        }
    else:
        return {
            'subject': 'Insurance Claim - Incident No. {{incident_number}}',
            'body': """Dear {{company_name}} Claims Team,

Please find attached the claim documents related to Incident No. {{incident_number}}.

Client Name: {{client_name}}
National ID: {{client_national_id}}
Policy No.: {{policy_number}}
Claim Amount: {{claim_amount}} SAR
Incident Date: {{incident_date}}
Coverage Type: {{coverage_type}}

Claim Details:
{{claim_details}}

All supporting documents are attached.

Thank you for your cooperation.

Best regards,
Claims Team"""
        }

def render_email_template(template_text, claim_data):
    """Render email template with claim data"""
    return render_template_string(template_text, **claim_data)

def prepare_claim_data(claim):
    """Prepare claim data for email template"""
    coverage_types = {
        'third_party': 'ضد الغير',
        'comprehensive': 'شامل',
        'other': 'أخرى'
    }
    
    return {
        'company_name': claim.insurance_company.name_ar,
        'client_name': claim.client_name,
        'client_national_id': claim.client_national_id,
        'policy_number': claim.policy_number or 'غير محدد',
        'incident_number': claim.incident_number or 'غير محدد',
        'claim_amount': str(claim.claim_amount),
        'incident_date': claim.incident_date.strftime('%Y-%m-%d'),
        'coverage_type': coverage_types.get(claim.coverage_type, claim.coverage_type),
        'claim_details': claim.claim_details
    }

def send_claim_email(claim, attachments=None):
    """Send claim email to insurance company"""
    try:
        # Get email template
        company = claim.insurance_company
        template = get_default_email_template('ar')
        
        # Use custom template if available
        if company.email_template_ar:
            template['body'] = company.email_template_ar
        
        # Prepare data
        claim_data = prepare_claim_data(claim)
        
        # Render template
        subject = render_email_template(template['subject'], claim_data)
        body = render_email_template(template['body'], claim_data)
        
        # Prepare recipients
        recipients = [company.claims_email_primary]
        cc_emails = []
        
        if company.claims_email_cc:
            try:
                cc_emails = json.loads(company.claims_email_cc)
            except:
                # If not JSON, try splitting by comma
                cc_emails = [email.strip() for email in company.claims_email_cc.split(',') if email.strip()]
        
        # Create message
        msg = Message(
            subject=subject,
            recipients=recipients,
            cc=cc_emails,
            body=body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        # Attach files
        if attachments:
            for attachment in attachments:
                try:
                    with open(attachment.storage_path, 'rb') as f:
                        msg.attach(
                            attachment.original_filename,
                            attachment.mime_type,
                            f.read()
                        )
                except Exception as e:
                    current_app.logger.error(f"Error attaching file {attachment.original_filename}: {e}")
        
        # Send email
        mail.send(msg)
        
        # Log success
        log_email_send(claim, recipients + cc_emails, subject, body, 'success')
        
        # Update claim status
        claim.status = 'sent'
        claim.email_sent_at = datetime.utcnow()
        db.session.commit()
        
        return True, "تم إرسال البريد الإلكتروني بنجاح"
        
    except Exception as e:
        # Log failure
        log_email_send(claim, recipients + cc_emails, subject, body, 'failed', str(e))
        
        # Update claim status
        claim.status = 'failed'
        db.session.commit()
        
        current_app.logger.error(f"Error sending email for claim {claim.id}: {e}")
        return False, f"خطأ في إرسال البريد الإلكتروني: {str(e)}"

def log_email_send(claim, recipients, subject, body, status, error_message=None):
    """Log email send attempt"""
    log = EmailLog(
        claim_id=claim.id,
        to_emails=','.join(recipients),
        subject=subject,
        body_preview=body[:500] + '...' if len(body) > 500 else body,
        send_status=status,
        error_message=error_message
    )
    db.session.add(log)
    db.session.commit()

def test_email_configuration():
    """Test email configuration"""
    try:
        msg = Message(
            subject='Test Email Configuration',
            recipients=[current_app.config.get('MAIL_DEFAULT_SENDER')],
            body='This is a test email to verify email configuration.',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        return True, "تم اختبار البريد الإلكتروني بنجاح"
    except Exception as e:
        return False, f"خطأ في اختبار البريد الإلكتروني: {str(e)}"

def test_email_configuration(config, test_email):
    """
    Test email configuration with custom settings
    """
    try:
        # Temporarily update Flask-Mail configuration
        current_app.config.update({
            'MAIL_SERVER': config['MAIL_SERVER'],
            'MAIL_PORT': config['MAIL_PORT'],
            'MAIL_USE_TLS': config['MAIL_USE_TLS'],
            'MAIL_USE_SSL': config['MAIL_USE_SSL'],
            'MAIL_USERNAME': config['MAIL_USERNAME'],
            'MAIL_PASSWORD': config['MAIL_PASSWORD'],
            'MAIL_DEFAULT_SENDER': config['MAIL_DEFAULT_SENDER']
        })

        # Reinitialize mail with new config
        mail.init_app(current_app)

        # Create test message
        msg = Message(
            subject='اختبار إعدادات البريد الإلكتروني - نظام إدارة المطالبات',
            recipients=[test_email],
            sender=config['MAIL_DEFAULT_SENDER']
        )

        msg.html = f"""
        <html>
        <body dir="rtl" style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">🎉 اختبار البريد الإلكتروني</h2>
                <p>مرحباً،</p>
                <p>هذا بريد اختبار من نظام إدارة مطالبات التأمين.</p>
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
                    <p style="margin: 0; color: #155724;">
                        <strong>✅ تهانينا!</strong> إعدادات البريد الإلكتروني تعمل بشكل صحيح.
                    </p>
                </div>
                <hr style="margin: 20px 0;">
                <p><strong>تفاصيل الاختبار:</strong></p>
                <ul>
                    <li>التاريخ والوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li>الخادم: {config['MAIL_SERVER']}</li>
                    <li>المنفذ: {config['MAIL_PORT']}</li>
                </ul>
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
                    تم إرسال هذا البريد تلقائياً من نظام إدارة مطالبات التأمين
                </p>
            </div>
        </body>
        </html>
        """

        # Send test email
        mail.send(msg)

        # Log successful test
        log_email_send(test_email, 'اختبار إعدادات البريد', 'sent', 'تم إرسال بريد الاختبار بنجاح')

        return True

    except Exception as e:
        # Log failed test
        log_email_send(test_email, 'اختبار إعدادات البريد', 'failed', str(e))
        return False