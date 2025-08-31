#!/usr/bin/env python3
"""
Advanced Notifications System
Supports Email, SMS, Push Notifications, WhatsApp, and In-App notifications
"""
import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from flask import current_app, render_template_string, url_for
from flask_mail import Message
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from app import db, mail
from app.models import (
    User, Claim, Notification, NotificationTemplate, 
    UserNotificationSettings, NotificationQueue,
    NotificationType, NotificationPriority
)
import uuid
import threading
from queue import Queue
import time

logger = logging.getLogger(__name__)

class AdvancedNotificationService:
    """Advanced notification service with multiple delivery channels"""
    
    def __init__(self):
        self.twilio_client = None
        self.whatsapp_client = None
        self.push_service = None
        self.processing_queue = Queue()
        self.setup_clients()
        self.start_background_processor()
    
    def setup_clients(self):
        """Setup external service clients"""
        # Setup Twilio for SMS
        try:
            twilio_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            twilio_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            if twilio_sid and twilio_token:
                self.twilio_client = Client(twilio_sid, twilio_token)
                logger.info("Twilio SMS client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {e}")
        
        # Setup WhatsApp Business API
        try:
            whatsapp_token = current_app.config.get('WHATSAPP_ACCESS_TOKEN')
            if whatsapp_token:
                self.whatsapp_client = WhatsAppClient(whatsapp_token)
                logger.info("WhatsApp client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp: {e}")
        
        # Setup Push Notification Service
        try:
            firebase_key = current_app.config.get('FIREBASE_SERVER_KEY')
            if firebase_key:
                self.push_service = PushNotificationService(firebase_key)
                logger.info("Push notification service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize push service: {e}")
    
    def start_background_processor(self):
        """Start background thread for processing notifications"""
        def process_notifications():
            while True:
                try:
                    # Process scheduled notifications
                    self.process_scheduled_notifications()
                    # Process queue items
                    self.process_notification_queue()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Background processor error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        thread = threading.Thread(target=process_notifications, daemon=True)
        thread.start()
        logger.info("Background notification processor started")
    
    def send_notification(self, 
                         user_id: int,
                         title: str,
                         message: str,
                         notification_types: List[str] = None,
                         priority: str = 'normal',
                         event_type: str = None,
                         claim_id: str = None,
                         scheduled_for: datetime = None,
                         metadata: Dict = None) -> Dict[str, Any]:
        """
        Send notification through multiple channels
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification message
            notification_types: List of notification types to send ['email', 'sms', 'push', 'whatsapp', 'in_app']
            priority: Notification priority ('low', 'normal', 'high', 'urgent')
            event_type: Event type for template matching
            claim_id: Related claim ID
            scheduled_for: Schedule notification for future delivery
            metadata: Additional metadata
        
        Returns:
            Dict with delivery results
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get user notification settings
            settings = self.get_user_settings(user_id)
            
            # Determine notification types to send
            if not notification_types:
                notification_types = self.get_enabled_notification_types(settings, event_type)
            
            results = {}
            
            # Create notification records and send
            for notification_type in notification_types:
                if self.should_send_notification(settings, notification_type, event_type):
                    result = self.create_and_send_notification(
                        user=user,
                        title=title,
                        message=message,
                        notification_type=notification_type,
                        priority=priority,
                        event_type=event_type,
                        claim_id=claim_id,
                        scheduled_for=scheduled_for,
                        metadata=metadata
                    )
                    results[notification_type] = result
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_and_send_notification(self, 
                                   user: User,
                                   title: str,
                                   message: str,
                                   notification_type: str,
                                   priority: str,
                                   event_type: str = None,
                                   claim_id: str = None,
                                   scheduled_for: datetime = None,
                                   metadata: Dict = None) -> Dict[str, Any]:
        """Create notification record and send it"""
        try:
            # Create notification record
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                notification_type=NotificationType(notification_type),
                priority=NotificationPriority(priority),
                event_type=event_type,
                claim_id=claim_id,
                scheduled_for=scheduled_for or datetime.utcnow()
            )
            
            if metadata:
                notification.set_extra_data(metadata)
            
            db.session.add(notification)
            db.session.flush()  # Get the ID
            
            # Send immediately if not scheduled
            if not scheduled_for or scheduled_for <= datetime.utcnow():
                result = self.deliver_notification(notification, user)
            else:
                result = {'success': True, 'status': 'scheduled'}
            
            db.session.commit()
            return result
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def deliver_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Deliver notification through appropriate channel"""
        try:
            notification_type = notification.notification_type.value
            
            if notification_type == 'email':
                return self.send_email_notification(notification, user)
            elif notification_type == 'sms':
                return self.send_sms_notification(notification, user)
            elif notification_type == 'push':
                return self.send_push_notification(notification, user)
            elif notification_type == 'whatsapp':
                return self.send_whatsapp_notification(notification, user)
            elif notification_type == 'in_app':
                return self.send_in_app_notification(notification, user)
            else:
                return {'success': False, 'error': f'Unknown notification type: {notification_type}'}
                
        except Exception as e:
            notification.mark_as_failed(str(e))
            db.session.commit()
            logger.error(f"Failed to deliver notification {notification.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_email_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Send email notification"""
        try:
            # Create HTML email content
            html_content = self.create_email_html(notification, user)
            
            msg = Message(
                subject=notification.title,
                recipients=[user.email],
                html=html_content,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            mail.send(msg)
            
            notification.mark_as_sent()
            notification.mark_as_delivered()  # Assume delivered for email
            
            delivery_details = {
                'recipient': user.email,
                'sent_at': datetime.utcnow().isoformat()
            }
            notification.set_delivery_details(delivery_details)
            
            db.session.commit()
            
            logger.info(f"Email notification sent to {user.email}")
            return {'success': True, 'status': 'delivered'}
            
        except Exception as e:
            notification.mark_as_failed(str(e))
            db.session.commit()
            logger.error(f"Failed to send email notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_sms_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Send SMS notification"""
        if not self.twilio_client or not user.phone:
            return {'success': False, 'error': 'SMS not available'}
        
        try:
            # Create SMS content (shorter version)
            sms_content = self.create_sms_content(notification, user)
            
            message = self.twilio_client.messages.create(
                body=sms_content,
                from_=current_app.config.get('TWILIO_PHONE_NUMBER'),
                to=user.phone
            )
            
            notification.mark_as_sent()
            
            delivery_details = {
                'recipient': user.phone,
                'message_sid': message.sid,
                'sent_at': datetime.utcnow().isoformat()
            }
            notification.set_delivery_details(delivery_details)
            
            db.session.commit()
            
            logger.info(f"SMS notification sent to {user.phone}")
            return {'success': True, 'status': 'sent', 'message_sid': message.sid}
            
        except TwilioException as e:
            notification.mark_as_failed(str(e))
            db.session.commit()
            logger.error(f"Twilio SMS error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            notification.mark_as_failed(str(e))
            db.session.commit()
            logger.error(f"Failed to send SMS notification: {e}")
            return {'success': False, 'error': str(e)}

    def send_push_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Send push notification"""
        if not self.push_service:
            return {'success': False, 'error': 'Push service not available'}

        try:
            settings = self.get_user_settings(user.id)
            if not settings.push_token:
                return {'success': False, 'error': 'No push token for user'}

            result = self.push_service.send_notification(
                token=settings.push_token,
                title=notification.title,
                body=notification.message,
                data={
                    'notification_id': notification.id,
                    'event_type': notification.event_type,
                    'claim_id': notification.claim_id
                }
            )

            if result['success']:
                notification.mark_as_sent()
                notification.set_delivery_details(result)
                db.session.commit()
                logger.info(f"Push notification sent to user {user.id}")
                return result
            else:
                notification.mark_as_failed(result.get('error', 'Unknown error'))
                db.session.commit()
                return result

        except Exception as e:
            notification.mark_as_failed(str(e))
            db.session.commit()
            logger.error(f"Failed to send push notification: {e}")
            return {'success': False, 'error': str(e)}

    def send_whatsapp_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Send WhatsApp notification"""
        if not self.whatsapp_client:
            return {'success': False, 'error': 'WhatsApp service not available'}

        try:
            # Try to get WhatsApp number from user profile first, then from settings
            whatsapp_number = user.whatsapp_number
            if not whatsapp_number:
                settings = self.get_user_settings(user.id)
                whatsapp_number = settings.whatsapp_phone if hasattr(settings, 'whatsapp_phone') else None

            if not whatsapp_number:
                return {'success': False, 'error': 'No WhatsApp number for user'}

            result = self.whatsapp_client.send_message(
                to=whatsapp_number,
                message=f"*{notification.title}*\n\n{notification.message}"
            )

            if result['success']:
                notification.mark_as_sent()
                notification.set_delivery_details(result)
                db.session.commit()
                logger.info(f"WhatsApp notification sent to {settings.whatsapp_phone}")
                return result
            else:
                notification.mark_as_failed(result.get('error', 'Unknown error'))
                db.session.commit()
                return result

        except Exception as e:
            notification.mark_as_failed(str(e))
            db.session.commit()
            logger.error(f"Failed to send WhatsApp notification: {e}")
            return {'success': False, 'error': str(e)}

    def send_in_app_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Send in-app notification (just mark as sent, will be displayed in UI)"""
        try:
            notification.mark_as_sent()
            notification.mark_as_delivered()

            delivery_details = {
                'type': 'in_app',
                'sent_at': datetime.utcnow().isoformat()
            }
            notification.set_delivery_details(delivery_details)

            db.session.commit()

            logger.info(f"In-app notification created for user {user.id}")
            return {'success': True, 'status': 'delivered'}

        except Exception as e:
            notification.mark_as_failed(str(e))
            db.session.commit()
            logger.error(f"Failed to create in-app notification: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_settings(self, user_id: int) -> UserNotificationSettings:
        """Get or create user notification settings"""
        settings = UserNotificationSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = UserNotificationSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
        return settings

    def get_enabled_notification_types(self, settings: UserNotificationSettings, event_type: str = None) -> List[str]:
        """Get list of enabled notification types for user"""
        enabled_types = []

        if settings.email_enabled:
            enabled_types.append('email')
        if settings.sms_enabled:
            enabled_types.append('sms')
        if settings.push_enabled:
            enabled_types.append('push')
        if settings.whatsapp_enabled:
            enabled_types.append('whatsapp')
        if settings.in_app_enabled:
            enabled_types.append('in_app')

        # Filter by event-specific settings if provided
        if event_type:
            event_settings = settings.get_event_settings()
            if event_type in event_settings:
                filtered_types = []
                for notification_type in enabled_types:
                    if event_settings[event_type].get(notification_type, True):
                        filtered_types.append(notification_type)
                return filtered_types

        return enabled_types

    def should_send_notification(self, settings: UserNotificationSettings, notification_type: str, event_type: str = None) -> bool:
        """Check if notification should be sent based on user settings"""
        # Check quiet hours
        if settings.quiet_hours_enabled and self.is_in_quiet_hours(settings):
            return False

        return settings.is_notification_enabled(notification_type, event_type)

    def is_in_quiet_hours(self, settings: UserNotificationSettings) -> bool:
        """Check if current time is in user's quiet hours"""
        if not settings.quiet_hours_enabled or not settings.quiet_hours_start or not settings.quiet_hours_end:
            return False

        now = datetime.now().time()
        start = settings.quiet_hours_start
        end = settings.quiet_hours_end

        if start <= end:
            return start <= now <= end
        else:  # Quiet hours span midnight
            return now >= start or now <= end

    def create_email_html(self, notification: Notification, user: User) -> str:
        """Create HTML content for email notification"""
        priority_text = {
            'low': 'منخفض',
            'normal': 'عادي',
            'high': 'عالي',
            'urgent': 'عاجل'
        }

        template = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{notification.title}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .message {{ font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 20px; }}
                .priority {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
                .priority-high {{ background-color: #ffc107; color: #856404; }}
                .priority-urgent {{ background-color: #dc3545; color: white; }}
                .priority-normal {{ background-color: #28a745; color: white; }}
                .priority-low {{ background-color: #6c757d; color: white; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #6c757d; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{notification.title}</h1>
                    <span class="priority priority-{notification.priority.value if notification.priority else 'normal'}">
                        {priority_text.get(notification.priority.value if notification.priority else 'normal', 'عادي')}
                    </span>
                </div>
                <div class="content">
                    <div class="message">
                        {notification.message}
                    </div>
                    {self.get_claim_details_html(notification) if notification.claim_id else ''}
                </div>
                <div class="footer">
                    <p>نظام إدارة مطالبات التأمين</p>
                    <p>تم الإرسال في: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return template

    def create_sms_content(self, notification: Notification, user: User) -> str:
        """Create SMS content (shorter version)"""
        content = f"{notification.title}\n\n{notification.message[:100]}"
        if len(notification.message) > 100:
            content += "..."

        if notification.claim_id:
            content += f"\n\nرقم المطالبة: {notification.claim_id}"

        return content

    def get_claim_details_html(self, notification: Notification) -> str:
        """Get claim details HTML for email"""
        if not notification.claim_id:
            return ""

        try:
            claim = Claim.query.get(notification.claim_id)
            if not claim:
                return ""

            return f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #007bff; margin-top: 0;">تفاصيل المطالبة</h3>
                <ul style="list-style: none; padding: 0;">
                    <li><strong>رقم المطالبة:</strong> {claim.id}</li>
                    <li><strong>العميل:</strong> {claim.client_name}</li>
                    <li><strong>المبلغ:</strong> {claim.claim_amount} {claim.currency}</li>
                    <li><strong>شركة التأمين:</strong> {claim.insurance_company.name_ar}</li>
                    <li><strong>الحالة:</strong> {claim.status}</li>
                </ul>
            </div>
            """
        except Exception as e:
            logger.error(f"Error getting claim details: {e}")
            return ""

    def process_scheduled_notifications(self):
        """Process notifications scheduled for current time"""
        try:
            # Get notifications scheduled for now or earlier
            scheduled_notifications = Notification.query.filter(
                Notification.status == 'pending',
                Notification.scheduled_for <= datetime.utcnow()
            ).all()

            for notification in scheduled_notifications:
                try:
                    user = User.query.get(notification.user_id)
                    if user:
                        self.deliver_notification(notification, user)
                except Exception as e:
                    logger.error(f"Failed to process scheduled notification {notification.id}: {e}")
                    notification.mark_as_failed(str(e))
                    db.session.commit()

        except Exception as e:
            logger.error(f"Error processing scheduled notifications: {e}")

    def process_notification_queue(self):
        """Process notification queue items"""
        try:
            # Get queue items ready for processing
            queue_items = NotificationQueue.query.filter(
                NotificationQueue.status == 'pending',
                NotificationQueue.scheduled_for <= datetime.utcnow()
            ).limit(10).all()  # Process 10 at a time

            for queue_item in queue_items:
                try:
                    self.process_queue_item(queue_item)
                except Exception as e:
                    logger.error(f"Failed to process queue item {queue_item.id}: {e}")
                    queue_item.mark_as_failed(str(e))
                    db.session.commit()

        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")

    def process_queue_item(self, queue_item: NotificationQueue):
        """Process a single queue item"""
        try:
            queue_item.mark_as_processing()
            db.session.commit()

            recipients = queue_item.get_recipients_list()
            context = queue_item.get_context_data()

            successful = 0
            failed = 0

            for recipient in recipients:
                try:
                    user_id = recipient.get('user_id')
                    if not user_id:
                        failed += 1
                        continue

                    # Send notification
                    result = self.send_notification(
                        user_id=user_id,
                        title=recipient.get('title', 'إشعار'),
                        message=recipient.get('message', ''),
                        notification_types=[queue_item.notification_type.value],
                        priority=recipient.get('priority', 'normal'),
                        event_type=queue_item.event_type,
                        metadata=context
                    )

                    if result['success']:
                        successful += 1
                    else:
                        failed += 1

                except Exception as e:
                    logger.error(f"Failed to send to recipient {recipient}: {e}")
                    failed += 1

            queue_item.mark_as_completed(successful, failed)
            db.session.commit()

        except Exception as e:
            queue_item.mark_as_failed(str(e))
            db.session.commit()
            raise
