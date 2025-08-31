#!/usr/bin/env python3
"""
Advanced Notifications Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import json

from app import db
from app.models import (
    User, Notification, NotificationTemplate, UserNotificationSettings,
    NotificationQueue, NotificationType, NotificationPriority
)
from app.forms import (
    NotificationSettingsForm, SendNotificationForm, NotificationTemplateForm,
    BulkNotificationForm, WhatsAppTestForm
)
from app.notification_services import get_notification_service, send_claim_notification

advanced_notifications_bp = Blueprint('advanced_notifications', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('يجب أن تكون مديراً للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@advanced_notifications_bp.route('/')
@login_required
def index():
    """Notifications dashboard"""
    # Get user's notifications
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Get unread count
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        status='delivered'
    ).count()
    
    # Get statistics
    stats = {
        'total': Notification.query.filter_by(user_id=current_user.id).count(),
        'unread': unread_count,
        'read': Notification.query.filter_by(user_id=current_user.id, status='read').count(),
        'failed': Notification.query.filter_by(user_id=current_user.id, status='failed').count()
    }
    
    return render_template('notifications/advanced/index.html',
                         notifications=notifications,
                         stats=stats,
                         unread_count=unread_count)


@advanced_notifications_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User notification settings"""
    # Get or create user settings
    user_settings = UserNotificationSettings.query.filter_by(user_id=current_user.id).first()
    if not user_settings:
        user_settings = UserNotificationSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()
    
    form = NotificationSettingsForm(obj=user_settings)
    
    if form.validate_on_submit():
        # Update basic settings
        user_settings.email_enabled = form.email_enabled.data
        user_settings.sms_enabled = form.sms_enabled.data
        user_settings.push_enabled = form.push_enabled.data
        user_settings.whatsapp_enabled = form.whatsapp_enabled.data
        user_settings.in_app_enabled = form.in_app_enabled.data
        user_settings.whatsapp_phone = form.whatsapp_phone.data
        user_settings.quiet_hours_enabled = form.quiet_hours_enabled.data
        user_settings.quiet_hours_start = form.quiet_hours_start.data
        user_settings.quiet_hours_end = form.quiet_hours_end.data
        
        # Update event-specific settings
        event_settings = {
            'claim_created': {
                'email': form.claim_created_email.data,
                'sms': form.claim_created_sms.data,
                'push': form.claim_created_push.data,
                'whatsapp': form.claim_created_whatsapp.data
            },
            'claim_sent': {
                'email': form.claim_sent_email.data,
                'sms': form.claim_sent_sms.data,
                'push': form.claim_sent_push.data,
                'whatsapp': form.claim_sent_whatsapp.data
            },
            'claim_status_changed': {
                'email': form.claim_status_changed_email.data,
                'sms': form.claim_status_changed_sms.data,
                'push': form.claim_status_changed_push.data,
                'whatsapp': form.claim_status_changed_whatsapp.data
            }
        }
        user_settings.set_event_settings(event_settings)
        
        db.session.commit()
        flash('تم حفظ إعدادات الإشعارات بنجاح', 'success')
        return redirect(url_for('advanced_notifications.settings'))
    
    # Populate event-specific fields
    if user_settings.event_settings:
        event_settings = user_settings.get_event_settings()
        
        # Claim created
        claim_created = event_settings.get('claim_created', {})
        form.claim_created_email.data = claim_created.get('email', True)
        form.claim_created_sms.data = claim_created.get('sms', False)
        form.claim_created_push.data = claim_created.get('push', True)
        form.claim_created_whatsapp.data = claim_created.get('whatsapp', False)
        
        # Claim sent
        claim_sent = event_settings.get('claim_sent', {})
        form.claim_sent_email.data = claim_sent.get('email', True)
        form.claim_sent_sms.data = claim_sent.get('sms', False)
        form.claim_sent_push.data = claim_sent.get('push', True)
        form.claim_sent_whatsapp.data = claim_sent.get('whatsapp', False)
        
        # Claim status changed
        claim_status = event_settings.get('claim_status_changed', {})
        form.claim_status_changed_email.data = claim_status.get('email', True)
        form.claim_status_changed_sms.data = claim_status.get('sms', False)
        form.claim_status_changed_push.data = claim_status.get('push', True)
        form.claim_status_changed_whatsapp.data = claim_status.get('whatsapp', False)
    
    return render_template('notifications/advanced/settings.html',
                         form=form,
                         user_settings=user_settings)


@advanced_notifications_bp.route('/send', methods=['GET', 'POST'])
@login_required
@admin_required
def send_notification():
    """Send custom notification"""
    form = SendNotificationForm()
    
    if form.validate_on_submit():
        try:
            # Determine recipients
            recipients = []
            if form.recipient_type.data == 'all_users':
                recipients = User.query.filter_by(active=True).all()
            elif form.recipient_type.data == 'admins':
                recipients = User.query.filter_by(role='admin', active=True).all()
            elif form.recipient_type.data == 'agents':
                recipients = User.query.filter_by(role='claims_agent', active=True).all()
            elif form.recipient_type.data == 'specific':
                if form.specific_users.data:
                    user_ids = [int(id.strip()) for id in form.specific_users.data.split(',') if id.strip().isdigit()]
                    recipients = User.query.filter(User.id.in_(user_ids)).all()
            
            if not recipients:
                flash('لم يتم العثور على مستلمين', 'error')
                return render_template('notifications/advanced/send.html', form=form)
            
            # Determine notification types
            notification_types = []
            if form.notification_types.data == 'all':
                notification_types = ['email', 'sms', 'push', 'whatsapp', 'in_app']
            else:
                notification_types = form.notification_types.data.split(',')
            
            # Determine scheduling
            scheduled_for = None
            if not form.send_immediately.data and form.scheduled_date.data:
                scheduled_time = form.scheduled_time.data or datetime.min.time()
                scheduled_for = datetime.combine(form.scheduled_date.data, scheduled_time)
            
            # Send notifications
            service = get_notification_service()
            results = []
            
            for user in recipients:
                result = service.send_notification(
                    user_id=user.id,
                    title=form.title.data,
                    message=form.message.data,
                    notification_types=notification_types,
                    priority=form.priority.data,
                    scheduled_for=scheduled_for,
                    metadata={'sent_by': current_user.id, 'sent_by_name': current_user.full_name}
                )
                results.append(result)
            
            successful = sum(1 for r in results if r.get('success'))
            failed = len(results) - successful
            
            if successful > 0:
                flash(f'تم إرسال {successful} إشعار بنجاح', 'success')
            if failed > 0:
                flash(f'فشل في إرسال {failed} إشعار', 'warning')
            
            return redirect(url_for('advanced_notifications.index'))
            
        except Exception as e:
            flash(f'حدث خطأ أثناء الإرسال: {str(e)}', 'error')
    
    return render_template('notifications/advanced/send.html', form=form)


@advanced_notifications_bp.route('/templates')
@login_required
@admin_required
def templates():
    """Manage notification templates"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    templates = NotificationTemplate.query.order_by(NotificationTemplate.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('notifications/advanced/templates.html', templates=templates)


@advanced_notifications_bp.route('/templates/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_template():
    """Create new notification template"""
    form = NotificationTemplateForm()
    
    if form.validate_on_submit():
        template = NotificationTemplate(
            name=form.name.data,
            event_type=form.event_type.data,
            notification_type=NotificationType(form.notification_type.data),
            subject_ar=form.subject_ar.data,
            content_ar=form.content_ar.data,
            subject_en=form.subject_en.data,
            content_en=form.content_en.data,
            variables=form.variables.data,
            active=form.active.data
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash('تم إنشاء القالب بنجاح', 'success')
        return redirect(url_for('advanced_notifications.templates'))
    
    return render_template('notifications/advanced/template_form.html', form=form, title='إنشاء قالب جديد')


@advanced_notifications_bp.route('/templates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_template(id):
    """Edit notification template"""
    template = NotificationTemplate.query.get_or_404(id)
    form = NotificationTemplateForm(obj=template)
    
    if form.validate_on_submit():
        template.name = form.name.data
        template.event_type = form.event_type.data
        template.notification_type = NotificationType(form.notification_type.data)
        template.subject_ar = form.subject_ar.data
        template.content_ar = form.content_ar.data
        template.subject_en = form.subject_en.data
        template.content_en = form.content_en.data
        template.variables = form.variables.data
        template.active = form.active.data
        template.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('تم تحديث القالب بنجاح', 'success')
        return redirect(url_for('advanced_notifications.templates'))
    
    return render_template('notifications/advanced/template_form.html', 
                         form=form, template=template, title='تعديل القالب')


@advanced_notifications_bp.route('/templates/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_template(id):
    """Delete notification template"""
    template = NotificationTemplate.query.get_or_404(id)
    
    db.session.delete(template)
    db.session.commit()
    
    flash('تم حذف القالب بنجاح', 'success')
    return redirect(url_for('advanced_notifications.templates'))


@advanced_notifications_bp.route('/<string:id>/mark_read', methods=['POST'])
@login_required
def mark_as_read(id):
    """Mark notification as read"""
    notification = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    notification.mark_as_read()
    db.session.commit()
    
    return jsonify({'success': True})


@advanced_notifications_bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        status='delivered'
    ).all()
    
    for notification in notifications:
        notification.mark_as_read()
    
    db.session.commit()
    
    return jsonify({'success': True, 'count': len(notifications)})


@advanced_notifications_bp.route('/api/unread_count')
@login_required
def api_unread_count():
    """API endpoint for unread notifications count"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        status='delivered'
    ).count()
    
    return jsonify({'count': count})


@advanced_notifications_bp.route('/api/recent')
@login_required
def api_recent_notifications():
    """API endpoint for recent notifications"""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .limit(10).all()

    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
            'priority': notification.priority.value if notification.priority else 'normal',
            'status': notification.status,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': notification.status == 'read'
        })

    return jsonify({'notifications': notifications_data})


@advanced_notifications_bp.route('/api/statistics')
@login_required
def api_statistics():
    """API endpoint for dashboard statistics"""
    try:
        total_notifications = Notification.query.count()
        active_templates = NotificationTemplate.query.filter_by(active=True).count()
        pending_queue = NotificationQueue.query.filter_by(status='pending').count()

        return jsonify({
            'success': True,
            'total_notifications': total_notifications,
            'active_templates': active_templates,
            'pending_queue': pending_queue
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@advanced_notifications_bp.route('/whatsapp-test', methods=['GET', 'POST'])
@login_required
@admin_required
def whatsapp_test():
    """Test WhatsApp functionality"""
    form = WhatsAppTestForm()
    test_result = None

    if form.validate_on_submit():
        try:
            phone_number = form.phone_number.data
            message = form.message.data
            use_business_api = form.use_business_api.data

            # Clean phone number
            if not phone_number.startswith('+'):
                if phone_number.startswith('966'):
                    phone_number = '+' + phone_number
                elif phone_number.startswith('05'):
                    phone_number = '+966' + phone_number[1:]
                else:
                    phone_number = '+966' + phone_number

            if use_business_api and current_app.config.get('WHATSAPP_ACCESS_TOKEN'):
                # Use WhatsApp Business API
                from app.notification_services import send_whatsapp_notification

                success = send_whatsapp_notification(phone_number, 'رسالة تجريبية', message)

                if success:
                    test_result = {
                        'success': True,
                        'message': f'تم إرسال الرسالة بنجاح إلى {phone_number} عبر WhatsApp Business API',
                        'details': {'method': 'WhatsApp Business API', 'phone': phone_number}
                    }
                else:
                    test_result = {
                        'success': False,
                        'error': 'فشل في إرسال الرسالة عبر WhatsApp Business API',
                        'details': {'method': 'WhatsApp Business API', 'phone': phone_number}
                    }
            else:
                # Use simple WhatsApp Web method
                import urllib.parse
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/{phone_number.replace('+', '')}?text={encoded_message}"

                test_result = {
                    'success': True,
                    'message': f'تم إنشاء رابط واتساب ويب بنجاح',
                    'whatsapp_url': whatsapp_url,
                    'details': {'method': 'WhatsApp Web', 'phone': phone_number, 'url': whatsapp_url}
                }

            flash('تم اختبار الواتساب بنجاح', 'success')

        except Exception as e:
            test_result = {
                'success': False,
                'error': f'خطأ في اختبار الواتساب: {str(e)}',
                'details': {'error': str(e)}
            }
            flash('حدث خطأ أثناء اختبار الواتساب', 'error')

    return render_template('notifications/advanced/whatsapp_test.html',
                         form=form, test_result=test_result)
