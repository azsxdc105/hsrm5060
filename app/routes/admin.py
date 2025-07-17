from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, InsuranceCompany, Claim, EmailLog, SystemSettings
from app.forms import UserForm, InsuranceCompanyForm, SettingsForm
from app.email_utils import test_email_configuration
from datetime import datetime
import json

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
        user = User(
            full_name=form.full_name.data,
            email=form.email.data,
            role=form.role.data,
            active=form.active.data
        )
        
        if form.password.data:
            user.set_password(form.password.data)
        
        # Check if email already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('هذا البريد الإلكتروني مسجل مسبقاً', 'error')
            return render_template('admin/add_user.html', form=form)
        
        db.session.add(user)
        db.session.commit()
        
        flash('تم إنشاء المستخدم بنجاح', 'success')
        return redirect(url_for('admin.users'))
    
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
        user.role = form.role.data
        user.active = form.active.data
        
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

@admin_bp.route('/test_email', methods=['POST'])
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
    # Get various statistics for reports
    from sqlalchemy import func
    
    # Claims by status
    status_stats = db.session.query(
        Claim.status,
        func.count(Claim.id).label('count')
    ).group_by(Claim.status).all()
    
    # Claims by company
    company_stats = db.session.query(
        InsuranceCompany.name_ar,
        func.count(Claim.id).label('count'),
        func.sum(Claim.claim_amount).label('total_amount')
    ).outerjoin(Claim).group_by(InsuranceCompany.id, InsuranceCompany.name_ar).all()
    
    # Monthly claims
    monthly_stats = db.session.query(
        func.date_trunc('month', Claim.created_at).label('month'),
        func.count(Claim.id).label('count'),
        func.sum(Claim.claim_amount).label('total_amount')
    ).group_by(func.date_trunc('month', Claim.created_at)).all()
    
    return render_template('admin/reports.html',
                         status_stats=status_stats,
                         company_stats=company_stats,
                         monthly_stats=monthly_stats)

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