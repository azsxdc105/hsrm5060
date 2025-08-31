#!/usr/bin/env python3
"""
Full Payments routes implementation
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Payment, Claim
from app.forms import PaymentForm, PaymentSearchForm
from sqlalchemy import func, desc
from datetime import datetime

def admin_required(f):
    """Admin required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('يجب أن تكون مديراً للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

payments_bp = Blueprint('payments', __name__)

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
    
    # Apply filters
    claim_id = request.args.get('claim_id', '').strip()
    payment_method = request.args.get('payment_method', '').strip()
    status = request.args.get('status', '').strip()
    
    if claim_id:
        query = query.filter(Payment.claim_id.ilike(f'%{claim_id}%'))
        form.claim_id.data = claim_id
    
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
        form.payment_method.data = payment_method
    
    if status:
        query = query.filter(Payment.status == status)
        form.status.data = status
    
    # Order by creation date
    query = query.order_by(desc(Payment.created_at))
    
    # Paginate
    payments = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Statistics
    total_payments = Payment.query.count()
    total_amount = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'completed'
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
    
    return render_template('payments/payments_index.html',
                         payments=payments,
                         form=form,
                         stats=stats)

@payments_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_payment():
    """Create new payment"""
    form = PaymentForm()
    
    # Populate claim choices
    claims = Claim.query.all()
    form.claim_id.choices = [(claim.id, f"{claim.client_name} - {claim.id[:8]}...") 
                            for claim in claims]
    
    if form.validate_on_submit():
        payment = Payment(
            claim_id=form.claim_id.data,
            amount=form.amount.data,
            currency=form.currency.data,
            payment_method=form.payment_method.data,
            payment_date=form.payment_date.data,
            payment_reference=form.payment_reference.data,
            bank_name=form.bank_name.data,
            account_number=form.account_number.data,
            iban=form.iban.data,
            check_number=form.check_number.data,
            transaction_id=form.transaction_id.data,
            notes=form.notes.data,
            status=form.status.data,
            created_by_id=current_user.id
        )
        
        try:
            db.session.add(payment)
            db.session.commit()
            flash('تم إنشاء المدفوعة بنجاح', 'success')
            return redirect(url_for('payments.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إنشاء المدفوعة: {str(e)}', 'error')
    
    return render_template('payments/new_payment.html', form=form)

@payments_bp.route('/view/<payment_id>')
@login_required
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
    
    # Populate claim choices
    claims = Claim.query.all()
    form.claim_id.choices = [(claim.id, f"{claim.client_name} - {claim.id[:8]}...") 
                            for claim in claims]
    
    if form.validate_on_submit():
        payment.claim_id = form.claim_id.data
        payment.amount = form.amount.data
        payment.currency = form.currency.data
        payment.payment_method = form.payment_method.data
        payment.payment_date = form.payment_date.data
        payment.payment_reference = form.payment_reference.data
        payment.bank_name = form.bank_name.data
        payment.account_number = form.account_number.data
        payment.iban = form.iban.data
        payment.check_number = form.check_number.data
        payment.transaction_id = form.transaction_id.data
        payment.notes = form.notes.data
        payment.status = form.status.data
        payment.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('تم تحديث المدفوعة بنجاح', 'success')
            return redirect(url_for('payments.view_payment', payment_id=payment.id))
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في تحديث المدفوعة: {str(e)}', 'error')
    
    return render_template('payments/edit.html', form=form, payment=payment)

@payments_bp.route('/delete/<payment_id>', methods=['POST'])
@login_required
@admin_required
def delete_payment(payment_id):
    """Delete payment"""
    payment = Payment.query.get_or_404(payment_id)
    
    try:
        db.session.delete(payment)
        db.session.commit()
        flash('تم حذف المدفوعة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في حذف المدفوعة: {str(e)}', 'error')
    
    return redirect(url_for('payments.index'))
