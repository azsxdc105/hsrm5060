#!/usr/bin/env python3
"""
Security utilities and enhancements
"""
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, session, g
from flask_login import current_user
from cryptography.fernet import Fernet
from app import db, cache
from app.models import AuditLog
import logging
import re

logger = logging.getLogger(__name__)

class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self.failed_attempts = {}
        self.blocked_ips = set()
        self.rate_limits = {}
    
    def generate_encryption_key(self):
        """Generate encryption key for sensitive data"""
        return Fernet.generate_key()
    
    def encrypt_sensitive_data(self, data: str, key: bytes = None) -> str:
        """Encrypt sensitive data like national IDs, account numbers"""
        if not key:
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                # Generate and store key (in production, use proper key management)
                key = self.generate_encryption_key()
                current_app.config['ENCRYPTION_KEY'] = key
        
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return encrypted_data.decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str, key: bytes = None) -> str:
        """Decrypt sensitive data"""
        if not key:
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                raise ValueError("Encryption key not found")
        
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${password_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            salt, password_hash = hashed.split('$')
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == password_hash
        except:
            return False
    
    def is_strong_password(self, password: str) -> tuple:
        """Check if password meets security requirements"""
        errors = []
        
        if len(password) < 8:
            errors.append("كلمة المرور يجب أن تكون 8 أحرف على الأقل")
        
        if not re.search(r'[A-Z]', password):
            errors.append("كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل")
        
        if not re.search(r'[a-z]', password):
            errors.append("كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل")
        
        if not re.search(r'\d', password):
            errors.append("كلمة المرور يجب أن تحتوي على رقم واحد على الأقل")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل")
        
        return len(errors) == 0, errors
    
    def record_failed_attempt(self, ip_address: str, user_email: str = None):
        """Record failed login attempt"""
        key = f"failed_attempts_{ip_address}"
        attempts = cache.get(key) or 0
        attempts += 1
        
        # Store for 1 hour
        cache.set(key, attempts, timeout=3600)
        
        # Log the attempt
        AuditLog.log_action(
            user_id=None,
            action='LOGIN_FAILED',
            resource_type='security',
            ip_address=ip_address,
            details=f"Failed login attempt for {user_email or 'unknown'}"
        )
        
        # Block IP after 5 failed attempts
        if attempts >= 5:
            self.block_ip(ip_address, duration=3600)  # Block for 1 hour
    
    def block_ip(self, ip_address: str, duration: int = 3600):
        """Block IP address"""
        cache.set(f"blocked_ip_{ip_address}", True, timeout=duration)
        logger.warning(f"IP address blocked: {ip_address} for {duration} seconds")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        return cache.get(f"blocked_ip_{ip_address}") is not None
    
    def get_failed_attempts(self, ip_address: str) -> int:
        """Get number of failed attempts for IP"""
        return cache.get(f"failed_attempts_{ip_address}") or 0
    
    def clear_failed_attempts(self, ip_address: str):
        """Clear failed attempts for IP"""
        cache.delete(f"failed_attempts_{ip_address}")
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token"""
        stored_token = session.get('csrf_token')
        return stored_token and secrets.compare_digest(stored_token, token)

# Global security manager instance
security_manager = SecurityManager()

def rate_limit(max_requests: int = 100, window: int = 3600, per_ip: bool = True):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get identifier (IP or user)
            if per_ip:
                identifier = request.remote_addr
            else:
                identifier = current_user.id if current_user.is_authenticated else request.remote_addr
            
            # Create cache key
            cache_key = f"rate_limit_{f.__name__}_{identifier}"
            
            # Get current count
            current_count = cache.get(cache_key) or 0
            
            if current_count >= max_requests:
                logger.warning(f"Rate limit exceeded for {identifier} on {f.__name__}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'تم تجاوز الحد المسموح من الطلبات'
                }), 429
            
            # Increment counter
            cache.set(cache_key, current_count + 1, timeout=window)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_ip_whitelist(whitelist: list):
    """Require IP to be in whitelist"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            
            if client_ip not in whitelist:
                logger.warning(f"Access denied for IP: {client_ip}")
                return jsonify({
                    'error': 'Access denied',
                    'message': 'غير مسموح بالوصول من هذا العنوان'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def security_headers(f):
    """Add security headers to response"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add security headers
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https:;"
        
        return response
    
    return decorated_function

def check_ip_security():
    """Check IP-based security before each request"""
    client_ip = request.remote_addr
    
    # Check if IP is blocked
    if security_manager.is_ip_blocked(client_ip):
        logger.warning(f"Blocked IP attempted access: {client_ip}")
        return jsonify({
            'error': 'Access blocked',
            'message': 'تم حظر الوصول من هذا العنوان'
        }), 403
    
    # Check for suspicious patterns
    user_agent = request.headers.get('User-Agent', '')
    if not user_agent or len(user_agent) < 10:
        logger.warning(f"Suspicious request from {client_ip}: No/Short User-Agent")
    
    # Store request info for analysis
    g.client_ip = client_ip
    g.user_agent = user_agent
    g.request_time = time.time()

def log_security_event(event_type: str, details: str, severity: str = 'INFO'):
    """Log security events"""
    AuditLog.log_action(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=f'SECURITY_{event_type}',
        resource_type='security',
        ip_address=getattr(g, 'client_ip', None),
        user_agent=getattr(g, 'user_agent', None),
        details=f"[{severity}] {details}"
    )

def validate_file_upload(file, allowed_extensions: set, max_size: int = 10 * 1024 * 1024):
    """Validate uploaded file for security"""
    errors = []
    
    if not file or not file.filename:
        errors.append("لم يتم اختيار ملف")
        return False, errors
    
    # Check file extension
    if '.' not in file.filename:
        errors.append("امتداد الملف غير صحيح")
    else:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            errors.append(f"امتداد الملف غير مسموح. الامتدادات المسموحة: {', '.join(allowed_extensions)}")
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if size > max_size:
        errors.append(f"حجم الملف كبير جداً. الحد الأقصى: {max_size // (1024*1024)} MB")
    
    # Check for malicious content (basic check)
    if file.filename.lower().endswith(('.exe', '.bat', '.cmd', '.scr', '.pif')):
        errors.append("نوع الملف غير مسموح")
    
    return len(errors) == 0, errors

def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', 'javascript:', 'vbscript:', 'onload=', 'onerror=']
    
    sanitized = input_string
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()

class SecurityAudit:
    """Security audit and monitoring"""
    
    @staticmethod
    def get_security_summary():
        """Get security summary for the last 24 hours"""
        since = datetime.utcnow() - timedelta(hours=24)
        
        # Get security-related audit logs
        security_logs = AuditLog.query.filter(
            AuditLog.timestamp >= since,
            AuditLog.action.like('SECURITY_%')
        ).all()
        
        # Count different types of events
        events = {}
        for log in security_logs:
            event_type = log.action.replace('SECURITY_', '')
            events[event_type] = events.get(event_type, 0) + 1
        
        # Get failed login attempts
        failed_logins = AuditLog.query.filter(
            AuditLog.timestamp >= since,
            AuditLog.action == 'LOGIN_FAILED'
        ).count()
        
        return {
            'period': '24 hours',
            'security_events': events,
            'failed_logins': failed_logins,
            'total_events': len(security_logs),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_suspicious_activities():
        """Get suspicious activities"""
        since = datetime.utcnow() - timedelta(hours=24)
        
        # Multiple failed logins from same IP
        suspicious_ips = db.session.query(
            AuditLog.ip_address,
            db.func.count(AuditLog.id).label('attempts')
        ).filter(
            AuditLog.timestamp >= since,
            AuditLog.action == 'LOGIN_FAILED',
            AuditLog.ip_address.isnot(None)
        ).group_by(AuditLog.ip_address).having(
            db.func.count(AuditLog.id) >= 3
        ).all()
        
        return {
            'suspicious_ips': [
                {'ip': ip, 'failed_attempts': attempts}
                for ip, attempts in suspicious_ips
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
