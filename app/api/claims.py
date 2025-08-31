#!/usr/bin/env python3
"""
API endpoints for claims management
"""
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models import Claim, ClaimAttachment, InsuranceCompany, User
from app.api.auth import get_current_user, admin_required
from app import db
import logging

logger = logging.getLogger(__name__)

class ClaimsResource(Resource):
    """Claims collection endpoint"""
    
    @jwt_required()
    def get(self):
        """Get list of claims with filtering and pagination"""
        try:
            current_user = get_current_user()
            if not current_user:
                return {'error': 'User not found'}, 401
            
            # Parse query parameters
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            status = request.args.get('status')
            company_id = request.args.get('company_id', type=int)
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Build query
            query = Claim.query
            
            # Filter by user role
            if current_user.role != 'admin':
                query = query.filter(Claim.created_by_user_id == current_user.id)
            
            # Apply filters
            if status:
                query = query.filter(Claim.status == status)
            if company_id:
                query = query.filter(Claim.company_id == company_id)
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Claim.created_at >= start_date)
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(Claim.created_at <= end_date)
            
            # Order by creation date (newest first)
            query = query.order_by(Claim.created_at.desc())
            
            # Paginate
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            claims = []
            for claim in pagination.items:
                claims.append({
                    'id': claim.id,
                    'company_id': claim.company_id,
                    'company_name': claim.insurance_company.name_ar,
                    'client_name': claim.client_name,
                    'client_national_id': claim.client_national_id,
                    'policy_number': claim.policy_number,
                    'incident_number': claim.incident_number,
                    'incident_date': claim.incident_date.isoformat() if claim.incident_date else None,
                    'claim_amount': float(claim.claim_amount),
                    'currency': claim.currency,
                    'coverage_type': claim.coverage_type,
                    'claim_details': claim.claim_details,
                    'city': claim.city,
                    'tags': claim.tags,
                    'status': claim.status,
                    'email_sent_at': claim.email_sent_at.isoformat() if claim.email_sent_at else None,
                    'created_at': claim.created_at.isoformat(),
                    'updated_at': claim.updated_at.isoformat(),
                    'created_by': claim.created_by.full_name,
                    'attachments_count': len(claim.attachments)
                })
            
            return {
                'success': True,
                'claims': claims,
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching claims: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required()
    def post(self):
        """Create new claim"""
        try:
            current_user = get_current_user()
            if not current_user:
                return {'error': 'User not found'}, 401
            
            if current_user.role == 'viewer':
                return {'error': 'Insufficient permissions'}, 403
            
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Validate required fields
            required_fields = ['company_id', 'client_name', 'client_national_id', 
                             'incident_date', 'claim_amount', 'coverage_type', 'claim_details']
            
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400
            
            # Validate company exists
            company = InsuranceCompany.query.get(data['company_id'])
            if not company:
                return {'error': 'Invalid company_id'}, 400
            
            # Parse incident_date
            try:
                incident_date = datetime.strptime(data['incident_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'error': 'Invalid incident_date format. Use YYYY-MM-DD'}, 400
            
            # Create claim
            claim = Claim(
                company_id=data['company_id'],
                client_name=data['client_name'],
                client_national_id=data['client_national_id'],
                policy_number=data.get('policy_number'),
                incident_number=data.get('incident_number'),
                incident_date=incident_date,
                claim_amount=data['claim_amount'],
                currency=data.get('currency', 'SAR'),
                coverage_type=data['coverage_type'],
                claim_details=data['claim_details'],
                city=data.get('city'),
                tags=data.get('tags'),
                created_by_user_id=current_user.id
            )
            
            db.session.add(claim)
            db.session.commit()
            
            logger.info(f"Claim created via API: {claim.id} by user {current_user.email}")
            
            return {
                'success': True,
                'claim_id': claim.id,
                'message': 'Claim created successfully'
            }, 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating claim: {str(e)}")
            return {'error': 'Internal server error'}, 500

class ClaimResource(Resource):
    """Individual claim endpoint"""
    
    @jwt_required()
    def get(self, claim_id):
        """Get specific claim details"""
        try:
            current_user = get_current_user()
            if not current_user:
                return {'error': 'User not found'}, 401
            
            claim = Claim.query.get(claim_id)
            if not claim:
                return {'error': 'Claim not found'}, 404
            
            # Check permissions
            if current_user.role != 'admin' and claim.created_by_user_id != current_user.id:
                return {'error': 'Access denied'}, 403
            
            # Get attachments
            attachments = []
            for attachment in claim.attachments:
                attachments.append({
                    'id': attachment.id,
                    'filename': attachment.original_filename,
                    'size': attachment.file_size,
                    'mime_type': attachment.mime_type,
                    'uploaded_at': attachment.uploaded_at.isoformat()
                })
            
            return {
                'success': True,
                'claim': {
                    'id': claim.id,
                    'company_id': claim.company_id,
                    'company_name': claim.insurance_company.name_ar,
                    'client_name': claim.client_name,
                    'client_national_id': claim.client_national_id,
                    'policy_number': claim.policy_number,
                    'incident_number': claim.incident_number,
                    'incident_date': claim.incident_date.isoformat() if claim.incident_date else None,
                    'claim_amount': float(claim.claim_amount),
                    'currency': claim.currency,
                    'coverage_type': claim.coverage_type,
                    'claim_details': claim.claim_details,
                    'city': claim.city,
                    'tags': claim.tags,
                    'status': claim.status,
                    'email_message_id': claim.email_message_id,
                    'email_sent_at': claim.email_sent_at.isoformat() if claim.email_sent_at else None,
                    'created_at': claim.created_at.isoformat(),
                    'updated_at': claim.updated_at.isoformat(),
                    'created_by': claim.created_by.full_name,
                    'attachments': attachments
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching claim {claim_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required()
    def put(self, claim_id):
        """Update claim"""
        try:
            current_user = get_current_user()
            if not current_user:
                return {'error': 'User not found'}, 401
            
            if current_user.role == 'viewer':
                return {'error': 'Insufficient permissions'}, 403
            
            claim = Claim.query.get(claim_id)
            if not claim:
                return {'error': 'Claim not found'}, 404
            
            # Check permissions
            if current_user.role != 'admin' and claim.created_by_user_id != current_user.id:
                return {'error': 'Access denied'}, 403
            
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Update allowed fields
            updatable_fields = ['client_name', 'client_national_id', 'policy_number', 
                              'incident_number', 'claim_amount', 'claim_details', 
                              'city', 'tags']
            
            for field in updatable_fields:
                if field in data:
                    setattr(claim, field, data[field])
            
            # Handle incident_date separately
            if 'incident_date' in data:
                try:
                    claim.incident_date = datetime.strptime(data['incident_date'], '%Y-%m-%d').date()
                except ValueError:
                    return {'error': 'Invalid incident_date format. Use YYYY-MM-DD'}, 400
            
            claim.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Claim updated via API: {claim.id} by user {current_user.email}")
            
            return {
                'success': True,
                'message': 'Claim updated successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating claim {claim_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500

class ClaimStatusResource(Resource):
    """Claim status management endpoint"""
    
    @jwt_required()
    def put(self, claim_id):
        """Update claim status"""
        try:
            current_user = get_current_user()
            if not current_user:
                return {'error': 'User not found'}, 401
            
            if current_user.role == 'viewer':
                return {'error': 'Insufficient permissions'}, 403
            
            claim = Claim.query.get(claim_id)
            if not claim:
                return {'error': 'Claim not found'}, 404
            
            # Check permissions
            if current_user.role != 'admin' and claim.created_by_user_id != current_user.id:
                return {'error': 'Access denied'}, 403
            
            data = request.get_json()
            if not data or 'status' not in data:
                return {'error': 'Status is required'}, 400
            
            new_status = data['status']
            valid_statuses = ['draft', 'ready', 'sent', 'failed', 'acknowledged', 'paid']
            
            if new_status not in valid_statuses:
                return {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, 400
            
            old_status = claim.status
            claim.status = new_status
            claim.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Claim status updated via API: {claim.id} from {old_status} to {new_status} by user {current_user.email}")
            
            return {
                'success': True,
                'message': f'Claim status updated from {old_status} to {new_status}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating claim status {claim_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
