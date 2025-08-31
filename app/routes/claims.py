from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Claim, ClaimAttachment, InsuranceCompany
from app.forms import ClaimForm, EditClaimForm, OCRUploadForm, AutoFillClaimForm
from app.email_utils import send_claim_email
from app.ocr_utils import extract_claim_data_from_file, extract_text_from_image, get_ocr_status, is_ocr_available
from app.notifications import send_claim_notification
from app.notification_manager import NotificationManager
from app.audit_utils import log_claim_created, log_claim_updated, log_claim_status_changed, log_claim_sent, log_claim_deleted, log_file_upload
import os
import uuid
import json
from datetime import datetime
import zipfile
import io
import mimetypes
from config import Config

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

        # Log file upload
        log_file_upload(unique_filename, file_size, claim_id)
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
def new():
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

        # Log claim creation
        log_claim_created(claim)

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

        # Send notification for new claim
        NotificationManager.notify_claim_created(claim)

        # Run AI classification automatically
        try:
            from app.ai_classification import classify_claim_ai
            from app.models import ClaimClassification, FraudIndicator

            result = classify_claim_ai(claim)

            # Save classification to database
            classification = ClaimClassification(
                claim_id=claim.id,
                category=result.category,
                subcategory=result.subcategory,
                confidence=result.confidence,
                risk_level=result.risk_level,
                fraud_probability=result.fraud_probability,
                suggested_amount=result.suggested_amount
            )

            if result.reasoning:
                classification.set_reasoning_list(result.reasoning)

            db.session.add(classification)
            db.session.flush()  # Get the ID

            # Save fraud indicators if any
            from app.ai_classification import ai_classifier
            fraud_probability, fraud_indicators = ai_classifier._detect_fraud(claim,
                                                                             ai_classifier._extract_text_content(claim))

            for indicator in fraud_indicators:
                fraud_indicator = FraudIndicator(
                    classification_id=classification.id,
                    indicator_type='pattern_analysis',
                    indicator_name=indicator.indicator,
                    description=indicator.description,
                    severity=indicator.severity,
                    confidence=indicator.confidence
                )
                db.session.add(fraud_indicator)

            db.session.commit()

            # Add classification info to flash message
            flash(f'تم إنشاء المطالبة بنجاح. رقم المطالبة: {claim.id}', 'success')
            flash(f'تم تصنيف المطالبة كـ "{classification.get_category_display_name()}" بثقة {(classification.confidence * 100):.1f}%', 'info')

            if result.risk_level == 'high':
                flash('تحذير: تم تصنيف هذه المطالبة كعالية المخاطر', 'warning')

            if result.fraud_probability > 0.5:
                flash(f'تحذير: احتمالية الاحتيال {(result.fraud_probability * 100):.1f}%', 'warning')

        except Exception as e:
            # Don't fail the request if AI classification fails
            print(f"Failed to run AI classification: {e}")
            flash(f'تم إنشاء المطالبة بنجاح. رقم المطالبة: {claim.id}', 'success')
            flash('تعذر تشغيل التصنيف الذكي، يمكن تشغيله لاحقاً', 'warning')

        # Send notification for new claim
        try:
            send_claim_notification('claim_created', claim)
        except Exception as e:
            # Don't fail the request if notification fails
            print(f"Failed to send notification: {e}")

        return redirect(url_for('claims.view', id=claim.id))

    return render_template('claims/new.html', form=form)

@claims_bp.route('/')
@login_required
def index():
    """List all claims"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    company_id = request.args.get('company_id', type=int)
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')

    # Build query with claim type relationship
    query = Claim.query.options(db.joinedload(Claim.claim_type))

    if search:
        query = query.filter(
            (Claim.client_name.contains(search)) |
            (Claim.client_national_id.contains(search))
        )

    if company_id:
        query = query.filter(Claim.company_id == company_id)

    if status:
        query = query.filter(Claim.status == status)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Claim.incident_date >= date_from_obj)
        except ValueError:
            pass

    claims = query.order_by(Claim.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    # Get companies for filter
    companies = InsuranceCompany.query.filter_by(active=True).all()

    return render_template('claims/index.html', claims=claims, companies=companies)

@claims_bp.route('/new-with-ocr', methods=['GET', 'POST'])
@login_required
def new_with_ocr():
    """Create new claim with OCR assistance"""
    if not Config.OCR_ENABLED:
        flash('ميزة OCR غير مفعلة', 'warning')
        return redirect(url_for('claims.new'))

    ocr_form = OCRUploadForm()
    autofill_form = AutoFillClaimForm()
    claim_form = ClaimForm()

    extracted_data = None

    if ocr_form.validate_on_submit() and ocr_form.extract_data.data:
        # Process uploaded file with OCR
        file = ocr_form.file.data
        if file and allowed_file(file.filename):
            # Save temporary file
            filename = secure_filename(file.filename)
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_' + filename)
            file.save(temp_path)

            try:
                # Extract data using OCR
                extracted_data = extract_claim_data_from_file(temp_path)

                if extracted_data.get('ocr_confidence', 0) > 0:
                    # Pre-fill the autofill form with extracted data
                    if 'name' in extracted_data:
                        autofill_form.client_name.data = extracted_data['name']
                    if 'national_id' in extracted_data:
                        autofill_form.client_national_id.data = extracted_data['national_id']
                    if 'policy_number' in extracted_data:
                        autofill_form.policy_number.data = extracted_data['policy_number']
                    if 'incident_number' in extracted_data:
                        autofill_form.incident_number.data = extracted_data['incident_number']
                    if 'amount' in extracted_data:
                        autofill_form.claim_amount.data = extracted_data['amount']

                    autofill_form.ocr_data.data = json.dumps(extracted_data)
                    autofill_form.ocr_confidence.data = str(extracted_data.get('ocr_confidence', 0))

                    flash(f'تم استخراج البيانات بنجاح! مستوى الثقة: {extracted_data.get("ocr_confidence", 0):.2%}', 'success')
                else:
                    flash('لم يتم العثور على بيانات قابلة للاستخراج في الملف', 'warning')

            except Exception as e:
                flash(f'خطأ في معالجة الملف: {str(e)}', 'error')
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    elif autofill_form.validate_on_submit():
        if autofill_form.use_extracted_data.data:
            # Use extracted data to pre-fill claim form
            try:
                ocr_data = json.loads(autofill_form.ocr_data.data) if autofill_form.ocr_data.data else {}

                # Pre-fill claim form
                claim_form.client_name.data = autofill_form.client_name.data
                claim_form.client_national_id.data = autofill_form.client_national_id.data
                claim_form.policy_number.data = autofill_form.policy_number.data
                claim_form.incident_number.data = autofill_form.incident_number.data
                claim_form.claim_amount.data = autofill_form.claim_amount.data
                claim_form.incident_date.data = autofill_form.incident_date.data

                flash('تم تعبئة النموذج بالبيانات المستخرجة', 'info')

            except Exception as e:
                flash(f'خطأ في استخدام البيانات المستخرجة: {str(e)}', 'error')

        elif autofill_form.manual_entry.data:
            # Redirect to manual entry
            return redirect(url_for('claims.new'))

    return render_template('claims/new_claim_ocr.html',
                         ocr_form=ocr_form,
                         autofill_form=autofill_form,
                         claim_form=claim_form,
                         extracted_data=extracted_data)

@claims_bp.route('/api/extract-data', methods=['POST'])
@login_required
def api_extract_data():
    """API endpoint for extracting data from uploaded files"""
    if not Config.OCR_ENABLED:
        return jsonify({'error': 'OCR not enabled'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    try:
        # Save temporary file
        filename = secure_filename(file.filename)
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', 'api_' + filename)
        file.save(temp_path)

        # Extract data using OCR
        extracted_data = extract_claim_data_from_file(temp_path)

        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return jsonify({
            'success': True,
            'data': extracted_data,
            'confidence': extracted_data.get('ocr_confidence', 0),
            'method': extracted_data.get('ocr_method', 'unknown')
        })

    except Exception as e:
        # Clean up temporary file in case of error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

        return jsonify({'error': str(e)}), 500

@claims_bp.route('/<string:id>')
@login_required
def view(id):
    claim = Claim.query.get_or_404(id)
    return render_template('claims/view.html', claim=claim)

@claims_bp.route('/<string:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit claim"""
    claim = Claim.query.get_or_404(id)
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
        return redirect(url_for('claims.view', id=claim.id))

    return render_template('claims/edit.html', form=form, claim=claim)

@claims_bp.route('/<string:id>/send', methods=['POST'])
@login_required
def send(id):
    """Send claim"""
    claim = Claim.query.get_or_404(id)

    if claim.status in ['sent', 'acknowledged', 'paid']:
        flash('لا يمكن إرسال مطالبة مرسلة مسبقاً', 'warning')
        return redirect(url_for('claims.view', id=claim.id))

    # Send email
    success, message = send_claim_email(claim, claim.attachments)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('claims.view', id=claim.id))

@claims_bp.route('/<string:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete claim"""
    claim = Claim.query.get_or_404(id)

    # Delete attachments from filesystem
    for attachment in claim.attachments:
        try:
            if os.path.exists(attachment.storage_path):
                os.remove(attachment.storage_path)
        except:
            pass

    # Delete claim folder
    claim_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(id))
    try:
        if os.path.exists(claim_folder):
            os.rmdir(claim_folder)
    except:
        pass

    db.session.delete(claim)
    db.session.commit()

    flash('تم حذف المطالبة بنجاح', 'success')
    return redirect(url_for('claims.index'))







@claims_bp.route('/<string:claim_id>/attachments/<int:attachment_id>')
@login_required
def download_attachment(claim_id, attachment_id):
    claim = Claim.query.get_or_404(claim_id)
    attachment = ClaimAttachment.query.get_or_404(attachment_id)

    if attachment.claim_id != claim_id:
        flash('غير مسموح بالوصول إلى هذا المرفق', 'error')
        return redirect(url_for('claims.view', id=claim_id))

    return send_file(attachment.storage_path, as_attachment=True,
                     download_name=attachment.original_filename)

@claims_bp.route('/<string:claim_id>/attachments/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(claim_id, attachment_id):
    claim = Claim.query.get_or_404(claim_id)
    attachment = ClaimAttachment.query.get_or_404(attachment_id)

    if attachment.claim_id != claim_id:
        flash('غير مسموح بالوصول إلى هذا المرفق', 'error')
        return redirect(url_for('claims.view', id=claim_id))

    # Delete file from filesystem
    try:
        if os.path.exists(attachment.storage_path):
            os.remove(attachment.storage_path)
    except:
        pass

    db.session.delete(attachment)
    db.session.commit()

    flash('تم حذف المرفق بنجاح', 'success')
    return redirect(url_for('claims.view', id=claim_id))

@claims_bp.route('/<string:claim_id>/download_all')
@login_required
def download_all_attachments(claim_id):
    claim = Claim.query.get_or_404(claim_id)

    if not claim.attachments:
        flash('لا توجد مرفقات لهذه المطالبة', 'warning')
        return redirect(url_for('claims.view', id=claim_id))

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

@claims_bp.route('/<string:claim_id>/status', methods=['POST'])
@login_required
def update_claim_status(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    new_status = request.form.get('status')

    valid_statuses = ['draft', 'ready', 'sent', 'failed', 'acknowledged', 'paid']
    if new_status in valid_statuses:
        old_status = claim.status
        claim.status = new_status
        claim.updated_at = datetime.utcnow()
        db.session.commit()

        # Send notification for status change
        try:
            NotificationManager.notify_claim_status_changed(claim, old_status, new_status, current_user)
            send_claim_notification('claim_status_changed', claim, {
                'old_status': old_status,
                'new_status': new_status,
                'updated_by': current_user.full_name
            })
        except Exception as e:
            print(f"Failed to send notification: {e}")

        flash('تم تحديث حالة المطالبة بنجاح', 'success')
    else:
        flash('حالة غير صالحة', 'error')

    return redirect(url_for('claims.view', id=claim_id))

@claims_bp.route('/api/ocr/process', methods=['POST'])
@login_required
def api_ocr_process():
    """API endpoint for processing files with OCR"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'لم يتم رفع أي ملفات'}), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات'}), 400

        # Process files
        processed_files = []
        extracted_data = {}

        for file in files:
            if file and file.filename and allowed_file(file.filename):
                # Save temporary file
                filename = secure_filename(file.filename)
                temp_filename = f"temp_{uuid.uuid4()}_{filename}"
                temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', temp_filename)

                # Ensure temp directory exists
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)

                file.save(temp_path)

                # Get file info
                file_size = os.path.getsize(temp_path)

                # Extract data using OCR
                try:
                    file_data = extract_claim_data_from_file(temp_path)
                    if file_data:
                        # Merge extracted data
                        for key, value in file_data.items():
                            if value and key not in extracted_data:
                                extracted_data[key] = value
                except Exception as e:
                    print(f"OCR extraction failed for {filename}: {e}")

                # Add file info
                processed_files.append({
                    'original_name': filename,
                    'temp_path': temp_path,
                    'size': file_size,
                    'type': file.content_type
                })

        return jsonify({
            'success': True,
            'data': extracted_data,
            'files': processed_files,
            'message': 'تم معالجة الملفات بنجاح'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'حدث خطأ في معالجة الملفات: {str(e)}'
        }), 500

@claims_bp.route('/api/claims/auto-save', methods=['POST'])
@login_required
def api_auto_save():
    """API endpoint for auto-saving claim drafts"""
    try:
        # Get form data
        form_data = request.form.to_dict()

        # Here you could save to a temporary table or session
        # For now, just return success

        return jsonify({
            'success': True,
            'message': 'تم الحفظ التلقائي'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@claims_bp.route('/api/ocr/status')
@login_required
def api_ocr_status():
    """Get OCR system status"""
    try:
        status = get_ocr_status()
        return jsonify({
            'success': True,
            'status': status,
            'enabled': Config.OCR_ENABLED,
            'available': is_ocr_available()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'enabled': Config.OCR_ENABLED,
            'available': False
        })

@claims_bp.route('/api/ocr/test', methods=['POST'])
@login_required
def api_ocr_test():
    """Test OCR functionality with sample text"""
    try:
        from app.ocr_utils import extract_claim_data_from_text

        # Sample Arabic text for testing
        sample_text = """
        تقرير حادث مروري
        رقم الحادث: ACC-2025-001
        التاريخ: 2025-01-21
        اسم المؤمن له: محمد أحمد السعيد
        رقم الهوية: 1234567890
        رقم الوثيقة: POL-2025-12345
        مبلغ الضرر: 25000 ريال سعودي
        نوع التغطية: شامل
        المدينة: الرياض
        """

        result = extract_claim_data_from_text(sample_text)

        return jsonify({
            'success': True,
            'test_result': result,
            'sample_text': sample_text.strip()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })