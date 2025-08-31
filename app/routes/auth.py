from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models import User
from app.forms import LoginForm
from app.audit_utils import log_login, log_logout, log_failed_login_attempt
from app.notification_manager import NotificationManager

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.active:
            login_user(user, remember=form.remember_me.data)

            # Log successful login
            log_login(user.id, success=True)

            # Send login notification
            try:
                NotificationManager.notify_user_login(user)
            except Exception as e:
                print(f"Failed to send login notification: {e}")

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            # Log failed login attempt
            log_failed_login_attempt(form.email.data)
            flash('بيانات تسجيل الدخول غير صحيحة', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    # Log logout before logging out
    log_logout(current_user.id)

    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Validate current password
    if not current_user.check_password(current_password):
        flash('كلمة المرور الحالية غير صحيحة', 'error')
        return redirect(url_for('profile'))

    # Validate new password
    if new_password != confirm_password:
        flash('كلمات المرور الجديدة غير متطابقة', 'error')
        return redirect(url_for('profile'))

    if len(new_password) < 6:
        flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error')
        return redirect(url_for('profile'))

    # Update password
    current_user.set_password(new_password)
    db.session.commit()

    flash('تم تغيير كلمة المرور بنجاح', 'success')
    return redirect(url_for('profile'))

@auth_bp.route('/set_language/<language>')
def set_language(language):
    session['language'] = language
    return redirect(request.referrer or url_for('main.dashboard'))