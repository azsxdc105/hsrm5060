from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.Enum('admin', 'claims_agent', 'viewer', name='user_roles'), default='claims_agent')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    claims = db.relationship('Claim', backref='created_by', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
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