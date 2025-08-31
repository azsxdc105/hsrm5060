#!/usr/bin/env python3
"""
Audit logging utilities for tracking all system operations
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, current_app
from flask_login import current_user
from app.models import AuditLog
from app import db
import logging

logger = logging.getLogger(__name__)

class AuditLogger:
    """Centralized audit logging system"""
    
    @staticmethod
    def get_client_info():
        """Get client IP and user agent"""
        if request:
            # Handle proxy headers
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            
            user_agent = request.headers.get('User-Agent', '')
            return ip_address, user_agent
        return None, None
    
    @staticmethod
    def log_user_action(action: str, resource_type: str, resource_id: str = None, 
                       old_values: Dict = None, new_values: Dict = None, 
                       details: str = None):
        """Log user action with automatic user detection"""
        try:
            user_id = current_user.id if current_user.is_authenticated else None
            ip_address, user_agent = AuditLogger.get_client_info()
            
            AuditLog.log_action(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details
            )
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
    
    @staticmethod
    def log_system_action(action: str, resource_type: str, resource_id: str = None,
                         details: str = None):
        """Log system action (no user)"""
        try:
            AuditLog.log_action(
                user_id=None,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details
            )
        except Exception as e:
            logger.error(f"Failed to log system action: {e}")

# Convenience functions for common operations
def log_login(user_id: int, success: bool = True):
    """Log user login attempt"""
    action = 'LOGIN_SUCCESS' if success else 'LOGIN_FAILED'
    ip_address, user_agent = AuditLogger.get_client_info()
    
    AuditLog.log_action(
        user_id=user_id if success else None,
        action=action,
        resource_type='user',
        resource_id=str(user_id),
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"Login {'successful' if success else 'failed'}"
    )

def log_logout(user_id: int):
    """Log user logout"""
    ip_address, user_agent = AuditLogger.get_client_info()
    
    AuditLog.log_action(
        user_id=user_id,
        action='LOGOUT',
        resource_type='user',
        resource_id=str(user_id),
        ip_address=ip_address,
        user_agent=user_agent,
        details="User logged out"
    )

def log_claim_created(claim):
    """Log claim creation"""
    claim_data = {
        'client_name': claim.client_name,
        'company_id': claim.company_id,
        'claim_amount': float(claim.claim_amount),
        'status': claim.status
    }
    
    AuditLogger.log_user_action(
        action='CREATE',
        resource_type='claim',
        resource_id=claim.id,
        new_values=claim_data,
        details=f"Created claim for {claim.client_name}"
    )

def log_claim_updated(claim, old_data: Dict, new_data: Dict):
    """Log claim update"""
    AuditLogger.log_user_action(
        action='UPDATE',
        resource_type='claim',
        resource_id=claim.id,
        old_values=old_data,
        new_values=new_data,
        details=f"Updated claim for {claim.client_name}"
    )

def log_claim_status_changed(claim, old_status: str, new_status: str):
    """Log claim status change"""
    AuditLogger.log_user_action(
        action='STATUS_CHANGE',
        resource_type='claim',
        resource_id=claim.id,
        old_values={'status': old_status},
        new_values={'status': new_status},
        details=f"Changed claim status from {old_status} to {new_status}"
    )

def log_claim_sent(claim):
    """Log claim email sending"""
    AuditLogger.log_user_action(
        action='EMAIL_SENT',
        resource_type='claim',
        resource_id=claim.id,
        details=f"Sent claim email to {claim.insurance_company.name_ar}"
    )

def log_claim_deleted(claim_id: str, client_name: str):
    """Log claim deletion"""
    AuditLogger.log_user_action(
        action='DELETE',
        resource_type='claim',
        resource_id=claim_id,
        details=f"Deleted claim for {client_name}"
    )

def log_user_created(user):
    """Log user creation"""
    user_data = {
        'full_name': user.full_name,
        'email': user.email,
        'role': user.role,
        'active': user.active
    }
    
    AuditLogger.log_user_action(
        action='CREATE',
        resource_type='user',
        resource_id=str(user.id),
        new_values=user_data,
        details=f"Created user {user.full_name}"
    )

def log_user_updated(user, old_data: Dict, new_data: Dict):
    """Log user update"""
    AuditLogger.log_user_action(
        action='UPDATE',
        resource_type='user',
        resource_id=str(user.id),
        old_values=old_data,
        new_values=new_data,
        details=f"Updated user {user.full_name}"
    )

def log_user_deleted(user_id: int, user_name: str):
    """Log user deletion"""
    AuditLogger.log_user_action(
        action='DELETE',
        resource_type='user',
        resource_id=str(user_id),
        details=f"Deleted user {user_name}"
    )

def log_company_created(company):
    """Log insurance company creation"""
    company_data = {
        'name_ar': company.name_ar,
        'name_en': company.name_en,
        'claims_email_primary': company.claims_email_primary,
        'active': company.active
    }
    
    AuditLogger.log_user_action(
        action='CREATE',
        resource_type='company',
        resource_id=str(company.id),
        new_values=company_data,
        details=f"Created insurance company {company.name_ar}"
    )

def log_company_updated(company, old_data: Dict, new_data: Dict):
    """Log insurance company update"""
    AuditLogger.log_user_action(
        action='UPDATE',
        resource_type='company',
        resource_id=str(company.id),
        old_values=old_data,
        new_values=new_data,
        details=f"Updated insurance company {company.name_ar}"
    )

def log_company_deleted(company_id: int, company_name: str):
    """Log insurance company deletion"""
    AuditLogger.log_user_action(
        action='DELETE',
        resource_type='company',
        resource_id=str(company_id),
        details=f"Deleted insurance company {company_name}"
    )

def log_data_export(export_type: str, format: str, record_count: int):
    """Log data export"""
    AuditLogger.log_user_action(
        action='EXPORT',
        resource_type=export_type,
        details=f"Exported {record_count} {export_type} records to {format.upper()}"
    )

def log_settings_changed(setting_key: str, old_value: Any, new_value: Any):
    """Log system settings change"""
    AuditLogger.log_user_action(
        action='SETTINGS_CHANGE',
        resource_type='settings',
        resource_id=setting_key,
        old_values={'value': old_value},
        new_values={'value': new_value},
        details=f"Changed setting {setting_key}"
    )

def log_api_access(endpoint: str, method: str, status_code: int):
    """Log API access"""
    AuditLogger.log_user_action(
        action='API_ACCESS',
        resource_type='api',
        resource_id=endpoint,
        details=f"{method} {endpoint} - Status: {status_code}"
    )

def log_file_upload(filename: str, file_size: int, claim_id: str = None):
    """Log file upload"""
    AuditLogger.log_user_action(
        action='FILE_UPLOAD',
        resource_type='file',
        resource_id=claim_id,
        details=f"Uploaded file {filename} ({file_size} bytes)"
    )

def log_password_change(user_id: int):
    """Log password change"""
    AuditLogger.log_user_action(
        action='PASSWORD_CHANGE',
        resource_type='user',
        resource_id=str(user_id),
        details="User changed password"
    )

def log_failed_login_attempt(email: str):
    """Log failed login attempt"""
    ip_address, user_agent = AuditLogger.get_client_info()
    
    AuditLog.log_action(
        user_id=None,
        action='LOGIN_FAILED',
        resource_type='user',
        resource_id=email,
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"Failed login attempt for {email}"
    )

# Global audit logger instance
audit_logger = AuditLogger()
