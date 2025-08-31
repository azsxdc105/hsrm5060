#!/usr/bin/env python3
"""
External notification services (WhatsApp, Push Notifications)
"""
import logging
import requests
import json
import os
from typing import Dict, Any, List
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

def get_whatsapp_client():
    """Get configured WhatsApp client"""
    try:
        access_token = os.environ.get('WHATSAPP_ACCESS_TOKEN') or current_app.config.get('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID') or current_app.config.get('WHATSAPP_PHONE_NUMBER_ID')

        if access_token and phone_number_id:
            return WhatsAppClient(access_token, phone_number_id)
        else:
            logger.warning("WhatsApp credentials not configured")
            return None
    except Exception as e:
        logger.error(f"Error creating WhatsApp client: {e}")
        return None

def send_whatsapp_notification(phone_number: str, title: str, message: str) -> bool:
    """Send WhatsApp notification using configured client"""
    try:
        client = get_whatsapp_client()
        if not client:
            logger.warning("WhatsApp client not available")
            return False

        # Format message with title
        full_message = f"*{title}*\n\n{message}"

        result = client.send_message(phone_number, full_message)

        if result.get('success'):
            logger.info(f"WhatsApp message sent successfully to {phone_number}")
            return True
        else:
            logger.error(f"Failed to send WhatsApp message: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"Error sending WhatsApp notification: {e}")
        return False

class WhatsAppClient:
    """WhatsApp Business API client"""
    
    def __init__(self, access_token: str, phone_number_id: str = None):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = "https://graph.facebook.com/v17.0"
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_message(self, to: str, message: str, message_type: str = 'text') -> Dict[str, Any]:
        """Send WhatsApp message"""
        try:
            # Clean phone number (remove + and spaces)
            to = to.replace('+', '').replace(' ', '').replace('-', '')
            
            if message_type == 'text':
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {
                        "body": message
                    }
                }
            else:
                return {'success': False, 'error': 'Unsupported message type'}
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'status': 'sent',
                    'sent_at': datetime.utcnow().isoformat()
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Unknown error'),
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_template_message(self, to: str, template_name: str, language: str = 'ar', 
                            parameters: List[str] = None) -> Dict[str, Any]:
        """Send WhatsApp template message"""
        try:
            to = to.replace('+', '').replace(' ', '').replace('-', '')
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language
                    }
                }
            }
            
            if parameters:
                payload["template"]["components"] = [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in parameters]
                }]
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'status': 'sent',
                    'sent_at': datetime.utcnow().isoformat()
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Unknown error'),
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"WhatsApp template send error: {e}")
            return {'success': False, 'error': str(e)}


class PushNotificationService:
    """Firebase Cloud Messaging (FCM) push notification service"""
    
    def __init__(self, server_key: str):
        self.server_key = server_key
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.headers = {
            'Authorization': f'key={server_key}',
            'Content-Type': 'application/json'
        }
    
    def send_notification(self, token: str, title: str, body: str, 
                         data: Dict[str, Any] = None, 
                         click_action: str = None) -> Dict[str, Any]:
        """Send push notification to single device"""
        try:
            payload = {
                "to": token,
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": "/static/img/notification-icon.png",
                    "sound": "default"
                }
            }
            
            if click_action:
                payload["notification"]["click_action"] = click_action
            
            if data:
                payload["data"] = data
            
            response = requests.post(self.fcm_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') == 1:
                    return {
                        'success': True,
                        'message_id': result.get('results', [{}])[0].get('message_id'),
                        'status': 'sent',
                        'sent_at': datetime.utcnow().isoformat()
                    }
                else:
                    error = result.get('results', [{}])[0].get('error', 'Unknown error')
                    return {'success': False, 'error': error}
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Push notification send error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_to_multiple(self, tokens: List[str], title: str, body: str,
                        data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send push notification to multiple devices"""
        try:
            payload = {
                "registration_ids": tokens,
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": "/static/img/notification-icon.png",
                    "sound": "default"
                }
            }
            
            if data:
                payload["data"] = data
            
            response = requests.post(self.fcm_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'success_count': result.get('success', 0),
                    'failure_count': result.get('failure', 0),
                    'results': result.get('results', []),
                    'sent_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Push notification batch send error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_to_topic(self, topic: str, title: str, body: str,
                     data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send push notification to topic subscribers"""
        try:
            payload = {
                "to": f"/topics/{topic}",
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": "/static/img/notification-icon.png",
                    "sound": "default"
                }
            }
            
            if data:
                payload["data"] = data
            
            response = requests.post(self.fcm_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('message_id'),
                    'sent_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Push notification topic send error: {e}")
            return {'success': False, 'error': str(e)}


class EmailTemplateService:
    """Service for managing email templates"""
    
    @staticmethod
    def get_claim_notification_template(event_type: str, language: str = 'ar') -> Dict[str, str]:
        """Get email template for claim notifications"""
        templates = {
            'claim_created': {
                'ar': {
                    'subject': 'تم إنشاء مطالبة جديدة - {claim_id}',
                    'title': 'مطالبة جديدة',
                    'message': 'تم إنشاء مطالبة تأمين جديدة برقم {claim_id} للعميل {client_name} بمبلغ {claim_amount} {currency}.'
                },
                'en': {
                    'subject': 'New Claim Created - {claim_id}',
                    'title': 'New Claim',
                    'message': 'A new insurance claim {claim_id} has been created for client {client_name} with amount {claim_amount} {currency}.'
                }
            },
            'claim_sent': {
                'ar': {
                    'subject': 'تم إرسال المطالبة - {claim_id}',
                    'title': 'تم إرسال المطالبة',
                    'message': 'تم إرسال المطالبة {claim_id} بنجاح إلى شركة التأمين {company_name}.'
                },
                'en': {
                    'subject': 'Claim Sent - {claim_id}',
                    'title': 'Claim Sent',
                    'message': 'Claim {claim_id} has been successfully sent to insurance company {company_name}.'
                }
            },
            'claim_status_changed': {
                'ar': {
                    'subject': 'تغيير حالة المطالبة - {claim_id}',
                    'title': 'تحديث حالة المطالبة',
                    'message': 'تم تغيير حالة المطالبة {claim_id} من {old_status} إلى {new_status}.'
                },
                'en': {
                    'subject': 'Claim Status Changed - {claim_id}',
                    'title': 'Claim Status Update',
                    'message': 'Claim {claim_id} status has been changed from {old_status} to {new_status}.'
                }
            }
        }
        
        return templates.get(event_type, {}).get(language, templates.get(event_type, {}).get('ar', {}))


# Global service instances
notification_service = None

def get_notification_service():
    """Get global notification service instance"""
    global notification_service
    if notification_service is None:
        from app.advanced_notifications import AdvancedNotificationService
        notification_service = AdvancedNotificationService()
    return notification_service


def send_claim_notification(event_type: str, claim, additional_recipients: List[int] = None, 
                          custom_message: str = None, priority: str = 'normal'):
    """
    Convenient function to send claim-related notifications
    
    Args:
        event_type: Type of event (claim_created, claim_sent, etc.)
        claim: Claim object
        additional_recipients: Additional user IDs to notify
        custom_message: Custom message override
        priority: Notification priority
    """
    try:
        service = get_notification_service()
        
        # Get template
        template = EmailTemplateService.get_claim_notification_template(event_type, 'ar')
        
        # Prepare context
        context = {
            'claim_id': claim.id,
            'client_name': claim.client_name,
            'claim_amount': float(claim.claim_amount),
            'currency': claim.currency,
            'company_name': claim.insurance_company.name_ar,
            'status': claim.status,
            'created_by': claim.created_by.full_name if claim.created_by else 'النظام'
        }
        
        title = template.get('title', 'إشعار')
        message = custom_message or template.get('message', '').format(**context)
        
        # Get recipients (admins + additional)
        from app.models import User
        recipients = User.query.filter_by(role='admin', active=True).all()
        
        if additional_recipients:
            additional_users = User.query.filter(User.id.in_(additional_recipients)).all()
            recipients.extend(additional_users)
        
        # Send notifications
        results = []
        for user in recipients:
            result = service.send_notification(
                user_id=user.id,
                title=title,
                message=message,
                priority=priority,
                event_type=event_type,
                claim_id=claim.id,
                metadata=context
            )
            results.append(result)
        
        return {'success': True, 'results': results}
        
    except Exception as e:
        logger.error(f"Failed to send claim notification: {e}")
        return {'success': False, 'error': str(e)}
