#!/usr/bin/env python3
"""
Two-Factor Authentication Routes
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.two_factor_auth import TwoFactorAuth
from app.security_manager import SecurityManager
from functools import wraps

two_factor_bp = Blueprint('two_factor', __name__)

def require_2fa_setup(f):
    """Decorator to require 2FA setup for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Check if 2FA is required but not set up
        if current_user.role == 'admin' and not current_user.two_factor_enabled:
            flash('يجب تفعيل المصادقة الثنائية للمدراء', 'warning')
            return redirect(url_for('two_factor.setup'))
        
        return f(*args, **kwargs)
    return decorated_function

@two_factor_bp.route('/setup')
@login_required
def setup():
    """2FA setup page"""
    # Generate new secret if not exists
    if not current_user.two_factor_secret:
        secret = TwoFactorAuth.generate_secret()
        # Store temporarily in session
        session['temp_2fa_secret'] = secret
    else:
        secret = current_user.two_factor_secret
    
    # Generate QR code
    qr_code = TwoFactorAuth.generate_qr_code(current_user, secret)
    
    return render_template('two_factor/setup.html', 
                         secret=secret, 
                         qr_code=qr_code,
                         user=current_user)

@two_factor_bp.route('/verify-setup', methods=['POST'])
@login_required
def verify_setup():
    """Verify 2FA setup"""
    try:
        token = request.form.get('token')
        secret = session.get('temp_2fa_secret') or current_user.two_factor_secret
        
        if not token or not secret:
            return jsonify({'success': False, 'error': 'بيانات غير صحيحة'})
        
        # Verify token
        if TwoFactorAuth.enable_2fa_for_user(current_user.id, secret, token):
            # Clear temporary secret
            session.pop('temp_2fa_secret', None)
            
            SecurityManager.log_security_event(
                'two_factor_setup_completed',
                f'User {current_user.email} completed 2FA setup',
                severity='info',
                user_id=current_user.id
            )
            
            return jsonify({
                'success': True, 
                'message': 'تم تفعيل المصادقة الثنائية بنجاح',
                'backup_codes': current_user.two_factor_backup_codes
            })
        else:
            return jsonify({'success': False, 'error': 'رمز التحقق غير صحيح'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': 'حدث خطأ في النظام'})

@two_factor_bp.route('/disable', methods=['POST'])
@login_required
def disable():
    """Disable 2FA"""
    try:
        password = request.form.get('password')
        
        # Verify password before disabling
        if not current_user.check_password(password):
            return jsonify({'success': False, 'error': 'كلمة المرور غير صحيحة'})
        
        if TwoFactorAuth.disable_2fa_for_user(current_user.id):
            SecurityManager.log_security_event(
                'two_factor_disabled',
                f'User {current_user.email} disabled 2FA',
                severity='medium',
                user_id=current_user.id
            )
            
            return jsonify({'success': True, 'message': 'تم إلغاء تفعيل المصادقة الثنائية'})
        else:
            return jsonify({'success': False, 'error': 'فشل في إلغاء تفعيل المصادقة الثنائية'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': 'حدث خطأ في النظام'})

@two_factor_bp.route('/verify')
def verify():
    """2FA verification page"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if not TwoFactorAuth.require_2fa_verification(current_user):
        return redirect(url_for('main.dashboard'))
    
    return render_template('two_factor/verify.html')

@two_factor_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify 2FA token"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'غير مصرح'})
        
        token = request.form.get('token')
        use_backup = request.form.get('use_backup') == 'true'
        
        if not token:
            return jsonify({'success': False, 'error': 'يرجى إدخال الرمز'})
        
        verified = False
        
        if use_backup:
            # Verify backup code
            verified = TwoFactorAuth.verify_backup_code(current_user.id, token)
            if verified:
                SecurityManager.log_security_event(
                    'backup_code_used',
                    f'User {current_user.email} used backup code',
                    severity='medium',
                    user_id=current_user.id
                )
        else:
            # Verify TOTP token
            verified = TwoFactorAuth.verify_totp(current_user.two_factor_secret, token)
        
        if verified:
            TwoFactorAuth.mark_2fa_verified(current_user.id)
            
            SecurityManager.log_security_event(
                'two_factor_verified',
                f'User {current_user.email} completed 2FA verification',
                severity='info',
                user_id=current_user.id
            )
            
            # Redirect to intended page or dashboard
            next_page = session.get('next_page', url_for('main.dashboard'))
            session.pop('next_page', None)
            
            return jsonify({'success': True, 'redirect': next_page})
        else:
            SecurityManager.log_security_event(
                'two_factor_failed',
                f'Failed 2FA verification for user {current_user.email}',
                severity='high',
                user_id=current_user.id
            )
            
            return jsonify({'success': False, 'error': 'رمز التحقق غير صحيح'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': 'حدث خطأ في النظام'})

@two_factor_bp.route('/backup-codes')
@login_required
def backup_codes():
    """Show backup codes"""
    if not current_user.two_factor_enabled:
        flash('يجب تفعيل المصادقة الثنائية أولاً', 'error')
        return redirect(url_for('two_factor.setup'))
    
    return render_template('two_factor/backup_codes.html', 
                         backup_codes=current_user.two_factor_backup_codes)

@two_factor_bp.route('/regenerate-backup-codes', methods=['POST'])
@login_required
def regenerate_backup_codes():
    """Regenerate backup codes"""
    try:
        password = request.form.get('password')
        
        # Verify password
        if not current_user.check_password(password):
            return jsonify({'success': False, 'error': 'كلمة المرور غير صحيحة'})
        
        # Generate new backup codes
        new_codes = TwoFactorAuth.generate_backup_codes()
        current_user.two_factor_backup_codes = new_codes
        
        from app import db
        db.session.commit()
        
        SecurityManager.log_security_event(
            'backup_codes_regenerated',
            f'User {current_user.email} regenerated backup codes',
            severity='medium',
            user_id=current_user.id
        )
        
        return jsonify({'success': True, 'backup_codes': new_codes})
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'حدث خطأ في النظام'})

@two_factor_bp.route('/status')
@login_required
def status():
    """Get 2FA status"""
    status = TwoFactorAuth.get_2fa_status(current_user.id)
    return jsonify(status)

@two_factor_bp.route('/settings')
@login_required
def settings():
    """2FA settings page"""
    status = TwoFactorAuth.get_2fa_status(current_user.id)
    return render_template('two_factor/settings.html', status=status)
