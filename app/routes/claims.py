from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Claim, ClaimAttachment, InsuranceCompany
from app.forms import ClaimForm, EditClaimForm
from app.email_utils import send_claim_email
import os
import uuid
from datetime import datetime
import zipfile
import io
import mimetypes

claims_bp = Blueprint('claims', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file, claim_id):
    """Save uploaded file and return attachment object"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create claim folder
        claim_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], claim_id)
        os.makedirs(claim_folder, exist_ok=True)
        
        # Save file
        file_path = os.path.join(claim_folder, unique_filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        mime_type = mimetypes.guess_type(file_path)[0]
        
        # Create attachment record
        attachment = ClaimAttachment(
            claim_id=claim_id,
            original_filename=filename,
            stored_filename=unique_filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_path=file_path
        )
        
        return attachment
    return None

@claims_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_claim():
    form = ClaimForm()
    
    if form.validate_on_submit():
        # Create claim
        claim = Claim(
            company_id=form.company_id.data,
            client_name=form.client_name.data,
            client_national_id=form.client_national_id.data,
            policy_number=form.policy_number.data,
            incident_number=form.incident_number.data,
            incident_date=form.incident_date.data,
            claim_amount=form.claim_amount.data,
            coverage_type=form.coverage_type.data,
            claim_details=form.claim_details.data,
            city=form.city.data,
            tags=form.tags.data,
            created_by_user_id=current_user.id,
            status='draft'
        )
        
        db.session.add(claim)
        db.session.flush()  # Get the claim ID
        
        # Handle file uploads
        attachments = []
        if form.files.data:
            for file in form.files.data:
                if file and file.filename:
                    attachment = save_uploaded_file(file, claim.id)
                    if attachment:
                        attachments.append(attachment)
                        db.session.add(attachment)
        
        db.session.commit()
        
        flash(f'تم إنشاء المطالبة بنجاح. رقم المطالبة: {claim.id}', 'success')
        return redirect(url_for('claims.view_claim', claim_id=claim.id))
    
    return render_template('claims/new_claim.html', form=form)

@claims_bp.route('/<claim_id>')
@login_required
def view_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    return render_template('claims/view_claim.html', claim=claim)

@claims_bp.route('/<claim_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    form = EditClaimForm(obj=claim)
    
    if form.validate_on_submit():
        # Update claim
        form.populate_obj(claim)
        claim.updated_at = datetime.utcnow()
        
        # Handle new file uploads
        if form.files.data:
            for file in form.files.data:
                if file and file.filename:
                    attachment = save_uploaded_file(file, claim.id)
                    if attachment:
                        db.session.add(attachment)
        
        db.session.commit()
        flash('تم تحديث المطالبة بنجاح', 'success')
        return redirect(url_for('claims.view_claim', claim_id=claim.id))
    
    return render_template('claims/edit_claim.html', form=form, claim=claim)

@claims_bp.route('/<claim_id>/send', methods=['POST'])
@login_required
def send_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    
    if claim.status in ['sent', 'acknowledged', 'paid']:
        flash('لا يمكن إرسال مطالبة مرسلة مسبقاً', 'warning')
        return redirect(url_for('claims.view_claim', claim_id=claim.id))
    
    # Send email
    success, message = send_claim_email(claim, claim.attachments)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('claims.view_claim', claim_id=claim.id))

@claims_bp.route('/<claim_id>/resend', methods=['POST'])
@login_required
def resend_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    
    # Reset status to ready
    claim.status = 'ready'
    db.session.commit()
    
    # Send email
    success, message = send_claim_email(claim, claim.attachments)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('claims.view_claim', claim_id=claim.id))

@claims_bp.route('/<claim_id>/delete', methods=['POST'])
@login_required
def delete_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    
    # Delete attachments from filesystem
    for attachment in claim.attachments:
        try:
            if os.path.exists(attachment.storage_path):
                os.remove(attachment.storage_path)
        except:
            pass
    
    # Delete claim folder
    claim_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], claim_id)
    try:
        if os.path.exists(claim_folder):
            os.rmdir(claim_folder)
    except:
        pass
    
    db.session.delete(claim)
    db.session.commit()
    
    flash('تم حذف المطالبة بنجاح', 'success')
    return redirect(url_for('main.claims_list'))

@claims_bp.route('/<claim_id>/attachments/<int:attachment_id>')
@login_required
def download_attachment(claim_id, attachment_id):
    claim = Claim.query.get_or_404(claim_id)
    attachment = ClaimAttachment.query.get_or_404(attachment_id)
    
    if attachment.claim_id != claim_id:
        flash('غير مسموح بالوصول إلى هذا المرفق', 'error')
        return redirect(url_for('claims.view_claim', claim_id=claim_id))
    
    return send_file(attachment.storage_path, as_attachment=True, 
                     download_name=attachment.original_filename)

@claims_bp.route('/<claim_id>/attachments/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(claim_id, attachment_id):
    claim = Claim.query.get_or_404(claim_id)
    attachment = ClaimAttachment.query.get_or_404(attachment_id)
    
    if attachment.claim_id != claim_id:
        flash('غير مسموح بالوصول إلى هذا المرفق', 'error')
        return redirect(url_for('claims.view_claim', claim_id=claim_id))
    
    # Delete file from filesystem
    try:
        if os.path.exists(attachment.storage_path):
            os.remove(attachment.storage_path)
    except:
        pass
    
    db.session.delete(attachment)
    db.session.commit()
    
    flash('تم حذف المرفق بنجاح', 'success')
    return redirect(url_for('claims.view_claim', claim_id=claim_id))

@claims_bp.route('/<claim_id>/download_all')
@login_required
def download_all_attachments(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    
    if not claim.attachments:
        flash('لا توجد مرفقات لهذه المطالبة', 'warning')
        return redirect(url_for('claims.view_claim', claim_id=claim_id))
    
    # Create ZIP file in memory
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for attachment in claim.attachments:
            try:
                zf.write(attachment.storage_path, attachment.original_filename)
            except:
                pass
    
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        as_attachment=True,
        download_name=f'claim_{claim_id}_attachments.zip',
        mimetype='application/zip'
    )

@claims_bp.route('/<claim_id>/status', methods=['POST'])
@login_required
def update_claim_status(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    new_status = request.form.get('status')
    
    valid_statuses = ['draft', 'ready', 'sent', 'failed', 'acknowledged', 'paid']
    if new_status in valid_statuses:
        claim.status = new_status
        claim.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('تم تحديث حالة المطالبة بنجاح', 'success')
    else:
        flash('حالة غير صالحة', 'error')
    
    return redirect(url_for('claims.view_claim', claim_id=claim_id))