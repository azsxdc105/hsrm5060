from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import json
from enum import Enum
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)  # Phone number for SMS notifications
    whatsapp_number = db.Column(db.String(20), nullable=True)  # WhatsApp number for WhatsApp notifications
    password_hash = db.Column(db.String(255))
    role = db.Column(db.Enum('admin', 'claims_agent', 'viewer', name='user_roles'), default='claims_agent')
    active = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(2), default='ar')  # Preferred language for notifications
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Security fields (commented out temporarily to fix the error)
    last_login = db.Column(db.DateTime, nullable=True)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    # password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    two_factor_backup_codes = db.Column(db.JSON, nullable=True)

    # Temporary SMS verification
    temp_sms_code = db.Column(db.String(10), nullable=True)
    temp_sms_code_expiry = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    claims = db.relationship('Claim', backref='created_by', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def lock_account(self, minutes=30):
        """Lock account for specified minutes"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        self.login_attempts = 0

    def unlock_account(self):
        """Unlock account"""
        self.locked_until = None
        self.login_attempts = 0

    def record_login_attempt(self, success=False):
        """Record login attempt"""
        if success:
            self.last_login = datetime.utcnow()
            self.login_attempts = 0
            self.locked_until = None
        else:
            self.login_attempts += 1
            if self.login_attempts >= 5:  # Lock after 5 failed attempts
                self.lock_account()

    def needs_password_change(self, days=90):
        """Check if password needs to be changed"""
        # Temporarily disabled until password_changed_at column is properly added
        return False
        # if not self.password_changed_at:
        #     return True
        # password_age = datetime.utcnow() - self.password_changed_at
        # return password_age.days > days

    def __repr__(self):
        return f'<User {self.email}>'

class InsuranceCompany(db.Model):
    __tablename__ = 'insurance_companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200), nullable=False)
    claims_email_primary = db.Column(db.String(120), nullable=False)
    claims_email_cc = db.Column(db.Text)  # JSON string for multiple CC emails
    policy_portal_url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    email_template_ar = db.Column(db.Text)
    email_template_en = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    claims = db.relationship('Claim', backref='insurance_company', lazy=True)
    
    def __repr__(self):
        return f'<InsuranceCompany {self.name_ar}>'

class Claim(db.Model):
    __tablename__ = 'claims'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = db.Column(db.Integer, db.ForeignKey('insurance_companies.id'), nullable=False)
    claim_type_id = db.Column(db.Integer, db.ForeignKey('claim_types.id'), nullable=True)  # Dynamic form type
    client_name = db.Column(db.String(120), nullable=False)
    client_national_id = db.Column(db.String(20), nullable=False)
    policy_number = db.Column(db.String(50))
    incident_number = db.Column(db.String(50))
    incident_date = db.Column(db.Date, nullable=False)
    claim_amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='SAR')
    coverage_type = db.Column(db.Enum('third_party', 'comprehensive', 'other', name='coverage_types'), nullable=False)
    claim_details = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100))
    tags = db.Column(db.String(500))  # Comma-separated tags
    status = db.Column(db.Enum('draft', 'ready', 'sent', 'failed', 'acknowledged', 'paid', name='claim_statuses'), default='draft')
    email_message_id = db.Column(db.String(255))
    email_sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    attachments = db.relationship('ClaimAttachment', backref='claim', lazy=True, cascade='all, delete-orphan')
    email_logs = db.relationship('EmailLog', backref='claim', lazy=True)
    
    def get_status_color(self):
        colors = {
            'draft': 'secondary',
            'ready': 'info',
            'sent': 'primary',
            'failed': 'danger',
            'acknowledged': 'warning',
            'paid': 'success'
        }
        return colors.get(self.status, 'secondary')
    
    def get_status_text_ar(self):
        texts = {
            'draft': 'مسودة',
            'ready': 'جاهز',
            'sent': 'مرسل',
            'failed': 'فشل',
            'acknowledged': 'مستلم',
            'paid': 'مدفوع'
        }
        return texts.get(self.status, 'غير محدد')
    
    def __repr__(self):
        return f'<Claim {self.id}>'

class ClaimAttachment(db.Model):
    __tablename__ = 'claim_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.String(36), db.ForeignKey('claims.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)
    storage_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    extracted_text = db.Column(db.Text)  # For OCR results
    doc_type = db.Column(db.Enum('najim_report', 'id_copy', 'invoice', 'photo', 'medical_report', 'other', name='doc_types'), default='other')
    
    def __repr__(self):
        return f'<ClaimAttachment {self.original_filename}>'

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.String(36), db.ForeignKey('claims.id'), nullable=False)
    to_emails = db.Column(db.String(500), nullable=False)
    cc_emails = db.Column(db.String(500))
    subject = db.Column(db.String(500), nullable=False)
    body_preview = db.Column(db.Text)
    send_status = db.Column(db.Enum('success', 'failed', name='email_statuses'), nullable=False)
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailLog {self.id}>'

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSettings {self.key}>'

class SimpleNotification(db.Model):
    """Simple notification model for backward compatibility"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # claim_created, claim_status_changed, etc.
    related_claim_id = db.Column(db.String(36), db.ForeignKey('claims.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    sent_via_email = db.Column(db.Boolean, default=False)
    sent_via_sms = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='simple_notifications')
    related_claim = db.relationship('Claim', backref='simple_notifications')

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'related_claim_id': self.related_claim_id,
            'is_read': self.is_read,
            'sent_via_email': self.sent_via_email,
            'sent_via_sms': self.sent_via_sms,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None
        }

    def __repr__(self):
        return f'<SimpleNotification {self.id}: {self.title}>'

class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # claim_created, claim_status_changed, etc.
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=False)
    push_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='notification_preferences')

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'notification_type', name='unique_user_notification_type'),)

    def __repr__(self):
        return f'<NotificationPreference {self.user_id}: {self.notification_type}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    resource_type = db.Column(db.String(50), nullable=False)  # claim, user, company, etc.
    resource_id = db.Column(db.String(100), nullable=True)  # ID of the affected resource
    old_values = db.Column(db.Text, nullable=True)  # JSON of old values
    new_values = db.Column(db.Text, nullable=True)  # JSON of new values
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    details = db.Column(db.Text, nullable=True)  # Additional details

    # Relationships
    user = db.relationship('User', backref='audit_logs')

    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'System',
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }

    @staticmethod
    def log_action(user_id, action, resource_type, resource_id=None, old_values=None,
                   new_values=None, ip_address=None, user_agent=None, details=None):
        """Create audit log entry"""
        import json

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            old_values=json.dumps(old_values, ensure_ascii=False) if old_values else None,
            new_values=json.dumps(new_values, ensure_ascii=False) if new_values else None,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        db.session.add(audit_log)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Log the error but don't fail the main operation
            print(f"Failed to create audit log: {e}")

    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action} on {self.resource_type}>'

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = db.Column(db.String(36), db.ForeignKey('claims.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='SAR', nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # bank_transfer, check, cash, online
    payment_reference = db.Column(db.String(100), nullable=True)  # Reference number from bank/payment gateway
    payment_date = db.Column(db.Date, nullable=False)
    received_date = db.Column(db.Date, nullable=True)  # When payment was actually received
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, received, failed, cancelled
    notes = db.Column(db.Text, nullable=True)

    # Bank transfer specific fields
    bank_name = db.Column(db.String(100), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    iban = db.Column(db.String(34), nullable=True)

    # Check specific fields
    check_number = db.Column(db.String(50), nullable=True)
    check_bank = db.Column(db.String(100), nullable=True)

    # Online payment specific fields
    transaction_id = db.Column(db.String(100), nullable=True)
    gateway_response = db.Column(db.Text, nullable=True)  # JSON response from payment gateway

    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    claim = db.relationship('Claim', backref='payments')
    created_by = db.relationship('User', backref='created_payments')

    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'claim_id': self.claim_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'status': self.status,
            'notes': self.notes,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'iban': self.iban,
            'check_number': self.check_number,
            'check_bank': self.check_bank,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by.full_name
        }

    def get_status_text_ar(self):
        """Get Arabic status text"""
        status_map = {
            'pending': 'في الانتظار',
            'received': 'مستلم',
            'failed': 'فشل',
            'cancelled': 'ملغي'
        }
        return status_map.get(self.status, self.status)

    def get_status_color(self):
        """Get Bootstrap color class for status"""
        color_map = {
            'pending': 'warning',
            'received': 'success',
            'failed': 'danger',
            'cancelled': 'secondary'
        }
        return color_map.get(self.status, 'secondary')

    def get_payment_method_text_ar(self):
        """Get Arabic payment method text"""
        method_map = {
            'bank_transfer': 'تحويل بنكي',
            'check': 'شيك',
            'cash': 'نقدي',
            'online': 'دفع إلكتروني'
        }
        return method_map.get(self.payment_method, self.payment_method)

    def __repr__(self):
        return f'<Payment {self.id}: {self.amount} {self.currency} for claim {self.claim_id}>'


# ============================================================================
# ADVANCED NOTIFICATIONS SYSTEM MODELS
# ============================================================================

class NotificationType(Enum):
    """Notification types enumeration"""
    EMAIL = 'email'
    SMS = 'sms'
    PUSH = 'push'
    WHATSAPP = 'whatsapp'
    IN_APP = 'in_app'


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'


class NotificationTemplate(db.Model):
    """Templates for different types of notifications"""
    __tablename__ = 'notification_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    event_type = db.Column(db.String(50), nullable=False)  # claim_created, claim_sent, etc.
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)

    # Templates for different languages
    subject_ar = db.Column(db.String(200))
    subject_en = db.Column(db.String(200))
    content_ar = db.Column(db.Text)
    content_en = db.Column(db.Text)

    # Template variables (JSON)
    variables = db.Column(db.Text)  # JSON string of available variables

    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_variables_list(self):
        """Get list of template variables"""
        if self.variables:
            return json.loads(self.variables)
        return []

    def set_variables_list(self, variables_list):
        """Set template variables"""
        self.variables = json.dumps(variables_list)

    def __repr__(self):
        return f'<NotificationTemplate {self.name}>'


class UserNotificationSettings(db.Model):
    """User-specific notification preferences"""
    __tablename__ = 'user_notification_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Notification type preferences
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=False)
    push_enabled = db.Column(db.Boolean, default=True)
    whatsapp_enabled = db.Column(db.Boolean, default=False)
    in_app_enabled = db.Column(db.Boolean, default=True)

    # Event-specific settings (JSON)
    event_settings = db.Column(db.Text)  # JSON: {"claim_created": {"email": true, "sms": false}, ...}

    # Quiet hours
    quiet_hours_enabled = db.Column(db.Boolean, default=False)
    quiet_hours_start = db.Column(db.Time)
    quiet_hours_end = db.Column(db.Time)

    # WhatsApp phone number
    whatsapp_phone = db.Column(db.String(20))

    # Push notification token
    push_token = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='notification_settings')

    def get_event_settings(self):
        """Get event-specific settings"""
        if self.event_settings:
            return json.loads(self.event_settings)
        return {}

    def set_event_settings(self, settings):
        """Set event-specific settings"""
        self.event_settings = json.dumps(settings)

    def is_notification_enabled(self, notification_type, event_type=None):
        """Check if notification type is enabled for user"""
        # Check global setting
        type_enabled = getattr(self, f'{notification_type}_enabled', False)
        if not type_enabled:
            return False

        # Check event-specific setting if provided
        if event_type:
            event_settings = self.get_event_settings()
            event_config = event_settings.get(event_type, {})
            return event_config.get(notification_type, type_enabled)

        return type_enabled

    def __repr__(self):
        return f'<UserNotificationSettings for user {self.user_id}>'


class Notification(db.Model):
    """Individual notification records"""
    __tablename__ = 'advanced_notifications'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Notification details
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    priority = db.Column(db.Enum(NotificationPriority), default=NotificationPriority.NORMAL)

    # Related entities
    claim_id = db.Column(db.String(36), db.ForeignKey('claims.id'), nullable=True)
    related_claim_id = db.Column(db.String(36), db.ForeignKey('claims.id'), nullable=True)  # For backward compatibility
    event_type = db.Column(db.String(50))  # claim_created, claim_sent, etc.

    # Status and delivery
    status = db.Column(db.Enum('pending', 'sent', 'delivered', 'failed', 'read', name='notification_status'), default='pending')
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)

    # Backward compatibility fields
    is_read = db.Column(db.Boolean, default=False)
    sent_via_email = db.Column(db.Boolean, default=False)
    sent_via_sms = db.Column(db.Boolean, default=False)

    # Scheduling
    scheduled_for = db.Column(db.DateTime)  # For scheduled notifications

    # Delivery details
    delivery_details = db.Column(db.Text)  # JSON with delivery info (message_id, error, etc.)

    # Extra data
    extra_data = db.Column(db.Text)  # JSON with additional data

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='advanced_notifications')
    claim = db.relationship('Claim', foreign_keys=[claim_id], backref='advanced_notifications')
    related_claim = db.relationship('Claim', foreign_keys=[related_claim_id], backref='old_notifications')

    def get_delivery_details(self):
        """Get delivery details as dict"""
        if self.delivery_details:
            return json.loads(self.delivery_details)
        return {}

    def set_delivery_details(self, details):
        """Set delivery details"""
        self.delivery_details = json.dumps(details)

    def get_extra_data(self):
        """Get extra data as dict"""
        if self.extra_data:
            return json.loads(self.extra_data)
        return {}

    def set_extra_data(self, data):
        """Set extra data"""
        self.extra_data = json.dumps(data)

    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()

    def mark_as_delivered(self):
        """Mark notification as delivered"""
        self.status = 'delivered'
        self.delivered_at = datetime.utcnow()

    def mark_as_read(self):
        """Mark notification as read"""
        self.status = 'read'
        self.is_read = True  # For backward compatibility
        self.read_at = datetime.utcnow()

    def mark_as_failed(self, error_message=None):
        """Mark notification as failed"""
        self.status = 'failed'
        if error_message:
            details = self.get_delivery_details()
            details['error'] = error_message
            self.set_delivery_details(details)

    def to_dict(self):
        """Convert notification to dictionary (for backward compatibility)"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type.value if self.notification_type else 'unknown',
            'related_claim_id': self.related_claim_id or self.claim_id,
            'is_read': self.is_read,
            'sent_via_email': self.sent_via_email,
            'sent_via_sms': self.sent_via_sms,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None
        }

    def is_scheduled(self):
        """Check if notification is scheduled for future"""
        return self.scheduled_for and self.scheduled_for > datetime.utcnow()

    def get_priority_color(self):
        """Get Bootstrap color class for priority"""
        color_map = {
            'low': 'secondary',
            'normal': 'primary',
            'high': 'warning',
            'urgent': 'danger'
        }
        return color_map.get(self.priority.value if self.priority else 'normal', 'primary')

    def get_status_color(self):
        """Get Bootstrap color class for status"""
        color_map = {
            'pending': 'warning',
            'sent': 'info',
            'delivered': 'success',
            'failed': 'danger',
            'read': 'success'
        }
        return color_map.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'


class NotificationQueue(db.Model):
    """Queue for batch notification processing"""
    __tablename__ = 'notification_queue'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Batch details
    batch_name = db.Column(db.String(100))
    event_type = db.Column(db.String(50), nullable=False)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)

    # Recipients (JSON array)
    recipients = db.Column(db.Text, nullable=False)  # JSON array of recipient objects

    # Content
    template_id = db.Column(db.Integer, db.ForeignKey('notification_templates.id'))
    custom_content = db.Column(db.Text)  # JSON with custom content if not using template

    # Context data for template rendering
    context_data = db.Column(db.Text)  # JSON with template variables

    # Scheduling
    scheduled_for = db.Column(db.DateTime, default=datetime.utcnow)

    # Processing status
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', name='queue_status'), default='pending')
    processed_at = db.Column(db.DateTime)

    # Results
    total_recipients = db.Column(db.Integer, default=0)
    successful_sends = db.Column(db.Integer, default=0)
    failed_sends = db.Column(db.Integer, default=0)

    # Error details
    error_details = db.Column(db.Text)  # JSON with error information

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    template = db.relationship('NotificationTemplate', backref='queue_items')

    def get_recipients_list(self):
        """Get recipients as list"""
        if self.recipients:
            return json.loads(self.recipients)
        return []

    def set_recipients_list(self, recipients_list):
        """Set recipients list"""
        self.recipients = json.dumps(recipients_list)
        self.total_recipients = len(recipients_list)

    def get_context_data(self):
        """Get context data as dict"""
        if self.context_data:
            return json.loads(self.context_data)
        return {}

    def set_context_data(self, context):
        """Set context data"""
        self.context_data = json.dumps(context)

    def get_custom_content(self):
        """Get custom content as dict"""
        if self.custom_content:
            return json.loads(self.custom_content)
        return {}

    def set_custom_content(self, content):
        """Set custom content"""
        self.custom_content = json.dumps(content)

    def get_error_details(self):
        """Get error details as dict"""
        if self.error_details:
            return json.loads(self.error_details)
        return {}

    def set_error_details(self, errors):
        """Set error details"""
        self.error_details = json.dumps(errors)

    def mark_as_processing(self):
        """Mark queue item as processing"""
        self.status = 'processing'
        self.updated_at = datetime.utcnow()

    def mark_as_completed(self, successful=0, failed=0):
        """Mark queue item as completed"""
        self.status = 'completed'
        self.processed_at = datetime.utcnow()
        self.successful_sends = successful
        self.failed_sends = failed

    def mark_as_failed(self, error_message):
        """Mark queue item as failed"""
        self.status = 'failed'
        self.processed_at = datetime.utcnow()
        self.set_error_details({'error': error_message})

    def get_success_rate(self):
        """Get success rate percentage"""
        if self.total_recipients == 0:
            return 0
        return round((self.successful_sends / self.total_recipients) * 100, 1)

    def is_ready_for_processing(self):
        """Check if queue item is ready for processing"""
        return (self.status == 'pending' and
                self.scheduled_for <= datetime.utcnow())

    def __repr__(self):
        return f'<NotificationQueue {self.id}: {self.batch_name}>'


# ============================================================================
# DYNAMIC FORMS SYSTEM MODELS
# ============================================================================

class ClaimType(db.Model):
    """Different types of insurance claims with dynamic form configurations"""
    __tablename__ = 'claim_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)  # car, health, home, travel, etc.
    description_ar = db.Column(db.Text)
    description_en = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fas fa-file-alt')  # FontAwesome icon
    color = db.Column(db.String(7), default='#007bff')  # Hex color
    active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # Form configuration (JSON)
    form_config = db.Column(db.JSON)  # Dynamic form fields configuration
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    claims = db.relationship('Claim', backref='claim_type', lazy=True)
    
    def get_form_config(self):
        """Get form configuration as dict"""
        if self.form_config:
            return self.form_config
        return {}
    
    def set_form_config(self, config):
        """Set form configuration"""
        self.form_config = config
    
    def __repr__(self):
        return f'<ClaimType {self.code}>'

class DynamicFormField(db.Model):
    """Dynamic form fields for different claim types"""
    __tablename__ = 'dynamic_form_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    claim_type_id = db.Column(db.Integer, db.ForeignKey('claim_types.id'), nullable=False)
    
    # Field properties
    field_name = db.Column(db.String(50), nullable=False)  # Technical name
    field_label_ar = db.Column(db.String(200), nullable=False)  # Arabic label
    field_label_en = db.Column(db.String(200), nullable=False)  # English label
    field_type = db.Column(db.String(20), nullable=False)  # text, number, select, date, file, etc.
    field_order = db.Column(db.Integer, default=0)
    
    # Validation
    required = db.Column(db.Boolean, default=False)
    min_length = db.Column(db.Integer)
    max_length = db.Column(db.Integer)
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    pattern = db.Column(db.String(200))  # Regex pattern
    
    # Options for select fields (JSON)
    field_options = db.Column(db.JSON)  # For select, radio, checkbox fields
    
    # Conditional logic (JSON)
    conditional_logic = db.Column(db.JSON)  # Show/hide based on other fields
    
    # Display properties
    placeholder_ar = db.Column(db.String(200))
    placeholder_en = db.Column(db.String(200))
    help_text_ar = db.Column(db.Text)
    help_text_en = db.Column(db.Text)
    css_class = db.Column(db.String(100))
    
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    claim_type = db.relationship('ClaimType', backref='dynamic_fields')
    
    def get_options(self):
        """Get field options as list"""
        if self.field_options:
            return self.field_options
        return []
    
    def get_conditional_logic(self):
        """Get conditional logic as dict"""
        if self.conditional_logic:
            return self.conditional_logic
        return {}
    
    def __repr__(self):
        return f'<DynamicFormField {self.field_name}>'

class ClaimDynamicData(db.Model):
    """Store dynamic form data for claims"""
    __tablename__ = 'claim_dynamic_data'
    
    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.String(36), db.ForeignKey('claims.id'), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)
    field_value = db.Column(db.Text)  # Store as JSON for complex data
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    claim = db.relationship('Claim', backref='dynamic_data')
    
    def get_value(self):
        """Get field value, parse JSON if needed"""
        if self.field_value:
            try:
                return json.loads(self.field_value)
            except:
                return self.field_value
        return None
    
    def set_value(self, value):
        """Set field value, convert to JSON if needed"""
        if isinstance(value, (dict, list)):
            self.field_value = json.dumps(value, ensure_ascii=False)
        else:
            self.field_value = str(value) if value is not None else None
    
    def __repr__(self):
        return f'<ClaimDynamicData {self.field_name}>'

# ============================================================================
# AI CLASSIFICATION SYSTEM MODELS
# ============================================================================

class ClaimClassification(db.Model):
    """AI classification results for claims"""
    __tablename__ = 'claim_classifications'

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.String(36), db.ForeignKey('claims.id'), nullable=False, unique=True)

    # Classification results
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50))
    confidence = db.Column(db.Float, nullable=False)

    # Risk assessment
    risk_level = db.Column(db.Enum('low', 'medium', 'high', name='risk_levels'), nullable=False)
    fraud_probability = db.Column(db.Float, default=0.0)

    # AI suggestions
    suggested_amount = db.Column(db.Numeric(10, 2))
    reasoning = db.Column(db.Text)  # JSON string with reasoning

    # Processing info
    ai_model_version = db.Column(db.String(20), default='1.0')
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Manual review
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    manual_override = db.Column(db.Boolean, default=False)
    manual_category = db.Column(db.String(50))
    manual_risk_level = db.Column(db.Enum('low', 'medium', 'high', name='manual_risk_levels'))
    review_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    claim = db.relationship('Claim', backref='ai_classification')
    reviewed_by = db.relationship('User', backref='reviewed_classifications')

    def get_reasoning_list(self):
        """Get reasoning as list"""
        if self.reasoning:
            return json.loads(self.reasoning)
        return []

    def set_reasoning_list(self, reasoning_list):
        """Set reasoning list"""
        self.reasoning = json.dumps(reasoning_list, ensure_ascii=False)

    def get_final_category(self):
        """Get final category (manual override or AI)"""
        return self.manual_category if self.manual_override else self.category

    def get_final_risk_level(self):
        """Get final risk level (manual override or AI)"""
        return self.manual_risk_level.value if (self.manual_override and self.manual_risk_level) else self.risk_level

    def get_category_display_name(self):
        """Get display name for category"""
        category_names = {
            'vehicle_accident': 'حادث مركبة',
            'medical': 'طبي',
            'property_damage': 'أضرار الممتلكات',
            'theft': 'سرقة',
            'natural_disaster': 'كارثة طبيعية',
            'unknown': 'غير محدد'
        }
        final_category = self.get_final_category()
        return category_names.get(final_category, final_category)

    def get_risk_level_display_name(self):
        """Get display name for risk level"""
        risk_names = {
            'low': 'منخفض',
            'medium': 'متوسط',
            'high': 'عالي'
        }
        final_risk = self.get_final_risk_level()
        return risk_names.get(final_risk, final_risk)

    def get_risk_level_color(self):
        """Get Bootstrap color class for risk level"""
        color_map = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger'
        }
        final_risk = self.get_final_risk_level()
        return color_map.get(final_risk, 'secondary')

    def get_fraud_risk_color(self):
        """Get Bootstrap color class for fraud probability"""
        if self.fraud_probability >= 0.7:
            return 'danger'
        elif self.fraud_probability >= 0.4:
            return 'warning'
        else:
            return 'success'

    def get_fraud_risk_text(self):
        """Get text description for fraud risk"""
        if self.fraud_probability >= 0.7:
            return 'عالي'
        elif self.fraud_probability >= 0.4:
            return 'متوسط'
        else:
            return 'منخفض'

    def mark_as_reviewed(self, user_id: int, notes: str = None,
                        manual_category: str = None, manual_risk: str = None):
        """Mark classification as manually reviewed"""
        self.reviewed_by_user_id = user_id
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes

        if manual_category and manual_category != self.category:
            self.manual_override = True
            self.manual_category = manual_category

        if manual_risk and manual_risk != self.risk_level:
            self.manual_override = True
            self.manual_risk_level = manual_risk

    def __repr__(self):
        return f'<ClaimClassification {self.claim_id}: {self.category}>'


class FraudIndicator(db.Model):
    """Fraud indicators detected for claims"""
    __tablename__ = 'fraud_indicators'

    id = db.Column(db.Integer, primary_key=True)
    classification_id = db.Column(db.Integer, db.ForeignKey('claim_classifications.id'), nullable=False)

    # Indicator details
    indicator_type = db.Column(db.String(50), nullable=False)  # pattern_match, amount_analysis, timing_analysis
    indicator_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    # Severity and confidence
    severity = db.Column(db.Enum('low', 'medium', 'high', name='indicator_severity'), nullable=False)
    confidence = db.Column(db.Float, nullable=False)

    # Additional data
    extra_data = db.Column(db.Text)  # JSON with additional indicator data

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    classification = db.relationship('ClaimClassification', backref='fraud_indicators')

    def get_extra_data(self):
        """Get extra data as dict"""
        if self.extra_data:
            return json.loads(self.extra_data)
        return {}

    def set_extra_data(self, data):
        """Set extra data"""
        self.extra_data = json.dumps(data, ensure_ascii=False)

    def get_severity_color(self):
        """Get Bootstrap color class for severity"""
        color_map = {
            'low': 'info',
            'medium': 'warning',
            'high': 'danger'
        }
        return color_map.get(self.severity, 'secondary')

    def get_severity_display_name(self):
        """Get display name for severity"""
        severity_names = {
            'low': 'منخفض',
            'medium': 'متوسط',
            'high': 'عالي'
        }
        return severity_names.get(self.severity, self.severity)

    def __repr__(self):
        return f'<FraudIndicator {self.indicator_name}: {self.severity}>'