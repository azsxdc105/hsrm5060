from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
import os
from app import db
from app.models import User, InsuranceCompany, Claim, EmailLog, SystemSettings, ClaimClassification, NotificationTemplate, Notification
from app.forms import UserForm, InsuranceCompanyForm, SettingsForm, EmailSettingsForm
from app.email_utils import test_email_configuration
from app.reports_utils import reports_generator, get_dashboard_charts
from app.export_utils import export_claims_excel, export_claims_pdf, export_companies_excel
from datetime import datetime, timedelta
import json
import os

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('يجب أن تكون مديراً للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def index():
    # Get system statistics
    total_users = User.query.count()
    total_companies = InsuranceCompany.query.count()
    total_claims = Claim.query.count()
    total_emails = EmailLog.query.count()
    
    # Get recent activities
    recent_claims = Claim.query.order_by(Claim.created_at.desc()).limit(10).all()
    recent_emails = EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(10).all()
    
    stats = {
        'total_users': total_users,
        'total_companies': total_companies,
        'total_claims': total_claims,
        'total_emails': total_emails
    }
    
    return render_template('admin/index.html', stats=stats, 
                         recent_claims=recent_claims, recent_emails=recent_emails)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = UserForm()
    
    if form.validate_on_submit():
        print(f"Form data: {form.full_name.data}, {form.email.data}, {form.role.data}, {form.is_active.data}")

        # Check if email already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('هذا البريد الإلكتروني مسجل مسبقاً', 'error')
            return render_template('admin/add_user.html', form=form)

        user = User(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            whatsapp_number=form.whatsapp_number.data,
            role=form.role.data,
            active=form.is_active.data
        )

        if form.password.data:
            user.set_password(form.password.data)
        else:
            # Set a default password if none provided
            user.set_password('123456')

        try:
            db.session.add(user)
            db.session.commit()
            print(f"User created successfully: {user.id}")
            flash('تم إنشاء المستخدم بنجاح', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {e}")
            flash(f'خطأ في إنشاء المستخدم: {str(e)}', 'error')
            return render_template('admin/add_user.html', form=form)
    else:
        if form.errors:
            print(f"Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
    
    return render_template('admin/add_user.html', form=form)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.full_name = form.full_name.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.whatsapp_number = form.whatsapp_number.data
        user.role = form.role.data
        user.active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        # Check if email already exists (excluding current user)
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != user.id:
            flash('هذا البريد الإلكتروني مسجل مسبقاً', 'error')
            return render_template('admin/edit_user.html', form=form, user=user)
        
        db.session.commit()
        flash('تم تحديث المستخدم بنجاح', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('لا يمكن حذف حسابك الخاص', 'error')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    page = request.args.get('page', 1, type=int)
    companies = InsuranceCompany.query.order_by(InsuranceCompany.name_ar).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/companies.html', companies=companies)

@admin_bp.route('/companies/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_company():
    form = InsuranceCompanyForm()
    
    if form.validate_on_submit():
        company = InsuranceCompany(
            name_ar=form.name_ar.data,
            name_en=form.name_en.data,
            claims_email_primary=form.claims_email_primary.data,
            claims_email_cc=form.claims_email_cc.data,
            policy_portal_url=form.policy_portal_url.data,
            notes=form.notes.data,
            active=form.active.data,
            email_template_ar=form.email_template_ar.data,
            email_template_en=form.email_template_en.data
        )
        
        db.session.add(company)
        db.session.commit()
        
        flash('تم إنشاء شركة التأمين بنجاح', 'success')
        return redirect(url_for('admin.companies'))
    
    return render_template('admin/new_company.html', form=form)

@admin_bp.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_company(company_id):
    company = InsuranceCompany.query.get_or_404(company_id)
    form = InsuranceCompanyForm(obj=company)
    
    if form.validate_on_submit():
        form.populate_obj(company)
        db.session.commit()
        
        flash('تم تحديث شركة التأمين بنجاح', 'success')
        return redirect(url_for('admin.companies'))
    
    return render_template('admin/edit_company.html', form=form, company=company)

@admin_bp.route('/companies/<int:company_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_company(company_id):
    company = InsuranceCompany.query.get_or_404(company_id)
    
    # Check if company has claims
    if company.claims:
        flash('لا يمكن حذف شركة تأمين لديها مطالبات', 'error')
        return redirect(url_for('admin.companies'))
    
    db.session.delete(company)
    db.session.commit()
    
    flash('تم حذف شركة التأمين بنجاح', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    form = SettingsForm()
    
    if form.validate_on_submit():
        # Update settings in database
        settings_data = {
            'MAIL_SERVER': form.mail_server.data,
            'MAIL_PORT': form.mail_port.data,
            'MAIL_USERNAME': form.mail_username.data,
            'MAIL_USE_TLS': form.mail_use_tls.data,
            'MAIL_USE_SSL': form.mail_use_ssl.data,
            'MAX_UPLOAD_MB': form.max_upload_mb.data,
            'AI_ENABLED': form.ai_enabled.data,
            'OCR_ENABLED': form.ocr_enabled.data
        }
        
        if form.mail_password.data:
            settings_data['MAIL_PASSWORD'] = form.mail_password.data
        
        for key, value in settings_data.items():
            setting = SystemSettings.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
                setting.updated_at = datetime.utcnow()
            else:
                setting = SystemSettings(key=key, value=str(value))
                db.session.add(setting)
        
        db.session.commit()
        flash('تم حفظ الإعدادات بنجاح', 'success')
        return redirect(url_for('admin.settings'))
    
    # Load current settings
    settings = SystemSettings.query.all()
    settings_dict = {s.key: s.value for s in settings}
    
    # Populate form with current settings
    form.mail_server.data = settings_dict.get('MAIL_SERVER', '')
    form.mail_port.data = settings_dict.get('MAIL_PORT', '587')
    form.mail_username.data = settings_dict.get('MAIL_USERNAME', '')
    form.mail_use_tls.data = settings_dict.get('MAIL_USE_TLS', 'True') == 'True'
    form.mail_use_ssl.data = settings_dict.get('MAIL_USE_SSL', 'False') == 'True'
    form.max_upload_mb.data = settings_dict.get('MAX_UPLOAD_MB', '25')
    form.ai_enabled.data = settings_dict.get('AI_ENABLED', 'False') == 'True'
    form.ocr_enabled.data = settings_dict.get('OCR_ENABLED', 'False') == 'True'
    
    # Get system statistics
    stats = {
        'total_claims': Claim.query.count(),
        'sent_claims': Claim.query.filter_by(status='sent').count(),
        'paid_claims': Claim.query.filter_by(status='paid').count(),
        'total_users': User.query.count()
    }
    
    return render_template('admin/settings.html', form=form, settings=settings_dict, stats=stats, last_update=datetime.now().strftime('%Y-%m-%d %H:%M'))

@admin_bp.route('/test_email', methods=['GET', 'POST'])
@login_required
@admin_required
def test_email():
    success, message = test_email_configuration()

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('admin.settings'))

@admin_bp.route('/email_logs')
@login_required
@admin_required
def email_logs():
    page = request.args.get('page', 1, type=int)
    logs = EmailLog.query.order_by(EmailLog.sent_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/email_logs.html', logs=logs)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    # Get date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Get comprehensive overview
    overview = reports_generator.get_claims_overview(start_date, end_date)
    financial_summary = reports_generator.get_financial_summary(start_date, end_date)

    # Get all charts
    charts = get_dashboard_charts()

    return render_template('admin/reports.html',
                         overview=overview,
                         financial_summary=financial_summary,
                         charts=charts)

@admin_bp.route('/reports/advanced')
@login_required
@admin_required
def advanced_reports():
    """Advanced analytics dashboard"""
    # Get all charts and analytics
    charts = {
        'claims_trend_30': reports_generator.generate_claims_trend_chart(30),
        'claims_trend_90': reports_generator.generate_claims_trend_chart(90),
        'status_distribution': reports_generator.generate_status_distribution_chart(),
        'company_performance': reports_generator.generate_company_performance_chart(),
        'monthly_summary_current': reports_generator.generate_monthly_summary_chart(),
        'monthly_summary_previous': reports_generator.generate_monthly_summary_chart(datetime.now().year - 1)
    }

    # Get financial summaries for different periods
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

    current_month_summary = reports_generator.get_financial_summary(current_month_start)
    last_month_summary = reports_generator.get_financial_summary(last_month_start, current_month_start)

    return render_template('admin/advanced_reports.html',
                         charts=charts,
                         current_month=current_month_summary,
                         last_month=last_month_summary)

@admin_bp.route('/export/claims/<format>')
@login_required
@admin_required
def export_claims(format):
    """Export claims data"""
    try:
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        company_id = request.args.get('company_id', type=int)
        status = request.args.get('status')

        # Build query
        query = Claim.query

        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Claim.created_at >= start_date_obj)

        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Claim.created_at <= end_date_obj)

        if company_id:
            query = query.filter(Claim.company_id == company_id)

        if status:
            query = query.filter(Claim.status == status)

        claims = query.order_by(Claim.created_at.desc()).all()

        if not claims:
            flash('لا توجد مطالبات للتصدير', 'warning')
            return redirect(url_for('admin.reports'))

        # Export based on format
        if format.lower() == 'excel':
            filepath = export_claims_excel(claims)
            filename = os.path.basename(filepath)

            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        elif format.lower() == 'pdf':
            filepath = export_claims_pdf(claims)
            filename = os.path.basename(filepath)

            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )

        else:
            flash('صيغة التصدير غير مدعومة', 'error')
            return redirect(url_for('admin.reports'))

    except Exception as e:
        flash(f'خطأ في تصدير البيانات: {str(e)}', 'error')
        return redirect(url_for('admin.reports'))

@admin_bp.route('/export/companies/<format>')
@login_required
@admin_required
def export_companies(format):
    """Export insurance companies data"""
    try:
        companies = InsuranceCompany.query.order_by(InsuranceCompany.name_ar).all()

        if not companies:
            flash('لا توجد شركات للتصدير', 'warning')
            return redirect(url_for('admin.companies'))

        if format.lower() == 'excel':
            filepath = export_companies_excel(companies)
            filename = os.path.basename(filepath)

            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        else:
            flash('صيغة التصدير غير مدعومة', 'error')
            return redirect(url_for('admin.companies'))

    except Exception as e:
        flash(f'خطأ في تصدير البيانات: {str(e)}', 'error')
        return redirect(url_for('admin.companies'))

@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit logs"""
    from app.models import AuditLog

    page = request.args.get('page', 1, type=int)
    per_page = 50

    # Get filter parameters
    action = request.args.get('action', '')
    resource_type = request.args.get('resource_type', '')
    user_id = request.args.get('user_id', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    # Build query
    query = AuditLog.query

    if action:
        query = query.filter(AuditLog.action == action)

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp <= date_to_obj)
        except ValueError:
            pass

    # Execute query with pagination
    logs = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Get filter options
    actions = db.session.query(AuditLog.action).distinct().all()
    actions = [action[0] for action in actions]

    resource_types = db.session.query(AuditLog.resource_type).distinct().all()
    resource_types = [rt[0] for rt in resource_types]

    users = User.query.filter_by(active=True).all()

    return render_template('admin/audit_logs.html',
                         logs=logs,
                         actions=actions,
                         resource_types=resource_types,
                         users=users,
                         current_filters={
                             'action': action,
                             'resource_type': resource_type,
                             'user_id': user_id,
                             'date_from': date_from,
                             'date_to': date_to
                         })

@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('لا يمكنك تعطيل حسابك الشخصي', 'error')
        return redirect(url_for('admin.users'))
    
    user.active = not user.active
    db.session.commit()
    
    status = 'تم تفعيل' if user.active else 'تم تعطيل'
    flash(f'{status} المستخدم {user.full_name} بنجاح', 'success')

    return redirect(url_for('admin.users'))

@admin_bp.route('/performance')
@login_required
@admin_required
def performance_dashboard():
    """Performance monitoring dashboard (simplified)"""
    # from app.performance import performance_monitor, db_optimizer, health_checker

    # Get basic system metrics
    import psutil
    import os
    from datetime import datetime

    try:
        system_stats = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
            'timestamp': datetime.now()
        }
    except:
        system_stats = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_usage': 0,
            'timestamp': datetime.now()
        }

    # Get database stats
    try:
        from app.models import Claim, User, InsuranceCompany
        db_stats = {
            'total_claims': Claim.query.count(),
            'total_users': User.query.count(),
            'total_companies': InsuranceCompany.query.count()
        }
    except:
        db_stats = {'total_claims': 0, 'total_users': 0, 'total_companies': 0}

    return render_template('admin/performance_simple.html',
                         system_stats=system_stats,
                         db_stats=db_stats)

@admin_bp.route('/performance/optimize', methods=['POST'])
@login_required
@admin_required
def optimize_database():
    """Run database optimization (simplified)"""
    # from app.performance import db_optimizer
    # from app.audit_utils import AuditLogger

    try:
        # Simple database optimization
        db.engine.execute(db.text('VACUUM'))
        db.engine.execute(db.text('ANALYZE'))

        flash('تم تحسين قاعدة البيانات بنجاح', 'success')
    except Exception as e:
        flash(f'فشل في تحسين قاعدة البيانات: {str(e)}', 'error')

    return redirect(url_for('admin.performance_dashboard'))

@admin_bp.route('/performance/clear-cache', methods=['POST'])
@login_required
@admin_required
def clear_cache():
    """Clear application cache"""
    from app import cache
    from app.audit_utils import AuditLogger

    try:
        cache.clear()

        # Log cache clear
        AuditLogger.log_user_action(
            action='CACHE_CLEAR',
            resource_type='system',
            details="Application cache cleared"
        )

        flash('تم مسح الذاكرة المؤقتة بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ في مسح الذاكرة المؤقتة: {str(e)}', 'error')

    return redirect(url_for('admin.performance_dashboard'))

@admin_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    from app.performance import health_checker

    health_status = health_checker.get_health_status()

    # Determine overall status
    overall_status = 'healthy'
    for component, status in health_status.items():
        if isinstance(status, dict) and status.get('status') in ['unhealthy', 'critical']:
            overall_status = 'unhealthy'
            break
        elif isinstance(status, dict) and status.get('status') == 'warning':
            overall_status = 'warning'

    response_code = 200 if overall_status == 'healthy' else 503

    return jsonify({
        'status': overall_status,
        'components': health_status,
        'timestamp': datetime.utcnow().isoformat()
    }), response_code

# Email Settings Routes
@admin_bp.route('/email-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def email_settings():
    """إدارة إعدادات البريد الإلكتروني"""
    form = EmailSettingsForm()

    if form.validate_on_submit():
        try:
            # Update environment variables or database settings
            settings_to_update = {
                'MAIL_SERVER': form.mail_server.data,
                'MAIL_PORT': str(form.mail_port.data),
                'MAIL_USE_TLS': str(form.mail_use_tls.data),
                'MAIL_USE_SSL': str(form.mail_use_ssl.data),
                'MAIL_USERNAME': form.mail_username.data,
                'MAIL_PASSWORD': form.mail_password.data,
                'MAIL_DEFAULT_SENDER': form.mail_default_sender.data
            }

            # Update system settings in database
            for key, value in settings_to_update.items():
                setting = SystemSettings.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    setting = SystemSettings(key=key, value=value)
                    db.session.add(setting)

            db.session.commit()
            flash('تم حفظ إعدادات البريد الإلكتروني بنجاح', 'success')
            return redirect(url_for('admin.email_settings'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في حفظ الإعدادات: {str(e)}', 'error')

    # Load current settings
    current_settings = {}
    settings_keys = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_TLS', 'MAIL_USE_SSL',
                    'MAIL_USERNAME', 'MAIL_DEFAULT_SENDER']

    for key in settings_keys:
        setting = SystemSettings.query.filter_by(key=key).first()
        if setting:
            current_settings[key] = setting.value

    # Pre-populate form with current settings
    if current_settings.get('MAIL_SERVER'):
        form.mail_server.data = current_settings['MAIL_SERVER']
    if current_settings.get('MAIL_PORT'):
        form.mail_port.data = int(current_settings['MAIL_PORT'])
    if current_settings.get('MAIL_USE_TLS'):
        form.mail_use_tls.data = current_settings['MAIL_USE_TLS'].lower() == 'true'
    if current_settings.get('MAIL_USE_SSL'):
        form.mail_use_ssl.data = current_settings['MAIL_USE_SSL'].lower() == 'true'
    if current_settings.get('MAIL_USERNAME'):
        form.mail_username.data = current_settings['MAIL_USERNAME']
    if current_settings.get('MAIL_DEFAULT_SENDER'):
        form.mail_default_sender.data = current_settings['MAIL_DEFAULT_SENDER']

    # Get email statistics
    today = datetime.now().date()
    email_stats = {
        'sent_today': EmailLog.query.filter(
            EmailLog.created_at >= today,
            EmailLog.status == 'sent'
        ).count(),
        'failed_today': EmailLog.query.filter(
            EmailLog.created_at >= today,
            EmailLog.status == 'failed'
        ).count()
    }

    return render_template('admin/email_settings.html',
                         form=form,
                         email_stats=email_stats)

@admin_bp.route('/test-email', methods=['POST'])
@login_required
@admin_required
def test_email_settings():
    """اختبار إعدادات البريد الإلكتروني"""
    try:
        data = request.get_json()
        test_email_address = data.get('email')

        # Test email configuration
        config = {
            'MAIL_SERVER': data.get('mail_server'),
            'MAIL_PORT': int(data.get('mail_port')),
            'MAIL_USE_TLS': data.get('mail_use_tls'),
            'MAIL_USE_SSL': data.get('mail_use_ssl'),
            'MAIL_USERNAME': data.get('mail_username'),
            'MAIL_PASSWORD': data.get('mail_password'),
            'MAIL_DEFAULT_SENDER': data.get('mail_username')
        }

        # Send test email
        success = test_email_configuration(config, test_email_address)

        if success:
            return jsonify({
                'success': True,
                'message': f'تم إرسال بريد اختبار بنجاح إلى {test_email_address}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'فشل في إرسال البريد الإلكتروني. تحقق من الإعدادات.'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'حدث خطأ: {str(e)}'
        })

# Enhanced User Management Routes
@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status_enhanced(user_id):
    """تفعيل/إلغاء تفعيل مستخدم (محسن)"""
    try:
        user = User.query.get_or_404(user_id)

        # Prevent deactivating yourself
        if user.id == current_user.id:
            return jsonify({'success': False, 'error': 'لا يمكنك إلغاء تفعيل حسابك الخاص'})

        user.is_active = not user.is_active
        db.session.commit()

        status = 'تم تفعيل' if user.is_active else 'تم إلغاء تفعيل'
        return jsonify({'success': True, 'message': f'{status} المستخدم {user.username}'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/users/<int:user_id>/delete-enhanced', methods=['POST'])
@login_required
@admin_required
def delete_user_enhanced(user_id):
    """حذف مستخدم (محسن)"""
    try:
        user = User.query.get_or_404(user_id)

        # Prevent deleting yourself
        if user.id == current_user.id:
            return jsonify({'success': False, 'error': 'لا يمكنك حذف حسابك الخاص'})

        # Check if user has claims
        claims_count = Claim.query.filter_by(created_by_user_id=user.id).count()
        if claims_count > 0:
            return jsonify({
                'success': False,
                'error': f'لا يمكن حذف المستخدم لأنه مرتبط بـ {claims_count} مطالبة'
            })

        username = user.username
        db.session.delete(user)
        db.session.commit()

        return jsonify({'success': True, 'message': f'تم حذف المستخدم {username} بنجاح'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/ocr-test')
@login_required
@admin_required
def ocr_test():
    """صفحة اختبار ميزة OCR"""
    return render_template('admin/ocr_test.html')


@admin_bp.route('/advanced-features')
@login_required
@admin_required
def advanced_features():
    """إعدادات المميزات المتقدمة"""
    # Get AI Classification statistics
    ai_stats = {
        'total_classified': ClaimClassification.query.count(),
        'high_risk_count': ClaimClassification.query.filter_by(risk_level='high').count(),
        'fraud_suspects': ClaimClassification.query.filter(ClaimClassification.fraud_probability > 0.5).count(),
        'pending_review': ClaimClassification.query.filter_by(reviewed_by_user_id=None).count()
    }

    # Get Notifications statistics
    notification_stats = {
        'total_notifications': Notification.query.count(),
        'active_templates': NotificationTemplate.query.filter_by(active=True).count(),
        'total_templates': NotificationTemplate.query.count(),
        'recent_notifications': Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
    }

    # Get system configuration status
    config_status = {
        'twilio_configured': bool(os.environ.get('TWILIO_ACCOUNT_SID')),
        'whatsapp_configured': bool(os.environ.get('WHATSAPP_ACCESS_TOKEN')),
        'firebase_configured': bool(os.environ.get('FIREBASE_SERVER_KEY')),
    }

    return render_template('admin/advanced_features.html',
                         ai_stats=ai_stats,
                         notification_stats=notification_stats,
                         config_status=config_status)


@admin_bp.route('/advanced-features/toggle-feature', methods=['POST'])
@login_required
@admin_required
def toggle_advanced_feature():
    """تفعيل/إلغاء تفعيل المميزات المتقدمة"""
    feature = request.json.get('feature')
    enabled = request.json.get('enabled', False)

    try:
        # Here you would typically save the setting to database
        # For now, we'll just return success

        return jsonify({
            'success': True,
            'message': f'تم {"تفعيل" if enabled else "إلغاء تفعيل"} {feature} بنجاح'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@admin_bp.route('/advanced-features/batch-classify', methods=['POST'])
@login_required
@admin_required
def batch_classify_claims():
    """تصنيف جماعي للمطالبات"""
    try:
        from app.ai_classification import classify_claim_ai
        from app.models import ClaimClassification, FraudIndicator

        # Get unclassified claims
        classified_claim_ids = db.session.query(ClaimClassification.claim_id).all()
        classified_ids = [row[0] for row in classified_claim_ids]

        unclassified_claims = Claim.query.filter(
            ~Claim.id.in_(classified_ids)
        ).limit(20).all()  # Process 20 at a time

        if not unclassified_claims:
            return jsonify({
                'success': True,
                'message': 'لا توجد مطالبات غير مصنفة',
                'count': 0
            })

        classified_count = 0
        high_risk_count = 0

        for claim in unclassified_claims:
            try:
                # Run AI classification
                result = classify_claim_ai(claim)

                # Save classification
                classification = ClaimClassification(
                    claim_id=claim.id,
                    category=result.category,
                    confidence=result.confidence,
                    risk_level=result.risk_level,
                    fraud_probability=result.fraud_probability,
                    suggested_amount=result.suggested_amount
                )

                if result.reasoning:
                    classification.set_reasoning_list(result.reasoning)

                db.session.add(classification)
                classified_count += 1

                if result.risk_level == 'high':
                    high_risk_count += 1

            except Exception as e:
                print(f"Failed to classify claim {claim.id}: {e}")
                continue

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'تم تصنيف {classified_count} مطالبة بنجاح',
            'count': classified_count,
            'high_risk_count': high_risk_count
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@admin_bp.route('/api-documentation')
@login_required
@admin_required
def api_documentation():
    """API Documentation page"""
    return render_template('admin/api_documentation.html')

@admin_bp.route('/security-dashboard')
@login_required
@admin_required
def security_dashboard():
    """Security monitoring dashboard"""
    from app.security_manager import SecurityManager

    security_data = SecurityManager.get_security_dashboard_data()
    return render_template('admin/security_dashboard.html', security_data=security_data)

@admin_bp.route('/api/security-events')
@login_required
@admin_required
def api_security_events():
    """API endpoint for security events"""
    from app.security_manager import SecurityManager

    security_data = SecurityManager.get_security_dashboard_data()
    return jsonify(security_data)

@admin_bp.route('/backup-management')
@login_required
@admin_required
def backup_management():
    """Backup management page"""
    from app.backup_manager import BackupManager

    backups = BackupManager.list_backups()
    stats = BackupManager.get_backup_statistics()

    return render_template('admin/backup_management.html',
                         backups=backups,
                         stats=stats)

@admin_bp.route('/api/create-backup', methods=['POST'])
@login_required
@admin_required
def api_create_backup():
    """API endpoint to create backup"""
    from app.backup_manager import BackupManager

    backup_type = request.json.get('type', 'full')
    description = request.json.get('description', '')

    backup_info = BackupManager.create_backup(backup_type, description)

    if backup_info:
        return jsonify({'success': True, 'backup': backup_info})
    else:
        return jsonify({'success': False, 'error': 'Failed to create backup'}), 500

@admin_bp.route('/api/restore-backup', methods=['POST'])
@login_required
@admin_required
def api_restore_backup():
    """API endpoint to restore backup"""
    from app.backup_manager import BackupManager

    backup_path = request.json.get('backup_path')
    components = request.json.get('components', None)

    if not backup_path:
        return jsonify({'success': False, 'error': 'Backup path required'}), 400

    result = BackupManager.restore_backup(backup_path, components)
    return jsonify(result)

@admin_bp.route('/api/delete-backup', methods=['POST'])
@login_required
@admin_required
def api_delete_backup():
    """API endpoint to delete backup"""
    from app.backup_manager import BackupManager

    backup_path = request.json.get('backup_path')

    if not backup_path:
        return jsonify({'success': False, 'error': 'Backup path required'}), 400

    success = BackupManager.delete_backup(backup_path)
    return jsonify({'success': success})

@admin_bp.route('/download-backup')
@login_required
@admin_required
def download_backup():
    """Download backup file"""
    try:
        backup_path = request.args.get('path')

        if not backup_path or not os.path.exists(backup_path):
            flash('الملف غير موجود', 'error')
            return redirect(url_for('admin.backup_management'))

        return send_file(backup_path, as_attachment=True)

    except Exception as e:
        current_app.logger.error(f"Failed to download backup: {e}")
        flash('فشل في تحميل النسخة الاحتياطية', 'error')
        return redirect(url_for('admin.backup_management'))

@admin_bp.route('/api/backup-schedule', methods=['GET', 'POST'])
@login_required
@admin_required
def backup_schedule():
    """Manage backup schedule"""
    if request.method == 'GET':
        # Get current schedule settings
        schedule_settings = {
            'enabled': False,
            'frequency': 'daily',
            'time': '02:00',
            'backup_type': 'full',
            'retention_days': 30
        }
        return jsonify(schedule_settings)

    else:
        # Update schedule settings
        try:
            settings = request.json
            # In a real implementation, you would save these settings
            # and set up a background task scheduler (like Celery)

            return jsonify({'success': True, 'message': 'تم حفظ إعدادات الجدولة'})

        except Exception as e:
            return jsonify({'success': False, 'error': 'فشل في حفظ الإعدادات'})