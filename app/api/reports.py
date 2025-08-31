#!/usr/bin/env python3
"""
API endpoints for reports and analytics
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from app.models import Claim, InsuranceCompany, User
from app.api.auth import get_current_user
from app.reports_utils import reports_generator
from app import db
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

class ReportsResource(Resource):
    """Reports endpoint"""
    
    @jwt_required()
    def get(self):
        """Get comprehensive reports"""
        try:
            current_user = get_current_user()
            if not current_user:
                return {'error': 'User not found'}, 401
            
            # Parse query parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            report_type = request.args.get('type', 'overview')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            if report_type == 'overview':
                # Get comprehensive overview
                overview = reports_generator.get_claims_overview(start_date, end_date)
                financial_summary = reports_generator.get_financial_summary(start_date, end_date)
                
                return {
                    'success': True,
                    'report_type': 'overview',
                    'date_range': {
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None
                    },
                    'overview': overview,
                    'financial_summary': financial_summary,
                    'generated_at': datetime.utcnow().isoformat()
                }, 200
                
            elif report_type == 'status':
                # Status distribution report
                query = Claim.query
                if current_user.role != 'admin':
                    query = query.filter(Claim.created_by_user_id == current_user.id)
                
                if start_date:
                    query = query.filter(Claim.created_at >= start_date)
                if end_date:
                    query = query.filter(Claim.created_at <= end_date)
                
                status_counts = db.session.query(
                    Claim.status,
                    func.count(Claim.id).label('count'),
                    func.sum(Claim.claim_amount).label('total_amount')
                ).filter(query.whereclause).group_by(Claim.status).all()
                
                status_data = []
                for status, count, total_amount in status_counts:
                    status_data.append({
                        'status': status,
                        'count': count,
                        'total_amount': float(total_amount or 0),
                        'average_amount': float(total_amount / count) if count > 0 and total_amount else 0
                    })
                
                return {
                    'success': True,
                    'report_type': 'status',
                    'date_range': {
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None
                    },
                    'status_distribution': status_data,
                    'generated_at': datetime.utcnow().isoformat()
                }, 200
                
            elif report_type == 'companies':
                # Companies performance report
                query = db.session.query(
                    InsuranceCompany.id,
                    InsuranceCompany.name_ar,
                    InsuranceCompany.name_en,
                    func.count(Claim.id).label('claims_count'),
                    func.sum(Claim.claim_amount).label('total_amount'),
                    func.avg(Claim.claim_amount).label('average_amount')
                ).outerjoin(Claim)
                
                if current_user.role != 'admin':
                    query = query.filter(Claim.created_by_user_id == current_user.id)
                
                if start_date:
                    query = query.filter(Claim.created_at >= start_date)
                if end_date:
                    query = query.filter(Claim.created_at <= end_date)
                
                company_stats = query.group_by(
                    InsuranceCompany.id, InsuranceCompany.name_ar, InsuranceCompany.name_en
                ).all()
                
                companies_data = []
                for stat in company_stats:
                    companies_data.append({
                        'company_id': stat.id,
                        'name_ar': stat.name_ar,
                        'name_en': stat.name_en,
                        'claims_count': stat.claims_count or 0,
                        'total_amount': float(stat.total_amount or 0),
                        'average_amount': float(stat.average_amount or 0)
                    })
                
                return {
                    'success': True,
                    'report_type': 'companies',
                    'date_range': {
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None
                    },
                    'companies_performance': companies_data,
                    'generated_at': datetime.utcnow().isoformat()
                }, 200
                
            else:
                return {'error': 'Invalid report type. Use: overview, status, or companies'}, 400
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {'error': 'Internal server error'}, 500

class AnalyticsResource(Resource):
    """Advanced analytics endpoint"""
    
    @jwt_required()
    def get(self):
        """Get advanced analytics data"""
        try:
            current_user = get_current_user()
            if not current_user:
                return {'error': 'User not found'}, 401
            
            # Parse query parameters
            period = request.args.get('period', '30')  # days
            metric = request.args.get('metric', 'all')
            
            try:
                days = int(period)
            except ValueError:
                return {'error': 'Invalid period. Must be a number of days'}, 400
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Base query
            query = Claim.query.filter(Claim.created_at >= start_date)
            if current_user.role != 'admin':
                query = query.filter(Claim.created_by_user_id == current_user.id)
            
            if metric == 'all' or metric == 'trends':
                # Daily trends
                daily_stats = db.session.query(
                    func.date(Claim.created_at).label('date'),
                    func.count(Claim.id).label('count'),
                    func.sum(Claim.claim_amount).label('total_amount')
                ).filter(query.whereclause).group_by(
                    func.date(Claim.created_at)
                ).all()
                
                trends_data = []
                for stat in daily_stats:
                    trends_data.append({
                        'date': stat.date.isoformat(),
                        'claims_count': stat.count,
                        'total_amount': float(stat.total_amount or 0)
                    })
            
            if metric == 'all' or metric == 'performance':
                # Performance metrics
                total_claims = query.count()
                total_amount = db.session.query(func.sum(Claim.claim_amount)).filter(query.whereclause).scalar() or 0
                avg_amount = total_amount / total_claims if total_claims > 0 else 0
                
                # Status breakdown
                status_breakdown = db.session.query(
                    Claim.status,
                    func.count(Claim.id).label('count')
                ).filter(query.whereclause).group_by(Claim.status).all()
                
                status_data = {status: count for status, count in status_breakdown}
                
                performance_data = {
                    'total_claims': total_claims,
                    'total_amount': float(total_amount),
                    'average_amount': float(avg_amount),
                    'status_breakdown': status_data
                }
            
            # Prepare response
            response_data = {
                'success': True,
                'period_days': days,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            if metric == 'all':
                response_data['trends'] = trends_data
                response_data['performance'] = performance_data
            elif metric == 'trends':
                response_data['trends'] = trends_data
            elif metric == 'performance':
                response_data['performance'] = performance_data
            else:
                return {'error': 'Invalid metric. Use: all, trends, or performance'}, 400
            
            return response_data, 200
            
        except Exception as e:
            logger.error(f"Error generating analytics: {str(e)}")
            return {'error': 'Internal server error'}, 500
