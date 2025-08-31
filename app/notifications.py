#!/usr/bin/env python3
"""
Notifications system for real-time alerts via email and SMS
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from flask import current_app, render_template_string
from flask_mail import Message
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from app import db, mail
from app.models import User, Claim, EmailLog
from config import Config
import json

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via email and SMS"""
    
    def __init__(self):
        self.twilio_client = None
        self.setup_twilio()
    
    def setup_twilio(self):
        """Setup Twilio client for SMS"""
        if Config.SMS_ENABLED and Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
                logger.info("Twilio SMS client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.twilio_client = None
        else:
            logger.info("SMS notifications disabled or not configured")
    
    def send_notification(self, notification_type: str, recipients: List[Dict], context: Dict):
        """
        Send notification to multiple recipients
        
        Args:
            notification_type: Type of notification (claim_created, claim_status_changed, etc.)
            recipients: List of recipient dictionaries with 'user', 'email', 'phone', 'language'
            context: Context data for template rendering
        """
        if not Config.NOTIFICATIONS_ENABLED:
            logger.info("Notifications are disabled")
            return
        
        template = Config.NOTIFICATION_TEMPLATES.get(notification_type)
        if not template:
            logger.error(f"Unknown notification type: {notification_type}")
            return
        
        for recipient in recipients:
            try:
                # Send email notification
                if recipient.get('email'):
                    self._send_email_notification(
                        notification_type, 
                        recipient, 
                        template, 
                        context
                    )
                
                # Send SMS notification
                if recipient.get('phone') and Config.SMS_ENABLED:
                    self._send_sms_notification(
                        notification_type,
                        recipient,
                        template,
                        context
                    )
                    
            except Exception as e:
                logger.error(f"Failed to send notification to {recipient.get('email', 'unknown')}: {e}")
    
    def _send_email_notification(self, notification_type: str, recipient: Dict, template: Dict, context: Dict):
        """Send email notification"""
        try:
            language = recipient.get('language', 'ar')
            subject_key = f'email_subject_{language}'
            subject = template.get(subject_key, template.get('email_subject_ar', 'إشعار'))
            
            # Render subject with context
            subject = self._render_template(subject, context)
            
            # Create email body
            body = self._create_email_body(notification_type, context, language)
            
            msg = Message(
                subject=subject,
                recipients=[recipient['email']],
                html=body,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            mail.send(msg)
            
            # Log email
            self._log_notification_email(
                recipient.get('user'),
                recipient['email'],
                subject,
                body,
                notification_type,
                context
            )
            
            logger.info(f"Email notification sent to {recipient['email']}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def _send_sms_notification(self, notification_type: str, recipient: Dict, template: Dict, context: Dict):
        """Send SMS notification"""
        if not self.twilio_client:
            logger.warning("SMS client not available")
            return
        
        try:
            language = recipient.get('language', 'ar')
            sms_key = f'sms_{language}'
            message = template.get(sms_key, template.get('sms_ar', 'إشعار جديد'))
            
            # Render message with context
            message = self._render_template(message, context)
            
            # Send SMS
            sms = self.twilio_client.messages.create(
                body=message,
                from_=Config.TWILIO_PHONE_NUMBER,
                to=recipient['phone']
            )
            
            logger.info(f"SMS notification sent to {recipient['phone']}, SID: {sms.sid}")
            
        except TwilioException as e:
            logger.error(f"Twilio SMS error: {e}")
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
    
    def _render_template(self, template: str, context: Dict) -> str:
        """Render template string with context"""
        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return template
    
    def _create_email_body(self, notification_type: str, context: Dict, language: str = 'ar') -> str:
        """Create HTML email body"""
        if notification_type == 'claim_created':
            return self._create_claim_created_email(context, language)
        elif notification_type == 'claim_status_changed':
            return self._create_claim_status_changed_email(context, language)
        elif notification_type == 'claim_sent':
            return self._create_claim_sent_email(context, language)
        else:
            return self._create_generic_email(context, language)
    
    def _create_claim_created_email(self, context: Dict, language: str) -> str:
        """Create email for new claim notification"""
        if language == 'en':
            template = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #007bff;">New Claim Created</h2>
                <p>A new insurance claim has been created:</p>
                <ul>
                    <li><strong>Claim ID:</strong> {claim_id}</li>
                    <li><strong>Client:</strong> {client_name}</li>
                    <li><strong>Amount:</strong> {claim_amount} SAR</li>
                    <li><strong>Company:</strong> {company_name}</li>
                    <li><strong>Created by:</strong> {created_by}</li>
                </ul>
                <p>Please review the claim in the system.</p>
            </div>
            """
        else:
            template = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; direction: rtl;">
                <h2 style="color: #007bff;">تم إنشاء مطالبة جديدة</h2>
                <p>تم إنشاء مطالبة تأمين جديدة:</p>
                <ul>
                    <li><strong>رقم المطالبة:</strong> {claim_id}</li>
                    <li><strong>العميل:</strong> {client_name}</li>
                    <li><strong>المبلغ:</strong> {claim_amount} ريال</li>
                    <li><strong>الشركة:</strong> {company_name}</li>
                    <li><strong>أنشأها:</strong> {created_by}</li>
                </ul>
                <p>يرجى مراجعة المطالبة في النظام.</p>
            </div>
            """
        
        return self._render_template(template, context)
    
    def _create_claim_status_changed_email(self, context: Dict, language: str) -> str:
        """Create email for claim status change notification"""
        status_translations = {
            'draft': {'ar': 'مسودة', 'en': 'Draft'},
            'ready': {'ar': 'جاهز', 'en': 'Ready'},
            'sent': {'ar': 'مرسل', 'en': 'Sent'},
            'failed': {'ar': 'فشل', 'en': 'Failed'},
            'acknowledged': {'ar': 'مستلم', 'en': 'Acknowledged'},
            'paid': {'ar': 'مدفوع', 'en': 'Paid'}
        }
        
        status_text = status_translations.get(context.get('new_status', ''), {}).get(language, context.get('new_status', ''))
        context['status_text'] = status_text
        
        if language == 'en':
            template = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">Claim Status Updated</h2>
                <p>The status of claim <strong>{claim_id}</strong> has been changed:</p>
                <ul>
                    <li><strong>Client:</strong> {client_name}</li>
                    <li><strong>Previous Status:</strong> {old_status}</li>
                    <li><strong>New Status:</strong> {status_text}</li>
                    <li><strong>Updated by:</strong> {updated_by}</li>
                </ul>
            </div>
            """
        else:
            template = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; direction: rtl;">
                <h2 style="color: #28a745;">تم تحديث حالة المطالبة</h2>
                <p>تم تغيير حالة المطالبة <strong>{claim_id}</strong>:</p>
                <ul>
                    <li><strong>العميل:</strong> {client_name}</li>
                    <li><strong>الحالة السابقة:</strong> {old_status}</li>
                    <li><strong>الحالة الجديدة:</strong> {status_text}</li>
                    <li><strong>حدثها:</strong> {updated_by}</li>
                </ul>
            </div>
            """
        
        return self._render_template(template, context)
    
    def _create_claim_sent_email(self, context: Dict, language: str) -> str:
        """Create email for claim sent notification"""
        if language == 'en':
            template = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #17a2b8;">Claim Sent Successfully</h2>
                <p>Claim <strong>{claim_id}</strong> has been sent to the insurance company:</p>
                <ul>
                    <li><strong>Client:</strong> {client_name}</li>
                    <li><strong>Company:</strong> {company_name}</li>
                    <li><strong>Amount:</strong> {claim_amount} SAR</li>
                    <li><strong>Sent at:</strong> {sent_at}</li>
                </ul>
            </div>
            """
        else:
            template = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; direction: rtl;">
                <h2 style="color: #17a2b8;">تم إرسال المطالبة بنجاح</h2>
                <p>تم إرسال المطالبة <strong>{claim_id}</strong> إلى شركة التأمين:</p>
                <ul>
                    <li><strong>العميل:</strong> {client_name}</li>
                    <li><strong>الشركة:</strong> {company_name}</li>
                    <li><strong>المبلغ:</strong> {claim_amount} ريال</li>
                    <li><strong>وقت الإرسال:</strong> {sent_at}</li>
                </ul>
            </div>
            """
        
        return self._render_template(template, context)
    
    def _create_generic_email(self, context: Dict, language: str) -> str:
        """Create generic email notification"""
        if language == 'en':
            template = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #6c757d;">System Notification</h2>
                <p>You have received a new notification from the Claims Management System.</p>
                <p>Please check the system for more details.</p>
            </div>
            """
        else:
            template = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; direction: rtl;">
                <h2 style="color: #6c757d;">إشعار من النظام</h2>
                <p>لقد تلقيت إشعاراً جديداً من نظام إدارة المطالبات.</p>
                <p>يرجى مراجعة النظام للمزيد من التفاصيل.</p>
            </div>
            """
        
        return self._render_template(template, context)
    
    def _log_notification_email(self, user: Optional[User], email: str, subject: str, 
                               body: str, notification_type: str, context: Dict):
        """Log notification email to database"""
        try:
            email_log = EmailLog(
                recipient_email=email,
                subject=subject,
                body=body,
                sent_at=datetime.utcnow(),
                status='sent',
                message_id=f"notification_{notification_type}_{datetime.utcnow().timestamp()}",
                claim_id=context.get('claim_id'),
                user_id=user.id if user else None
            )
            
            db.session.add(email_log)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log notification email: {e}")
            db.session.rollback()

# Global notification service instance
notification_service = NotificationService()

def send_claim_notification(notification_type: str, claim: Claim, additional_context: Dict = None):
    """
    Send notification for claim-related events
    
    Args:
        notification_type: Type of notification
        claim: Claim object
        additional_context: Additional context data
    """
    if not Config.NOTIFICATIONS_ENABLED:
        return
    
    # Prepare context
    context = {
        'claim_id': claim.id,
        'client_name': claim.client_name,
        'claim_amount': float(claim.claim_amount),
        'company_name': claim.insurance_company.name_ar,
        'created_by': claim.created_by.full_name,
        'created_at': claim.created_at.strftime('%Y-%m-%d %H:%M'),
        'status': claim.status
    }
    
    if additional_context:
        context.update(additional_context)
    
    # Get recipients (for now, notify all admin users)
    recipients = []
    admin_users = User.query.filter_by(role='admin', active=True).all()
    
    for user in admin_users:
        recipients.append({
            'user': user,
            'email': user.email,
            'phone': None,  # Add phone field to User model if needed
            'language': 'ar'  # Default to Arabic
        })
    
    # Send notifications
    notification_service.send_notification(notification_type, recipients, context)
