from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from app import db
from app.models import Claim, InsuranceCompany, User, EmailLog
from app.forms import SearchForm
from app.export_utils import export_claims_excel, export_claims_pdf
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import os

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

@main_bp.route('/employee')
@login_required
def employee_dashboard():
    """Employee dashboard"""
    from app.models import Claim, InsuranceCompany, User
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Get statistics
    total_claims = Claim.query.count()
    pending_claims = Claim.query.filter_by(status='pending').count()
    approved_claims = Claim.query.filter_by(status='approved').count()
    rejected_claims = Claim.query.filter_by(status='rejected').count()
    sent_claims = Claim.query.filter_by(status='sent').count()
    failed_claims = Claim.query.filter_by(status='failed').count()
    draft_claims = Claim.query.filter_by(status='draft').count()

    # Get recent claims (last 5 for employees)
    recent_claims = Claim.query.order_by(Claim.created_at.desc()).limit(5).all()

    # Get today's claims
    today = datetime.now().date()
    today_claims = Claim.query.filter(func.date(Claim.created_at) == today).count()

    # Get this week's claims
    week_ago = datetime.now() - timedelta(days=7)
    this_week_claims = Claim.query.filter(Claim.created_at >= week_ago).count()

    # Get companies count
    companies_count = InsuranceCompany.query.count()

    # Calculate average processing time (mock data for now)
    avg_processing_time = 3  # days

    stats = {
        'total_claims': total_claims,
        'pending_claims': pending_claims,
        'approved_claims': approved_claims,
        'rejected_claims': rejected_claims,
        'sent_claims': sent_claims,
        'failed_claims': failed_claims,
        'draft_claims': draft_claims,
        'today_claims': today_claims,
        'this_week_claims': this_week_claims,
        'companies_count': companies_count,
        'avg_processing_time': avg_processing_time
    }

    # Get current date
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')

    return render_template('employee/dashboard.html',
                         stats=stats,
                         recent_claims=recent_claims,
                         current_date=current_date)

@main_bp.route('/claims')
@login_required
def claims_list():
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Build query
    query = Claim.query

    # Apply filters from URL parameters (for GET requests)
    search_term = request.args.get('search_term', '').strip()
    company_id = request.args.get('company_id', '').strip()
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    # Apply search term filter
    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.filter(
            (Claim.client_name.ilike(search_pattern)) |
            (Claim.client_national_id.ilike(search_pattern)) |
            (Claim.incident_number.ilike(search_pattern)) |
            (Claim.policy_number.ilike(search_pattern))
        )
        form.search_term.data = search_term

    # Apply company filter
    if company_id and company_id.isdigit():
        query = query.filter(Claim.company_id == int(company_id))
        form.company_id.data = company_id

    # Apply status filter
    if status:
        query = query.filter(Claim.status == status)
        form.status.data = status

    # Apply date filters
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Claim.created_at >= date_from_obj)
            form.date_from.data = date_from_obj
        except ValueError:
            pass

    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Claim.created_at <= date_to_obj)
            form.date_to.data = date_to_obj
        except ValueError:
            pass

    # Execute query with pagination
    claims = query.order_by(desc(Claim.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('main/claims_list.html', claims=claims, form=form)

@main_bp.route('/export/claims/<format>')
@login_required
def export_claims_data(format):
    """Export claims data for current user"""
    try:
        # Get current user's claims or all claims for admin
        if current_user.role == 'admin':
            query = Claim.query
        else:
            query = Claim.query.filter_by(created_by_user_id=current_user.id)

        # Apply same filters as claims list
        search_term = request.args.get('search_term', '').strip()
        company_id = request.args.get('company_id', '').strip()
        status = request.args.get('status', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (Claim.client_name.ilike(search_pattern)) |
                (Claim.client_national_id.ilike(search_pattern)) |
                (Claim.incident_number.ilike(search_pattern)) |
                (Claim.policy_number.ilike(search_pattern))
            )

        if company_id and company_id.isdigit():
            query = query.filter(Claim.company_id == int(company_id))

        if status:
            query = query.filter(Claim.status == status)

        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(Claim.created_at >= date_from_obj)
            except ValueError:
                pass

        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(Claim.created_at <= date_to_obj)
            except ValueError:
                pass

        claims = query.order_by(desc(Claim.created_at)).all()

        if not claims:
            flash('لا توجد مطالبات للتصدير', 'warning')
            return redirect(url_for('main.claims_list'))

        # Export based on format
        if format.lower() == 'excel':
            filepath = export_claims_excel(claims)
            filename = os.path.basename(filepath)

            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        elif format.lower() == 'pdf':
            filepath = export_claims_pdf(claims)
            filename = os.path.basename(filepath)

            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )

        else:
            flash('صيغة التصدير غير مدعومة', 'error')
            return redirect(url_for('main.claims_list'))

    except Exception as e:
        flash(f'خطأ في تصدير البيانات: {str(e)}', 'error')
        return redirect(url_for('main.claims_list'))

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