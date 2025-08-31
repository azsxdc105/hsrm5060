#!/usr/bin/env python3
"""
Advanced Reports and Analytics Routes
"""
from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Claim, User, InsuranceCompany, EmailLog
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, timedelta
import json
import io
import csv
from collections import defaultdict

reports_bp = Blueprint('reports', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@reports_bp.route('/')
@login_required
@admin_required
def index():
    """Advanced Reports Dashboard"""
    return render_template('reports/index.html')

@reports_bp.route('/claims-analytics')
@login_required
@admin_required
def claims_analytics():
    """Claims Analytics Page"""
    return render_template('reports/claims_analytics.html')

@reports_bp.route('/financial-reports')
@login_required
@admin_required
def financial_reports():
    """Financial Reports Page"""
    return render_template('reports/financial_reports.html')

@reports_bp.route('/api/claims-by-status')
@login_required
@admin_required
def api_claims_by_status():
    """API: Claims grouped by status"""
    try:
        # Get date range from query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # Query claims by status
        claims_by_status = db.session.query(
            Claim.status,
            func.count(Claim.id).label('count')
        ).filter(
            Claim.created_at >= start_date
        ).group_by(Claim.status).all()
        
        # Format data for charts
        data = {
            'labels': [],
            'data': [],
            'colors': []
        }
        
        status_colors = {
            'draft': '#6c757d',
            'ready': '#0d6efd', 
            'sent': '#198754',
            'failed': '#dc3545',
            'acknowledged': '#fd7e14',
            'paid': '#20c997'
        }
        
        status_names = {
            'draft': 'مسودة',
            'ready': 'جاهز',
            'sent': 'مرسل', 
            'failed': 'فشل',
            'acknowledged': 'مستلم',
            'paid': 'مدفوع'
        }
        
        for status, count in claims_by_status:
            data['labels'].append(status_names.get(status, status))
            data['data'].append(count)
            data['colors'].append(status_colors.get(status, '#6c757d'))
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/api/claims-by-company')
@login_required
@admin_required
def api_claims_by_company():
    """API: Claims grouped by company"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        claims_by_company = db.session.query(
            InsuranceCompany.name_ar.label('name'),
            func.count(Claim.id).label('count'),
            func.sum(Claim.claim_amount).label('total_amount')
        ).join(
            Claim, InsuranceCompany.id == Claim.company_id
        ).filter(
            Claim.created_at >= start_date
        ).group_by(InsuranceCompany.name_ar).all()
        
        data = {
            'labels': [],
            'claims_count': [],
            'total_amounts': []
        }
        
        for company_name, count, total_amount in claims_by_company:
            data['labels'].append(company_name)
            data['claims_count'].append(count)
            data['total_amounts'].append(float(total_amount or 0))
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/api/claims-timeline')
@login_required
@admin_required
def api_claims_timeline():
    """API: Claims timeline data"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # Group claims by date
        claims_timeline = db.session.query(
            func.date(Claim.created_at).label('date'),
            func.count(Claim.id).label('count'),
            func.sum(Claim.claim_amount).label('total_amount')
        ).filter(
            Claim.created_at >= start_date
        ).group_by(
            func.date(Claim.created_at)
        ).order_by('date').all()
        
        data = {
            'labels': [],
            'claims_count': [],
            'total_amounts': []
        }
        
        for date, count, total_amount in claims_timeline:
            data['labels'].append(date.strftime('%Y-%m-%d'))
            data['claims_count'].append(count)
            data['total_amounts'].append(float(total_amount or 0))
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/api/monthly-summary')
@login_required
@admin_required
def api_monthly_summary():
    """API: Monthly summary statistics"""
    try:
        # Current month
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Previous month
        if now.month == 1:
            prev_month_start = current_month_start.replace(year=now.year-1, month=12)
        else:
            prev_month_start = current_month_start.replace(month=now.month-1)
        
        # Current month stats
        current_stats = db.session.query(
            func.count(Claim.id).label('total_claims'),
            func.sum(Claim.claim_amount).label('total_amount'),
            func.count(Claim.id).filter(Claim.status == 'sent').label('sent_claims'),
            func.count(Claim.id).filter(Claim.status == 'paid').label('paid_claims')
        ).filter(
            Claim.created_at >= current_month_start
        ).first()
        
        # Previous month stats
        prev_stats = db.session.query(
            func.count(Claim.id).label('total_claims'),
            func.sum(Claim.claim_amount).label('total_amount'),
            func.count(Claim.id).filter(Claim.status == 'sent').label('sent_claims'),
            func.count(Claim.id).filter(Claim.status == 'paid').label('paid_claims')
        ).filter(
            and_(
                Claim.created_at >= prev_month_start,
                Claim.created_at < current_month_start
            )
        ).first()
        
        # Calculate growth percentages
        def calculate_growth(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return ((current - previous) / previous) * 100
        
        data = {
            'current_month': {
                'total_claims': current_stats.total_claims or 0,
                'total_amount': float(current_stats.total_amount or 0),
                'sent_claims': current_stats.sent_claims or 0,
                'paid_claims': current_stats.paid_claims or 0
            },
            'previous_month': {
                'total_claims': prev_stats.total_claims or 0,
                'total_amount': float(prev_stats.total_amount or 0),
                'sent_claims': prev_stats.sent_claims or 0,
                'paid_claims': prev_stats.paid_claims or 0
            },
            'growth': {
                'total_claims': calculate_growth(
                    current_stats.total_claims or 0,
                    prev_stats.total_claims or 0
                ),
                'total_amount': calculate_growth(
                    float(current_stats.total_amount or 0),
                    float(prev_stats.total_amount or 0)
                ),
                'sent_claims': calculate_growth(
                    current_stats.sent_claims or 0,
                    prev_stats.sent_claims or 0
                ),
                'paid_claims': calculate_growth(
                    current_stats.paid_claims or 0,
                    prev_stats.paid_claims or 0
                )
            }
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/api/top-cities')
@login_required
@admin_required
def api_top_cities():
    """API: Top cities by claims count"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        top_cities = db.session.query(
            Claim.city,
            func.count(Claim.id).label('count'),
            func.sum(Claim.claim_amount).label('total_amount')
        ).filter(
            and_(
                Claim.created_at >= start_date,
                Claim.city.isnot(None),
                Claim.city != ''
            )
        ).group_by(Claim.city).order_by(
            func.count(Claim.id).desc()
        ).limit(10).all()
        
        data = {
            'labels': [],
            'claims_count': [],
            'total_amounts': []
        }
        
        for city, count, total_amount in top_cities:
            data['labels'].append(city)
            data['claims_count'].append(count)
            data['total_amounts'].append(float(total_amount or 0))
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/export/claims-csv')
@login_required
@admin_required
def export_claims_csv():
    """Export claims data as CSV"""
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # Query claims
        claims = db.session.query(Claim).filter(
            Claim.created_at >= start_date
        ).order_by(Claim.created_at.desc()).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Client Name', 'National ID', 'Policy Number',
            'Company', 'Claim Amount', 'Status', 'City',
            'Created At', 'Updated At'
        ])
        
        # Write data
        for claim in claims:
            writer.writerow([
                claim.id,
                claim.client_name,
                claim.client_national_id,
                claim.policy_number,
                claim.company.name_ar if claim.company else '',
                claim.claim_amount,
                claim.status,
                claim.city,
                claim.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                claim.updated_at.strftime('%Y-%m-%d %H:%M:%S') if claim.updated_at else ''
            ])
        
        # Create file-like object
        output.seek(0)
        file_data = io.BytesIO()
        file_data.write(output.getvalue().encode('utf-8-sig'))  # UTF-8 with BOM for Excel
        file_data.seek(0)
        
        return send_file(
            file_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'claims_report_{datetime.now().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/api/performance-metrics')
@login_required
@admin_required
def api_performance_metrics():
    """Get performance metrics for the system"""
    try:
        now = datetime.now()

        # Processing time metrics
        processing_times = db.session.query(
            func.avg(
                func.julianday(Claim.sent_at) - func.julianday(Claim.created_at)
            ).label('avg_processing_days')
        ).filter(
            Claim.sent_at.isnot(None),
            Claim.created_at >= now - timedelta(days=30)
        ).first()

        # Success rate by company
        company_success_rates = db.session.query(
            InsuranceCompany.name_ar.label('company'),
            func.count(Claim.id).label('total_claims'),
            func.sum(func.case([(Claim.status == 'sent', 1)], else_=0)).label('successful_claims')
        ).join(
            Claim, InsuranceCompany.id == Claim.company_id
        ).filter(
            Claim.created_at >= now - timedelta(days=30)
        ).group_by(InsuranceCompany.name_ar).all()

        return jsonify({
            'processing_time': {
                'avg_days': float(processing_times.avg_processing_days or 0)
            },
            'company_success_rates': [
                {
                    'company': rate.company,
                    'total_claims': rate.total_claims,
                    'successful_claims': rate.successful_claims,
                    'success_rate': (rate.successful_claims / rate.total_claims * 100) if rate.total_claims > 0 else 0
                }
                for rate in company_success_rates
            ]
        })

    except Exception as e:
        current_app.logger.error(f"Failed to get performance metrics: {e}")
        return jsonify({'error': 'Failed to get metrics'}), 500

@reports_bp.route('/advanced')
@login_required
@admin_required
def advanced_reports():
    """Advanced reports page"""
    return render_template('reports/advanced.html')
