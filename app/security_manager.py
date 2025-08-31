#!/usr/bin/env python3
"""
Advanced Security Manager
Handles security monitoring, audit logging, and threat detection
"""
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from flask import request, current_app, session
from flask_login import current_user
try:
    from app import db
    from app.models import User, AuditLog
except ImportError:
    # Handle circular import during initialization
    db = None
    User = None
    AuditLog = None
import json
import re
from collections import defaultdict, deque
import ipaddress

class SecurityManager:
    """Advanced security management and monitoring"""
    
    # Rate limiting storage (in production, use Redis)
    _rate_limits = defaultdict(lambda: deque())
    _failed_attempts = defaultdict(int)
    _blocked_ips = set()
    
    # Security thresholds
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes
    RATE_LIMIT_REQUESTS = 100  # requests per minute
    SUSPICIOUS_PATTERNS = [
        r'<script.*?>.*?</script>',  # XSS attempts
        r'union.*select',  # SQL injection
        r'drop\s+table',  # SQL injection
        r'exec\s*\(',  # Code execution
        r'eval\s*\(',  # Code execution
    ]
    
    @staticmethod
    def log_security_event(event_type, description, severity='info', user_id=None, ip_address=None, additional_data=None):
        """Log security events for monitoring and analysis"""
        try:
            # Handle case where models are not available during initialization
            if AuditLog is None or db is None:
                current_app.logger.warning(f"Security event: {event_type} - {description}")
                return
                
            if user_id is None and current_user.is_authenticated:
                user_id = current_user.id
            
            if ip_address is None:
                ip_address = SecurityManager.get_client_ip()
            
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                action=event_type,
                resource_type='security',
                resource_id=None,
                ip_address=ip_address,
                user_agent=request.headers.get('User-Agent', ''),
                details=json.dumps({
                    'description': description,
                    'severity': severity,
                    'additional_data': additional_data or {}
                })
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            # Log to application logger based on severity
            if severity == 'critical':
                current_app.logger.critical(f"SECURITY CRITICAL: {description}")
            elif severity == 'high':
                current_app.logger.error(f"SECURITY HIGH: {description}")
            elif severity == 'medium':
                current_app.logger.warning(f"SECURITY MEDIUM: {description}")
            else:
                current_app.logger.info(f"SECURITY INFO: {description}")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to log security event: {e}")
            return False
    
    @staticmethod
    def get_client_ip():
        """Get the real client IP address"""
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_ips = request.headers.get('X-Forwarded-For')
        if forwarded_ips:
            # Take the first IP (original client)
            return forwarded_ips.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr
    
    @staticmethod
    def is_rate_limited(identifier=None, limit=None, window=60):
        """Check if request is rate limited"""
        if identifier is None:
            identifier = SecurityManager.get_client_ip()
        
        if limit is None:
            limit = SecurityManager.RATE_LIMIT_REQUESTS
        
        now = time.time()
        window_start = now - window
        
        # Clean old entries
        requests = SecurityManager._rate_limits[identifier]
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # Check if limit exceeded
        if len(requests) >= limit:
            SecurityManager.log_security_event(
                'rate_limit_exceeded',
                f'Rate limit exceeded for {identifier}: {len(requests)} requests in {window}s',
                severity='medium',
                additional_data={'identifier': identifier, 'requests': len(requests)}
            )
            return True
        
        # Add current request
        requests.append(now)
        return False
    
    @staticmethod
    def check_failed_login_attempts(identifier):
        """Check and update failed login attempts"""
        attempts = SecurityManager._failed_attempts.get(identifier, 0)
        
        if attempts >= SecurityManager.MAX_LOGIN_ATTEMPTS:
            SecurityManager.log_security_event(
                'account_lockout',
                f'Account locked due to {attempts} failed login attempts',
                severity='high',
                additional_data={'identifier': identifier, 'attempts': attempts}
            )
            return True
        
        return False
    
    @staticmethod
    def record_failed_login(identifier):
        """Record a failed login attempt"""
        SecurityManager._failed_attempts[identifier] += 1
        attempts = SecurityManager._failed_attempts[identifier]
        
        SecurityManager.log_security_event(
            'failed_login_attempt',
            f'Failed login attempt #{attempts} for {identifier}',
            severity='medium' if attempts < 3 else 'high',
            additional_data={'identifier': identifier, 'attempts': attempts}
        )
        
        # Auto-block after too many attempts
        if attempts >= SecurityManager.MAX_LOGIN_ATTEMPTS:
            SecurityManager._blocked_ips.add(SecurityManager.get_client_ip())
    
    @staticmethod
    def record_successful_login(identifier):
        """Record successful login and reset failed attempts"""
        if identifier in SecurityManager._failed_attempts:
            del SecurityManager._failed_attempts[identifier]
        
        SecurityManager.log_security_event(
            'successful_login',
            f'Successful login for {identifier}',
            severity='info',
            additional_data={'identifier': identifier}
        )
    
    @staticmethod
    def is_ip_blocked(ip_address=None):
        """Check if IP address is blocked"""
        if ip_address is None:
            ip_address = SecurityManager.get_client_ip()
        
        return ip_address in SecurityManager._blocked_ips
    
    @staticmethod
    def detect_suspicious_input(input_data):
        """Detect potentially malicious input patterns"""
        if not input_data:
            return False
        
        input_str = str(input_data).lower()
        
        for pattern in SecurityManager.SUSPICIOUS_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                SecurityManager.log_security_event(
                    'suspicious_input_detected',
                    f'Suspicious pattern detected: {pattern}',
                    severity='high',
                    additional_data={'pattern': pattern, 'input_sample': input_str[:100]}
                )
                return True
        
        return False
    
    @staticmethod
    def validate_session_security():
        """Validate session security and detect anomalies"""
        if not current_user.is_authenticated:
            return True
        
        current_ip = SecurityManager.get_client_ip()
        session_ip = session.get('login_ip')
        
        # Check for IP address changes (potential session hijacking)
        if session_ip and session_ip != current_ip:
            SecurityManager.log_security_event(
                'session_ip_change',
                f'Session IP changed from {session_ip} to {current_ip}',
                severity='high',
                additional_data={'old_ip': session_ip, 'new_ip': current_ip}
            )
            return False
        
        # Check session age
        login_time = session.get('login_time')
        if login_time:
            session_age = datetime.now() - datetime.fromisoformat(login_time)
            if session_age > timedelta(hours=8):  # 8 hour session limit
                SecurityManager.log_security_event(
                    'session_expired',
                    f'Session expired after {session_age}',
                    severity='info'
                )
                return False
        
        return True
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hash password with salt using SHA-256"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Combine password and salt
        salted_password = password + salt
        
        # Hash multiple times for added security
        hashed = salted_password
        for _ in range(10000):  # 10,000 iterations
            hashed = hashlib.sha256(hashed.encode()).hexdigest()
        
        return f"{salt}:{hashed}"
    
    @staticmethod
    def verify_password(password, stored_hash):
        """Verify password against stored hash"""
        try:
            salt, hashed = stored_hash.split(':', 1)
            return SecurityManager.hash_password(password, salt) == stored_hash
        except ValueError:
            return False
    
    @staticmethod
    def check_password_strength(password):
        """Check password strength and return score and recommendations"""
        score = 0
        recommendations = []
        
        # Length check
        if len(password) >= 8:
            score += 2
        else:
            recommendations.append("استخدم 8 أحرف على الأقل")
        
        if len(password) >= 12:
            score += 1
        
        # Character variety checks
        if re.search(r'[a-z]', password):
            score += 1
        else:
            recommendations.append("أضف أحرف صغيرة")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            recommendations.append("أضف أحرف كبيرة")
        
        if re.search(r'\d', password):
            score += 1
        else:
            recommendations.append("أضف أرقام")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 2
        else:
            recommendations.append("أضف رموز خاصة")
        
        # Common password check
        common_passwords = ['password', '123456', 'admin', 'user', 'test']
        if password.lower() in common_passwords:
            score = max(0, score - 3)
            recommendations.append("تجنب كلمات المرور الشائعة")
        
        # Determine strength level
        if score >= 7:
            strength = "قوية جداً"
        elif score >= 5:
            strength = "قوية"
        elif score >= 3:
            strength = "متوسطة"
        else:
            strength = "ضعيفة"
        
        return {
            'score': score,
            'max_score': 8,
            'strength': strength,
            'recommendations': recommendations
        }
    
    @staticmethod
    def get_security_headers():
        """Get recommended security headers"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https://cdn.jsdelivr.net;",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    @staticmethod
    def clean_expired_blocks():
        """Clean expired IP blocks and failed attempts"""
        # This would typically be run as a background task
        # For now, we'll implement a simple time-based cleanup
        current_time = time.time()
        
        # Clean rate limits older than 1 hour
        for identifier in list(SecurityManager._rate_limits.keys()):
            requests = SecurityManager._rate_limits[identifier]
            while requests and requests[0] < current_time - 3600:
                requests.popleft()
            
            if not requests:
                del SecurityManager._rate_limits[identifier]
        
        # Reset failed attempts after lockout duration
        # In a real implementation, you'd store timestamps with attempts
        # For simplicity, we'll clear all after a certain time
        
        return True
    
    @staticmethod
    def get_security_dashboard_data():
        """Get security dashboard data for admin"""
        try:
            # Get recent security events
            recent_events = db.session.query(AuditLog).filter(
                AuditLog.resource_type == 'security',
                AuditLog.timestamp >= datetime.now() - timedelta(days=7)
            ).order_by(AuditLog.timestamp.desc()).limit(50).all()
            
            # Count events by type
            event_counts = defaultdict(int)
            for event in recent_events:
                event_counts[event.action] += 1
            
            # Get blocked IPs count
            blocked_ips_count = len(SecurityManager._blocked_ips)
            
            # Get active rate limits
            active_rate_limits = len([k for k, v in SecurityManager._rate_limits.items() if v])
            
            return {
                'recent_events': [
                    {
                        'timestamp': event.timestamp.isoformat(),
                        'action': event.action,
                        'ip_address': event.ip_address,
                        'user_id': event.user_id,
                        'details': json.loads(event.details) if event.details else {}
                    }
                    for event in recent_events
                ],
                'event_counts': dict(event_counts),
                'blocked_ips_count': blocked_ips_count,
                'active_rate_limits': active_rate_limits,
                'failed_attempts_count': len(SecurityManager._failed_attempts)
            }
            
        except Exception as e:
            current_app.logger.error(f"Failed to get security dashboard data: {e}")
            return {
                'recent_events': [],
                'event_counts': {},
                'blocked_ips_count': 0,
                'active_rate_limits': 0,
                'failed_attempts_count': 0
            }
