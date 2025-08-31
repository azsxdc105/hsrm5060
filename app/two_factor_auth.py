#!/usr/bin/env python3
"""
Two-Factor Authentication (2FA) System
Supports TOTP (Time-based One-Time Password) and SMS-based 2FA
"""
import pyotp
import qrcode
import io
import base64
from flask import current_app
from app import db
from app.models import User
import secrets
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class TwoFactorAuth:
    """Two-Factor Authentication manager"""
    
    @staticmethod
    def generate_secret():
        """Generate a new secret key for TOTP"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user, secret):
        """Generate QR code for TOTP setup"""
        try:
            # Create TOTP URI
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name="نظام إدارة مطالبات التأمين"
            )
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for display
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            current_app.logger.error(f"Failed to generate QR code: {e}")
            return None
    
    @staticmethod
    def verify_totp(secret, token):
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 1 window tolerance
        except Exception as e:
            current_app.logger.error(f"Failed to verify TOTP: {e}")
            return False
    
    @staticmethod
    def enable_2fa_for_user(user_id, secret, verification_token):
        """Enable 2FA for a user after verification"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Verify the token first
            if not TwoFactorAuth.verify_totp(secret, verification_token):
                return False
            
            # Enable 2FA
            user.two_factor_secret = secret
            user.two_factor_enabled = True
            user.two_factor_backup_codes = TwoFactorAuth.generate_backup_codes()
            
            db.session.commit()
            
            # Log security event
            from app.security_manager import SecurityManager
            SecurityManager.log_security_event(
                'two_factor_enabled',
                f'2FA enabled for user {user.email}',
                severity='info',
                user_id=user.id
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to enable 2FA: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def disable_2fa_for_user(user_id):
        """Disable 2FA for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            user.two_factor_secret = None
            user.two_factor_enabled = False
            user.two_factor_backup_codes = None
            
            db.session.commit()
            
            # Log security event
            from app.security_manager import SecurityManager
            SecurityManager.log_security_event(
                'two_factor_disabled',
                f'2FA disabled for user {user.email}',
                severity='medium',
                user_id=user.id
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to disable 2FA: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def generate_backup_codes(count=10):
        """Generate backup codes for 2FA recovery"""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        return codes
    
    @staticmethod
    def verify_backup_code(user_id, backup_code):
        """Verify and consume a backup code"""
        try:
            user = User.query.get(user_id)
            if not user or not user.two_factor_backup_codes:
                return False
            
            backup_codes = user.two_factor_backup_codes
            if backup_code in backup_codes:
                # Remove the used backup code
                backup_codes.remove(backup_code)
                user.two_factor_backup_codes = backup_codes
                db.session.commit()
                
                # Log security event
                from app.security_manager import SecurityManager
                SecurityManager.log_security_event(
                    'backup_code_used',
                    f'Backup code used for user {user.email}',
                    severity='medium',
                    user_id=user.id
                )
                
                return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Failed to verify backup code: {e}")
            return False
    
    @staticmethod
    def send_sms_code(phone_number, code):
        """Send SMS verification code (placeholder - integrate with SMS service)"""
        try:
            # This is a placeholder implementation
            # In production, integrate with SMS services like Twilio, AWS SNS, etc.
            
            current_app.logger.info(f"SMS code {code} would be sent to {phone_number}")
            
            # For development, you might want to log the code or send via email
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send SMS code: {e}")
            return False
    
    @staticmethod
    def generate_sms_code():
        """Generate a 6-digit SMS verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @staticmethod
    def store_sms_code(user_id, code, expiry_minutes=5):
        """Store SMS code temporarily (in production, use Redis or similar)"""
        try:
            # For simplicity, we'll store in user session or database
            # In production, use Redis or similar for temporary storage
            
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Store code and expiry time
            expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
            
            # You might want to add these fields to User model or use a separate table
            # For now, we'll use a simple approach
            user.temp_sms_code = code
            user.temp_sms_code_expiry = expiry_time
            
            db.session.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to store SMS code: {e}")
            return False
    
    @staticmethod
    def verify_sms_code(user_id, code):
        """Verify SMS code"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Check if code matches and hasn't expired
            if (hasattr(user, 'temp_sms_code') and 
                hasattr(user, 'temp_sms_code_expiry') and
                user.temp_sms_code == code and
                user.temp_sms_code_expiry > datetime.now()):
                
                # Clear the temporary code
                user.temp_sms_code = None
                user.temp_sms_code_expiry = None
                db.session.commit()
                
                return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Failed to verify SMS code: {e}")
            return False
    
    @staticmethod
    def get_2fa_status(user_id):
        """Get 2FA status for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            return {
                'enabled': user.two_factor_enabled or False,
                'method': 'totp' if user.two_factor_secret else None,
                'backup_codes_count': len(user.two_factor_backup_codes) if user.two_factor_backup_codes else 0,
                'setup_complete': bool(user.two_factor_secret and user.two_factor_enabled)
            }
            
        except Exception as e:
            current_app.logger.error(f"Failed to get 2FA status: {e}")
            return None
    
    @staticmethod
    def require_2fa_verification(user):
        """Check if user needs 2FA verification"""
        if not user or not user.two_factor_enabled:
            return False
        
        # Check if user has already verified 2FA in this session
        from flask import session
        session_key = f"2fa_verified_{user.id}"
        
        if session.get(session_key):
            # Check if verification is still valid (e.g., 1 hour)
            verification_time = session.get(f"{session_key}_time")
            if verification_time:
                verification_datetime = datetime.fromisoformat(verification_time)
                if datetime.now() - verification_datetime < timedelta(hours=1):
                    return False
        
        return True
    
    @staticmethod
    def mark_2fa_verified(user_id):
        """Mark 2FA as verified for this session"""
        from flask import session
        session_key = f"2fa_verified_{user_id}"
        session[session_key] = True
        session[f"{session_key}_time"] = datetime.now().isoformat()
    
    @staticmethod
    def clear_2fa_verification(user_id):
        """Clear 2FA verification from session"""
        from flask import session
        session_key = f"2fa_verified_{user_id}"
        session.pop(session_key, None)
        session.pop(f"{session_key}_time", None)
