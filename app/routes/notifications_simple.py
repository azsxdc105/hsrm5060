#!/usr/bin/env python3
"""
Simple notifications routes (placeholder)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import SimpleNotification, NotificationPreference, Notification
from app.notification_manager import NotificationManager
from datetime import datetime

def admin_required(f):
    """Simple admin required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('يجب أن تكون مديراً للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/')
@login_required
def index():
    """صفحة الإشعارات"""
    # Get notifications for current user
    notifications = NotificationManager.get_user_notifications(current_user.id, limit=50)
    unread_count = NotificationManager.get_unread_count(current_user.id)

    return render_template('notifications/index.html',
                         notifications=notifications,
                         unread_count=unread_count)

@notifications_bp.route('/mark-read/<notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark notification as read"""
    success = NotificationManager.mark_notification_read(notification_id, current_user.id)

    if request.is_json:
        return jsonify({'success': success})

    if success:
        flash('تم تحديد الإشعار كمقروء', 'success')
    else:
        flash('فشل في تحديث الإشعار', 'error')

    return redirect(url_for('notifications.index'))

@notifications_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """API endpoint for unread notifications count"""
    count = NotificationManager.get_unread_count(current_user.id)
    return jsonify({'count': count})

@notifications_bp.route('/api/recent')
@login_required
def api_recent():
    """API endpoint for recent notifications"""
    notifications = NotificationManager.get_user_notifications(current_user.id, limit=5)

    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'read_at': notification.read_at.strftime('%Y-%m-%d %H:%M') if notification.read_at else None,
            'priority': notification.priority.value if notification.priority else 'normal',
            'claim_id': notification.claim_id
        })

    return jsonify({'notifications': notifications_data})

@notifications_bp.route('/preferences')
@login_required
def preferences():
    """إعدادات الإشعارات"""
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

@notifications_bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all():
    """مسح جميع الإشعارات المقروءة"""
    try:
        # Mark all unread notifications as read
        notifications = Notification.query.filter_by(
            user_id=current_user.id,
            read_at=None
        ).all()

        for notification in notifications:
            notification.read_at = datetime.utcnow()
            notification.status = 'read'

        db.session.commit()
        flash(f'تم تحديد {len(notifications)} إشعار كمقروء', 'success')

    except Exception as e:
        db.session.rollback()
        flash('فشل في مسح الإشعارات', 'error')

    return redirect(url_for('notifications.index'))
