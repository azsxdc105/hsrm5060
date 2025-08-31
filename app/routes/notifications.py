#!/usr/bin/env python3
"""
Routes for notifications management
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import SimpleNotification as Notification, NotificationPreference
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/')
@login_required
def index():
    """Display user notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Mark notifications as read when viewed
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in unread_notifications:
        notification.mark_as_read()
    
    return render_template('notifications/index.html', notifications=notifications)

@notifications_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """Get count of unread notifications"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'count': count})

@notifications_bp.route('/api/recent')
@login_required
def api_recent():
    """Get recent notifications for dropdown"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'notifications': [notification.to_dict() for notification in notifications]
    })

@notifications_bp.route('/api/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def api_mark_read(notification_id):
    """Mark specific notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.mark_as_read()
    
    return jsonify({'success': True})

@notifications_bp.route('/api/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_read():
    """Mark all notifications as read"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'count': len(notifications)})

@notifications_bp.route('/preferences')
@login_required
def preferences():
    """Display notification preferences"""
    # Get or create preferences for different notification types
    notification_types = [
        'claim_created',
        'claim_status_changed',
        'claim_sent',
        'system_maintenance',
        'weekly_report'
    ]
    
    preferences = {}
    for notification_type in notification_types:
        pref = NotificationPreference.query.filter_by(
            user_id=current_user.id,
            notification_type=notification_type
        ).first()
        
        if not pref:
            # Create default preference
            pref = NotificationPreference(
                user_id=current_user.id,
                notification_type=notification_type,
                email_enabled=True,
                sms_enabled=False,
                push_enabled=True
            )
            db.session.add(pref)
        
        preferences[notification_type] = pref
    
    db.session.commit()
    
    return render_template('notifications/preferences.html', preferences=preferences)

@notifications_bp.route('/preferences/update', methods=['POST'])
@login_required
def update_preferences():
    """Update notification preferences"""
    try:
        data = request.get_json()
        
        for notification_type, settings in data.items():
            pref = NotificationPreference.query.filter_by(
                user_id=current_user.id,
                notification_type=notification_type
            ).first()
            
            if pref:
                pref.email_enabled = settings.get('email', True)
                pref.sms_enabled = settings.get('sms', False)
                pref.push_enabled = settings.get('push', True)
                pref.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم تحديث إعدادات الإشعارات بنجاح'})
        
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        db.session.rollback()
        return jsonify({'error': 'حدث خطأ في تحديث الإعدادات'}), 500

@notifications_bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """Send test notification (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'غير مسموح'}), 403
    
    try:
        from app.notifications import notification_service
        
        # Send test notification
        recipients = [{
            'user': current_user,
            'email': current_user.email,
            'phone': current_user.phone,
            'language': getattr(current_user, 'language', 'ar')
        }]
        
        context = {
            'claim_id': 'TEST-001',
            'client_name': 'عميل تجريبي',
            'claim_amount': 1000.0,
            'company_name': 'شركة تجريبية',
            'created_by': current_user.full_name,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        notification_service.send_notification('claim_created', recipients, context)
        
        return jsonify({'success': True, 'message': 'تم إرسال إشعار تجريبي'})
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return jsonify({'error': 'فشل في إرسال الإشعار التجريبي'}), 500

@notifications_bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete specific notification"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()
    
    if not notification:
        flash('الإشعار غير موجود', 'error')
        return redirect(url_for('notifications.index'))
    
    db.session.delete(notification)
    db.session.commit()
    
    flash('تم حذف الإشعار بنجاح', 'success')
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all():
    """Clear all notifications for current user"""
    notifications = Notification.query.filter_by(user_id=current_user.id).all()
    
    for notification in notifications:
        db.session.delete(notification)
    
    db.session.commit()
    
    flash(f'تم حذف {len(notifications)} إشعار', 'success')
    return redirect(url_for('notifications.index'))
