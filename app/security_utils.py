"""
Security utilities for the application
"""
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from flask import request, current_app, session
from flask_login import current_user
from functools import wraps
import logging

# Configure security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

class SecurityManager:
    """Security management utilities"""
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 with SHA-256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return f"{salt}:{password_hash.hex()}"
    
    @staticmethod
    def verify_password(password, hashed_password):
        """Verify password against hash"""
        try:
            salt, password_hash = hashed_password.split(':')
            return SecurityManager.hash_password(password, salt) == hashed_password
        except ValueError:
            return False
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append('كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        
        if not re.search(r'[A-Z]', password):
            errors.append('كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل')
        
        if not re.search(r'[a-z]', password):
            errors.append('كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل')
        
        if not re.search(r'\d', password):
            errors.append('كلمة المرور يجب أن تحتوي على رقم واحد على الأقل')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل')
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_input(input_string):
        """Sanitize user input to prevent XSS"""
        if not input_string:
            return input_string
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', 'javascript:', 'vbscript:', 'onload=', 'onerror=']
        
        for char in dangerous_chars:
            input_string = input_string.replace(char, '')
        
        return input_string.strip()
    
    @staticmethod
    def validate_file_upload(file):
        """Validate uploaded file for security"""
        if not file or not file.filename:
            return False, 'لم يتم اختيار ملف'
        
        # Check file extension
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', 
                                                   {'pdf', 'jpg', 'jpeg', 'png', 'docx', 'doc', 'txt'})
        
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return False, f'نوع الملف غير مسموح. الأنواع المسموحة: {", ".join(allowed_extensions)}'
        
        # Check file size (default 25MB)
        max_size = current_app.config.get('MAX_UPLOAD_MB', 25) * 1024 * 1024
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            return False, f'حجم الملف كبير جداً. الحد الأقصى: {max_size // (1024*1024)} ميجابايت'
        
        return True, 'الملف صالح'

class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self):
        self.attempts = {}
    
    def is_rate_limited(self, key, max_attempts=5, window_minutes=15):
        """Check if key is rate limited"""
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old attempts
        if key in self.attempts:
            self.attempts[key] = [
                attempt for attempt in self.attempts[key] 
                if attempt > window_start
            ]
        
        # Check current attempts
        current_attempts = len(self.attempts.get(key, []))
        
        if current_attempts >= max_attempts:
            return True, f'تم تجاوز الحد الأقصى للمحاولات. حاول مرة أخرى بعد {window_minutes} دقيقة'
        
        return False, None
    
    def record_attempt(self, key):
        """Record an attempt"""
        if key not in self.attempts:
            self.attempts[key] = []
        
        self.attempts[key].append(datetime.now())

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_attempts=5, window_minutes=15):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as key
            key = request.remote_addr
            
            is_limited, message = rate_limiter.is_rate_limited(
                key, max_attempts, window_minutes
            )
            
            if is_limited:
                security_logger.warning(f'Rate limit exceeded for IP: {key}')
                return {'error': message}, 429
            
            # Record this attempt
            rate_limiter.record_attempt(key)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_security_event(event_type, details, severity='INFO'):
    """Log security events"""
    user_info = 'Anonymous'
    if current_user and current_user.is_authenticated:
        user_info = f'{current_user.username} (ID: {current_user.id})'
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'user': user_info,
        'ip_address': request.remote_addr if request else 'Unknown',
        'user_agent': request.headers.get('User-Agent', 'Unknown') if request else 'Unknown',
        'details': details,
        'severity': severity
    }
    
    if severity == 'CRITICAL':
        security_logger.critical(f'SECURITY EVENT: {log_entry}')
    elif severity == 'WARNING':
        security_logger.warning(f'SECURITY EVENT: {log_entry}')
    else:
        security_logger.info(f'SECURITY EVENT: {log_entry}')

def require_fresh_login(f):
    """Decorator to require fresh login for sensitive operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Check if login is fresh (within last 30 minutes)
        last_login = session.get('last_fresh_login')
        if not last_login:
            session['next_url'] = request.url
            return redirect(url_for('auth.confirm_password'))
        
        last_login_time = datetime.fromisoformat(last_login)
        if datetime.now() - last_login_time > timedelta(minutes=30):
            session['next_url'] = request.url
            return redirect(url_for('auth.confirm_password'))
        
        return f(*args, **kwargs)
    return decorated_function

class CSRFProtection:
    """Enhanced CSRF protection"""
    
    @staticmethod
    def generate_csrf_token():
        """Generate CSRF token"""
        if 'csrf_token' not in session:
            session['csrf_token'] = SecurityManager.generate_secure_token()
        return session['csrf_token']
    
    @staticmethod
    def validate_csrf_token(token):
        """Validate CSRF token"""
        return token and session.get('csrf_token') == token

def audit_log(action, resource_type, resource_id=None, details=None):
    """Decorator for audit logging"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = datetime.now()
            
            try:
                result = f(*args, **kwargs)
                
                # Log successful action
                log_security_event(
                    'AUDIT_LOG',
                    {
                        'action': action,
                        'resource_type': resource_type,
                        'resource_id': resource_id,
                        'details': details,
                        'duration_ms': (datetime.now() - start_time).total_seconds() * 1000,
                        'status': 'SUCCESS'
                    }
                )
                
                return result
                
            except Exception as e:
                # Log failed action
                log_security_event(
                    'AUDIT_LOG',
                    {
                        'action': action,
                        'resource_type': resource_type,
                        'resource_id': resource_id,
                        'details': details,
                        'error': str(e),
                        'duration_ms': (datetime.now() - start_time).total_seconds() * 1000,
                        'status': 'FAILED'
                    },
                    'WARNING'
                )
                
                raise
        return decorated_function
    return decorator

def validate_ip_whitelist(allowed_ips=None):
    """Decorator to validate IP whitelist"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if allowed_ips:
                client_ip = request.remote_addr
                if client_ip not in allowed_ips:
                    log_security_event(
                        'IP_BLOCKED',
                        f'Access denied for IP: {client_ip}',
                        'WARNING'
                    )
                    return {'error': 'Access denied'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
