#!/usr/bin/env python3
"""
Comprehensive Notification Manager
Handles all types of notifications and events
"""
from flask import current_app
from app import db
from app.models import (
    Notification, NotificationTemplate, UserNotificationSettings, 
    SimpleNotification, User, Claim, NotificationType, NotificationPriority
)
from datetime import datetime
import uuid
import json

class NotificationManager:
    """Centralized notification management"""
    
    @staticmethod
    def create_notification(user_id, title, message, notification_type=NotificationType.IN_APP, 
                          priority=NotificationPriority.NORMAL, claim_id=None, event_type=None):
        """Create a new notification"""
        try:
            # Create advanced notification
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                claim_id=claim_id,
                event_type=event_type,
                status='pending'
            )
            
            db.session.add(notification)
            
            # Also create simple notification for backward compatibility
            simple_notification = SimpleNotification(
                user_id=user_id,
                title=title,
                message=message,
                type='info',
                claim_id=claim_id
            )
            
            db.session.add(simple_notification)
            db.session.commit()
            
            return notification
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create notification: {e}")
            return None
    
    @staticmethod
    def notify_claim_created(claim):
        """Send notification when a claim is created"""
        try:
            # Get all admin users
            admin_users = User.query.filter_by(role='admin', active=True).all()
            
            for user in admin_users:
                NotificationManager.create_notification(
                    user_id=user.id,
                    title="مطالبة جديدة",
                    message=f"تم إنشاء مطالبة جديدة للعميل {claim.client_name} بمبلغ {claim.claim_amount} ريال",
                    notification_type=NotificationType.IN_APP,
                    priority=NotificationPriority.NORMAL,
                    claim_id=claim.id,
                    event_type='claim_created'
                )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send claim created notification: {e}")
            return False
    
    @staticmethod
    def notify_claim_status_changed(claim, old_status, new_status, user):
        """Send notification when claim status changes"""
        try:
            status_names = {
                'draft': 'مسودة',
                'ready': 'جاهز',
                'sent': 'مرسل',
                'failed': 'فشل',
                'acknowledged': 'مستلم',
                'paid': 'مدفوع'
            }
            
            # Determine priority based on status
            priority = NotificationPriority.NORMAL
            if new_status == 'failed':
                priority = NotificationPriority.HIGH
            elif new_status == 'paid':
                priority = NotificationPriority.HIGH
            
            # Get all admin users and the user who created the claim
            users_to_notify = set()
            
            # Add admin users
            admin_users = User.query.filter_by(role='admin', active=True).all()
            users_to_notify.update(admin_users)
            
            # Add claim creator if different from current user
            if claim.created_by_user_id != user.id:
                claim_creator = User.query.get(claim.created_by_user_id)
                if claim_creator and claim_creator.active:
                    users_to_notify.add(claim_creator)
            
            for notify_user in users_to_notify:
                NotificationManager.create_notification(
                    user_id=notify_user.id,
                    title="تغيير حالة المطالبة",
                    message=f"تم تغيير حالة المطالبة {claim.id} من '{status_names.get(old_status, old_status)}' إلى '{status_names.get(new_status, new_status)}'",
                    notification_type=NotificationType.IN_APP,
                    priority=priority,
                    claim_id=claim.id,
                    event_type='claim_status_changed'
                )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send claim status change notification: {e}")
            return False
    
    @staticmethod
    def notify_claim_sent(claim, email_addresses):
        """Send notification when claim is sent via email"""
        try:
            # Get all admin users
            admin_users = User.query.filter_by(role='admin', active=True).all()
            
            # Add claim creator
            claim_creator = User.query.get(claim.created_by_user_id)
            users_to_notify = set(admin_users)
            if claim_creator and claim_creator.active:
                users_to_notify.add(claim_creator)
            
            for user in users_to_notify:
                NotificationManager.create_notification(
                    user_id=user.id,
                    title="تم إرسال المطالبة",
                    message=f"تم إرسال المطالبة {claim.id} للعميل {claim.client_name} إلى {', '.join(email_addresses)}",
                    notification_type=NotificationType.IN_APP,
                    priority=NotificationPriority.NORMAL,
                    claim_id=claim.id,
                    event_type='claim_sent'
                )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send claim sent notification: {e}")
            return False
    
    @staticmethod
    def notify_claim_failed(claim, error_message):
        """Send notification when claim sending fails"""
        try:
            # Get all admin users
            admin_users = User.query.filter_by(role='admin', active=True).all()
            
            # Add claim creator
            claim_creator = User.query.get(claim.created_by_user_id)
            users_to_notify = set(admin_users)
            if claim_creator and claim_creator.active:
                users_to_notify.add(claim_creator)
            
            for user in users_to_notify:
                NotificationManager.create_notification(
                    user_id=user.id,
                    title="فشل في إرسال المطالبة",
                    message=f"فشل في إرسال المطالبة {claim.id} للعميل {claim.client_name}. السبب: {error_message}",
                    notification_type=NotificationType.IN_APP,
                    priority=NotificationPriority.HIGH,
                    claim_id=claim.id,
                    event_type='claim_failed'
                )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send claim failed notification: {e}")
            return False
    
    @staticmethod
    def notify_user_login(user):
        """Send notification when user logs in (for security)"""
        try:
            # Only notify for admin users
            if user.role == 'admin':
                NotificationManager.create_notification(
                    user_id=user.id,
                    title="تسجيل دخول جديد",
                    message=f"تم تسجيل الدخول إلى حسابك في {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    notification_type=NotificationType.IN_APP,
                    priority=NotificationPriority.LOW,
                    event_type='user_login'
                )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send login notification: {e}")
            return False
    
    @staticmethod
    def get_user_notifications(user_id, limit=10, unread_only=False):
        """Get notifications for a user"""
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(read_at=None)
            
            notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
            return notifications
            
        except Exception as e:
            current_app.logger.error(f"Failed to get user notifications: {e}")
            return []
    
    @staticmethod
    def mark_notification_read(notification_id, user_id):
        """Mark a notification as read"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if notification and not notification.read_at:
                notification.read_at = datetime.utcnow()
                notification.status = 'read'
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for a user"""
        try:
            count = Notification.query.filter_by(
                user_id=user_id,
                read_at=None
            ).count()
            return count
            
        except Exception as e:
            current_app.logger.error(f"Failed to get unread count: {e}")
            return 0
