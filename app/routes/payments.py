#!/usr/bin/env python3
"""
Payment management routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Payment, Claim, User
from app.forms import PaymentForm, PaymentSearchForm
from app.audit_utils import AuditLogger
from sqlalchemy import desc, func, and_, or_, extract
from datetime import datetime, date, timedelta
import uuid

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

def admin_required(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('يجب أن تكون مديراً للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@payments_bp.route('/')
@login_required
@admin_required
def index():
    """List all payments"""
    form = PaymentSearchForm()
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Build query
    query = Payment.query
    
    # Apply filters from URL parameters
    claim_id = request.args.get('claim_id', '').strip()
    payment_method = request.args.get('payment_method', '').strip()
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    amount_from = request.args.get('amount_from', '').strip()
    amount_to = request.args.get('amount_to', '').strip()
    
    if claim_id:
        query = query.filter(Payment.claim_id.ilike(f'%{claim_id}%'))
        form.claim_id.data = claim_id
    
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
        form.payment_method.data = payment_method
    
    if status:
        query = query.filter(Payment.status == status)
        form.status.data = status
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Payment.payment_date >= date_from_obj)
            form.date_from.data = date_from_obj
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Payment.payment_date <= date_to_obj)
            form.date_to.data = date_to_obj
        except ValueError:
            pass
    
    if amount_from:
        try:
            amount_from_val = float(amount_from)
            query = query.filter(Payment.amount >= amount_from_val)
            form.amount_from.data = amount_from_val
        except ValueError:
            pass
    
    if amount_to:
        try:
            amount_to_val = float(amount_to)
            query = query.filter(Payment.amount <= amount_to_val)
            form.amount_to.data = amount_to_val
        except ValueError:
            pass
    
    # Execute query with pagination
    payments = query.order_by(desc(Payment.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get summary statistics
    total_payments = Payment.query.count()
    total_amount = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'received'
    ).scalar() or 0
    
    pending_payments = Payment.query.filter_by(status='pending').count()
    pending_amount = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'pending'
    ).scalar() or 0
    
    stats = {
        'total_payments': total_payments,
        'total_amount': float(total_amount),
        'pending_payments': pending_payments,
        'pending_amount': float(pending_amount)
    }
    
    return render_template('payments/index.html', 
                         payments=payments, 
                         form=form, 
                         stats=stats)

@payments_bp.route('/new/<claim_id>')
@login_required
@admin_required
def new_payment(claim_id):
    """Create new payment for a claim"""
    claim = Claim.query.get_or_404(claim_id)
    form = PaymentForm()
    
    # Pre-fill amount with claim amount
    form.amount.data = claim.claim_amount
    form.currency.data = claim.currency
    form.payment_date.data = date.today()
    
    if form.validate_on_submit():
        payment = Payment(
            id=str(uuid.uuid4()),
            claim_id=claim_id,
            amount=form.amount.data,
            currency=form.currency.data,
            payment_method=form.payment_method.data,
            payment_reference=form.payment_reference.data,
            payment_date=form.payment_date.data,
            received_date=form.received_date.data,
            status=form.status.data,
            bank_name=form.bank_name.data,
            account_number=form.account_number.data,
            iban=form.iban.data,
            check_number=form.check_number.data,
            check_bank=form.check_bank.data,
            transaction_id=form.transaction_id.data,
            notes=form.notes.data,
            created_by_user_id=current_user.id
        )
        
        db.session.add(payment)
        
        # Update claim status if payment is received
        if form.status.data == 'received':
            claim.status = 'paid'
            AuditLogger.log_user_action(
                action='STATUS_CHANGE',
                resource_type='claim',
                resource_id=claim_id,
                old_values={'status': 'acknowledged'},
                new_values={'status': 'paid'},
                details=f"Claim marked as paid due to payment receipt"
            )
        
        db.session.commit()
        
        # Log payment creation
        AuditLogger.log_user_action(
            action='CREATE',
            resource_type='payment',
            resource_id=payment.id,
            new_values=payment.to_dict(),
            details=f"Created payment of {payment.amount} {payment.currency} for claim {claim_id}"
        )
        
        flash('تم إضافة الدفعة بنجاح', 'success')
        return redirect(url_for('payments.view_payment', payment_id=payment.id))
    
    return render_template('payments/new.html', form=form, claim=claim)

@payments_bp.route('/view/<payment_id>')
@login_required
@admin_required
def view_payment(payment_id):
    """View payment details"""
    payment = Payment.query.get_or_404(payment_id)
    return render_template('payments/view.html', payment=payment)

@payments_bp.route('/edit/<payment_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_payment(payment_id):
    """Edit payment"""
    payment = Payment.query.get_or_404(payment_id)
    form = PaymentForm(obj=payment)
    
    if form.validate_on_submit():
        # Store old values for audit
        old_values = payment.to_dict()
        
        # Update payment
        form.populate_obj(payment)
        payment.updated_at = datetime.utcnow()
        
        # Update claim status based on payment status
        if form.status.data == 'received' and payment.claim.status != 'paid':
            payment.claim.status = 'paid'
        elif form.status.data != 'received' and payment.claim.status == 'paid':
            # Check if there are other received payments for this claim
            other_received = Payment.query.filter(
                and_(Payment.claim_id == payment.claim_id,
                     Payment.id != payment_id,
                     Payment.status == 'received')
            ).count()
            if other_received == 0:
                payment.claim.status = 'acknowledged'
        
        db.session.commit()
        
        # Log payment update
        AuditLogger.log_user_action(
            action='UPDATE',
            resource_type='payment',
            resource_id=payment_id,
            old_values=old_values,
            new_values=payment.to_dict(),
            details=f"Updated payment {payment_id}"
        )
        
        flash('تم تحديث الدفعة بنجاح', 'success')
        return redirect(url_for('payments.view_payment', payment_id=payment_id))
    
    return render_template('payments/edit.html', form=form, payment=payment)

@payments_bp.route('/delete/<payment_id>', methods=['POST'])
@login_required
@admin_required
def delete_payment(payment_id):
    """Delete payment"""
    payment = Payment.query.get_or_404(payment_id)
    claim_id = payment.claim_id
    payment_info = f"{payment.amount} {payment.currency}"
    
    # Check if this was the only received payment for the claim
    if payment.status == 'received':
        other_received = Payment.query.filter(
            and_(Payment.claim_id == claim_id,
                 Payment.id != payment_id,
                 Payment.status == 'received')
        ).count()
        if other_received == 0:
            # Revert claim status
            claim = Claim.query.get(claim_id)
            if claim and claim.status == 'paid':
                claim.status = 'acknowledged'
    
    db.session.delete(payment)
    db.session.commit()
    
    # Log payment deletion
    AuditLogger.log_user_action(
        action='DELETE',
        resource_type='payment',
        resource_id=payment_id,
        details=f"Deleted payment {payment_info} for claim {claim_id}"
    )
    
    flash('تم حذف الدفعة بنجاح', 'success')
    return redirect(url_for('payments.index'))

@payments_bp.route('/api/claim/<claim_id>/payments')
@login_required
def api_claim_payments(claim_id):
    """API endpoint to get payments for a claim"""
    payments = Payment.query.filter_by(claim_id=claim_id).order_by(desc(Payment.created_at)).all()
    return jsonify([payment.to_dict() for payment in payments])

@payments_bp.route('/api/stats')
@login_required
@admin_required
def api_payment_stats():
    """API endpoint for payment statistics"""
    # Payment status distribution
    status_stats = db.session.query(
        Payment.status,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total_amount')
    ).group_by(Payment.status).all()
    
    # Payment method distribution
    method_stats = db.session.query(
        Payment.payment_method,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total_amount')
    ).group_by(Payment.payment_method).all()
    
    # Monthly payment trends (last 12 months)
    from sqlalchemy import extract
    monthly_stats = db.session.query(
        extract('year', Payment.payment_date).label('year'),
        extract('month', Payment.payment_date).label('month'),
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total_amount')
    ).filter(
        Payment.payment_date >= datetime.now().replace(day=1, month=1) - timedelta(days=365)
    ).group_by(
        extract('year', Payment.payment_date),
        extract('month', Payment.payment_date)
    ).order_by(
        extract('year', Payment.payment_date),
        extract('month', Payment.payment_date)
    ).all()
    
    return jsonify({
        'status_stats': [
            {
                'status': stat.status,
                'count': stat.count,
                'total_amount': float(stat.total_amount or 0)
            } for stat in status_stats
        ],
        'method_stats': [
            {
                'method': stat.payment_method,
                'count': stat.count,
                'total_amount': float(stat.total_amount or 0)
            } for stat in method_stats
        ],
        'monthly_stats': [
            {
                'year': int(stat.year),
                'month': int(stat.month),
                'count': stat.count,
                'total_amount': float(stat.total_amount or 0)
            } for stat in monthly_stats
        ]
    })
