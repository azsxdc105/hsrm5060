from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from app import db
from app.models import Claim, InsuranceCompany, User, EmailLog
from app.forms import SearchForm
from sqlalchemy import func, desc
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_claims = Claim.query.count()
    sent_claims = Claim.query.filter_by(status='sent').count()
    failed_claims = Claim.query.filter_by(status='failed').count()
    draft_claims = Claim.query.filter_by(status='draft').count()
    
    # Get recent claims
    recent_claims = Claim.query.order_by(desc(Claim.created_at)).limit(10).all()
    
    # Get claims by company
    company_stats = db.session.query(
        InsuranceCompany.name_ar,
        func.count(Claim.id).label('count')
    ).outerjoin(Claim).group_by(InsuranceCompany.id, InsuranceCompany.name_ar).all()
    
    # Get monthly statistics
    current_month = datetime.now().replace(day=1)
    monthly_claims = Claim.query.filter(Claim.created_at >= current_month).count()
    
    stats = {
        'total_claims': total_claims,
        'sent_claims': sent_claims,
        'failed_claims': failed_claims,
        'draft_claims': draft_claims,
        'monthly_claims': monthly_claims,
        'success_rate': round((sent_claims / total_claims * 100) if total_claims > 0 else 0, 1)
    }
    
    return render_template('main/dashboard.html', 
                         stats=stats,
                         recent_claims=recent_claims,
                         company_stats=company_stats)

@main_bp.route('/claims')
@login_required
def claims_list():
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = Claim.query
    
    # Apply filters
    if form.search_term.data:
        search_term = f"%{form.search_term.data}%"
        query = query.filter(
            (Claim.client_name.ilike(search_term)) |
            (Claim.client_national_id.ilike(search_term)) |
            (Claim.incident_number.ilike(search_term)) |
            (Claim.policy_number.ilike(search_term))
        )
    
    if form.company_id.data:
        query = query.filter(Claim.company_id == form.company_id.data)
    
    if form.status.data:
        query = query.filter(Claim.status == form.status.data)
    
    if form.date_from.data:
        query = query.filter(Claim.created_at >= form.date_from.data)
    
    if form.date_to.data:
        query = query.filter(Claim.created_at <= form.date_to.data)
    
    # Execute query with pagination
    claims = query.order_by(desc(Claim.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('main/claims_list.html', claims=claims, form=form)

@main_bp.route('/profile')
@login_required
def profile():
    return render_template('main/profile.html', user=current_user)

@main_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    # Get claims by status
    status_stats = db.session.query(
        Claim.status,
        func.count(Claim.id).label('count')
    ).group_by(Claim.status).all()
    
    # Get daily claims for the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    daily_stats = db.session.query(
        func.date(Claim.created_at).label('date'),
        func.count(Claim.id).label('count')
    ).filter(
        Claim.created_at >= thirty_days_ago
    ).group_by(func.date(Claim.created_at)).all()
    
    return jsonify({
        'status_stats': [{'status': s[0], 'count': s[1]} for s in status_stats],
        'daily_stats': [{'date': str(s[0]), 'count': s[1]} for s in daily_stats]
    })