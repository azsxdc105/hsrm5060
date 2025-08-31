#!/usr/bin/env python3
"""
API endpoints for insurance companies management
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.models import InsuranceCompany
from app.api.auth import get_current_user, admin_required
from app import db
import logging

logger = logging.getLogger(__name__)

class CompaniesResource(Resource):
    """Insurance companies collection endpoint"""
    
    @jwt_required()
    def get(self):
        """Get list of insurance companies"""
        try:
            # Parse query parameters
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            
            query = InsuranceCompany.query
            
            if active_only:
                query = query.filter(InsuranceCompany.active == True)
            
            companies = query.order_by(InsuranceCompany.name_ar).all()
            
            companies_list = []
            for company in companies:
                companies_list.append({
                    'id': company.id,
                    'name_ar': company.name_ar,
                    'name_en': company.name_en,
                    'claims_email_primary': company.claims_email_primary,
                    'claims_email_cc': company.claims_email_cc,
                    'policy_portal_url': company.policy_portal_url,
                    'notes': company.notes,
                    'active': company.active,
                    'created_at': company.created_at.isoformat()
                })
            
            return {
                'success': True,
                'companies': companies_list,
                'total': len(companies_list)
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching companies: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required()
    @admin_required
    def post(self):
        """Create new insurance company (admin only)"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Validate required fields
            required_fields = ['name_ar', 'name_en', 'claims_email_primary']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400
            
            # Check if company already exists
            existing = InsuranceCompany.query.filter(
                (InsuranceCompany.name_ar == data['name_ar']) |
                (InsuranceCompany.name_en == data['name_en'])
            ).first()
            
            if existing:
                return {'error': 'Company with this name already exists'}, 409
            
            # Create company
            company = InsuranceCompany(
                name_ar=data['name_ar'],
                name_en=data['name_en'],
                claims_email_primary=data['claims_email_primary'],
                claims_email_cc=data.get('claims_email_cc'),
                policy_portal_url=data.get('policy_portal_url'),
                notes=data.get('notes'),
                active=data.get('active', True),
                email_template_ar=data.get('email_template_ar'),
                email_template_en=data.get('email_template_en')
            )
            
            db.session.add(company)
            db.session.commit()
            
            logger.info(f"Insurance company created via API: {company.name_ar}")
            
            return {
                'success': True,
                'company_id': company.id,
                'message': 'Insurance company created successfully'
            }, 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating company: {str(e)}")
            return {'error': 'Internal server error'}, 500

class CompanyResource(Resource):
    """Individual insurance company endpoint"""
    
    @jwt_required()
    def get(self, company_id):
        """Get specific company details"""
        try:
            company = InsuranceCompany.query.get(company_id)
            if not company:
                return {'error': 'Company not found'}, 404
            
            return {
                'success': True,
                'company': {
                    'id': company.id,
                    'name_ar': company.name_ar,
                    'name_en': company.name_en,
                    'claims_email_primary': company.claims_email_primary,
                    'claims_email_cc': company.claims_email_cc,
                    'policy_portal_url': company.policy_portal_url,
                    'notes': company.notes,
                    'active': company.active,
                    'email_template_ar': company.email_template_ar,
                    'email_template_en': company.email_template_en,
                    'created_at': company.created_at.isoformat(),
                    'claims_count': len(company.claims)
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching company {company_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required()
    @admin_required
    def put(self, company_id):
        """Update company (admin only)"""
        try:
            company = InsuranceCompany.query.get(company_id)
            if not company:
                return {'error': 'Company not found'}, 404
            
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Update allowed fields
            updatable_fields = ['name_ar', 'name_en', 'claims_email_primary', 
                              'claims_email_cc', 'policy_portal_url', 'notes', 
                              'active', 'email_template_ar', 'email_template_en']
            
            for field in updatable_fields:
                if field in data:
                    setattr(company, field, data[field])
            
            db.session.commit()
            
            logger.info(f"Insurance company updated via API: {company.name_ar}")
            
            return {
                'success': True,
                'message': 'Company updated successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating company {company_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required()
    @admin_required
    def delete(self, company_id):
        """Delete company (admin only)"""
        try:
            company = InsuranceCompany.query.get(company_id)
            if not company:
                return {'error': 'Company not found'}, 404
            
            # Check if company has claims
            if company.claims:
                return {'error': 'Cannot delete company with existing claims'}, 409
            
            company_name = company.name_ar
            db.session.delete(company)
            db.session.commit()
            
            logger.info(f"Insurance company deleted via API: {company_name}")
            
            return {
                'success': True,
                'message': 'Company deleted successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting company {company_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
