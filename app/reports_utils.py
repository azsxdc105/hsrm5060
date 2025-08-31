#!/usr/bin/env python3
"""
Advanced reporting and analytics utilities
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
from datetime import datetime, timedelta
from sqlalchemy import func, extract, and_
from app import db
from app.models import Claim, InsuranceCompany, EmailLog, User
from decimal import Decimal

class ReportsGenerator:
    """Generate advanced reports and analytics"""
    
    def __init__(self):
        pass
    
    def get_claims_overview(self, start_date=None, end_date=None):
        """Get comprehensive claims overview"""
        query = Claim.query
        
        if start_date:
            query = query.filter(Claim.created_at >= start_date)
        if end_date:
            query = query.filter(Claim.created_at <= end_date)
        
        claims = query.all()
        
        # Basic statistics
        total_claims = len(claims)
        total_amount = sum(float(claim.claim_amount) for claim in claims)
        avg_amount = total_amount / total_claims if total_claims > 0 else 0
        
        # Status distribution
        status_counts = {}
        for claim in claims:
            status_counts[claim.status] = status_counts.get(claim.status, 0) + 1
        
        # Company distribution
        company_stats = {}
        for claim in claims:
            company_name = claim.insurance_company.name_ar
            if company_name not in company_stats:
                company_stats[company_name] = {'count': 0, 'amount': 0}
            company_stats[company_name]['count'] += 1
            company_stats[company_name]['amount'] += float(claim.claim_amount)
        
        return {
            'total_claims': total_claims,
            'total_amount': total_amount,
            'average_amount': avg_amount,
            'status_distribution': status_counts,
            'company_distribution': company_stats
        }
    
    def generate_claims_trend_chart(self, days=30):
        """Generate claims trend chart for the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query claims by day
        daily_claims = db.session.query(
            func.date(Claim.created_at).label('date'),
            func.count(Claim.id).label('count'),
            func.sum(Claim.claim_amount).label('total_amount')
        ).filter(
            Claim.created_at >= start_date
        ).group_by(
            func.date(Claim.created_at)
        ).all()
        
        # Prepare data
        dates = []
        counts = []
        amounts = []
        
        for record in daily_claims:
            dates.append(record.date)
            counts.append(record.count)
            amounts.append(float(record.total_amount or 0))
        
        # Create chart
        fig = go.Figure()
        
        # Add claims count
        fig.add_trace(go.Scatter(
            x=dates,
            y=counts,
            mode='lines+markers',
            name='عدد المطالبات',
            line=dict(color='#007bff'),
            yaxis='y'
        ))
        
        # Add total amount on secondary y-axis
        fig.add_trace(go.Scatter(
            x=dates,
            y=amounts,
            mode='lines+markers',
            name='إجمالي المبلغ (ريال)',
            line=dict(color='#28a745'),
            yaxis='y2'
        ))
        
        # Update layout
        fig.update_layout(
            title=f'اتجاه المطالبات - آخر {days} يوم',
            xaxis_title='التاريخ',
            yaxis=dict(
                title='عدد المطالبات',
                side='left'
            ),
            yaxis2=dict(
                title='إجمالي المبلغ (ريال)',
                side='right',
                overlaying='y'
            ),
            hovermode='x unified',
            font=dict(family="Arial", size=12),
            height=400
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def generate_status_distribution_chart(self):
        """Generate claims status distribution pie chart"""
        status_counts = db.session.query(
            Claim.status,
            func.count(Claim.id).label('count')
        ).group_by(Claim.status).all()
        
        # Arabic status labels
        status_labels = {
            'draft': 'مسودة',
            'ready': 'جاهز',
            'sent': 'مرسل',
            'failed': 'فشل',
            'acknowledged': 'مستلم',
            'paid': 'مدفوع'
        }
        
        labels = [status_labels.get(record.status, record.status) for record in status_counts]
        values = [record.count for record in status_counts]
        
        colors = ['#ffc107', '#17a2b8', '#28a745', '#dc3545', '#6f42c1', '#20c997']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=colors
        )])
        
        fig.update_layout(
            title='توزيع المطالبات حسب الحالة',
            font=dict(family="Arial", size=12),
            height=400
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def generate_company_performance_chart(self):
        """Generate insurance company performance chart"""
        company_stats = db.session.query(
            InsuranceCompany.name_ar,
            func.count(Claim.id).label('claim_count'),
            func.sum(Claim.claim_amount).label('total_amount'),
            func.avg(Claim.claim_amount).label('avg_amount')
        ).join(Claim).group_by(InsuranceCompany.id).all()
        
        companies = [record.name_ar for record in company_stats]
        claim_counts = [record.claim_count for record in company_stats]
        total_amounts = [float(record.total_amount or 0) for record in company_stats]
        
        fig = go.Figure()
        
        # Add bar chart for claim counts
        fig.add_trace(go.Bar(
            x=companies,
            y=claim_counts,
            name='عدد المطالبات',
            marker_color='#007bff',
            yaxis='y'
        ))
        
        # Add line chart for total amounts
        fig.add_trace(go.Scatter(
            x=companies,
            y=total_amounts,
            mode='lines+markers',
            name='إجمالي المبلغ (ريال)',
            line=dict(color='#28a745'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='أداء شركات التأمين',
            xaxis_title='شركة التأمين',
            yaxis=dict(
                title='عدد المطالبات',
                side='left'
            ),
            yaxis2=dict(
                title='إجمالي المبلغ (ريال)',
                side='right',
                overlaying='y'
            ),
            height=500,
            font=dict(family="Arial", size=12)
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def generate_monthly_summary_chart(self, year=None):
        """Generate monthly summary chart"""
        if not year:
            year = datetime.now().year
        
        monthly_data = db.session.query(
            extract('month', Claim.created_at).label('month'),
            func.count(Claim.id).label('count'),
            func.sum(Claim.claim_amount).label('total_amount')
        ).filter(
            extract('year', Claim.created_at) == year
        ).group_by(
            extract('month', Claim.created_at)
        ).all()
        
        # Arabic month names
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }
        
        months = [month_names[int(record.month)] for record in monthly_data]
        counts = [record.count for record in monthly_data]
        amounts = [float(record.total_amount or 0) for record in monthly_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=months,
            y=counts,
            name='عدد المطالبات',
            marker_color='#17a2b8',
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=amounts,
            mode='lines+markers',
            name='إجمالي المبلغ (ريال)',
            line=dict(color='#ffc107', width=3),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=f'الملخص الشهري - {year}',
            xaxis_title='الشهر',
            yaxis=dict(
                title='عدد المطالبات',
                side='left'
            ),
            yaxis2=dict(
                title='إجمالي المبلغ (ريال)',
                side='right',
                overlaying='y'
            ),
            height=400,
            font=dict(family="Arial", size=12)
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def get_financial_summary(self, start_date=None, end_date=None):
        """Get detailed financial summary"""
        query = Claim.query
        
        if start_date:
            query = query.filter(Claim.created_at >= start_date)
        if end_date:
            query = query.filter(Claim.created_at <= end_date)
        
        claims = query.all()
        
        # Financial metrics
        total_claims_value = sum(float(claim.claim_amount) for claim in claims)
        paid_claims = [claim for claim in claims if claim.status == 'paid']
        total_paid = sum(float(claim.claim_amount) for claim in paid_claims)
        pending_claims = [claim for claim in claims if claim.status in ['sent', 'acknowledged']]
        total_pending = sum(float(claim.claim_amount) for claim in pending_claims)
        
        # Coverage type breakdown
        coverage_breakdown = {}
        for claim in claims:
            coverage = claim.coverage_type
            if coverage not in coverage_breakdown:
                coverage_breakdown[coverage] = {'count': 0, 'amount': 0}
            coverage_breakdown[coverage]['count'] += 1
            coverage_breakdown[coverage]['amount'] += float(claim.claim_amount)
        
        return {
            'total_claims_value': total_claims_value,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'payment_rate': (total_paid / total_claims_value * 100) if total_claims_value > 0 else 0,
            'coverage_breakdown': coverage_breakdown,
            'average_claim_value': total_claims_value / len(claims) if claims else 0
        }

# Global instance
reports_generator = ReportsGenerator()

def get_dashboard_charts():
    """Get all dashboard charts"""
    return {
        'claims_trend': reports_generator.generate_claims_trend_chart(),
        'status_distribution': reports_generator.generate_status_distribution_chart(),
        'company_performance': reports_generator.generate_company_performance_chart(),
        'monthly_summary': reports_generator.generate_monthly_summary_chart()
    }
