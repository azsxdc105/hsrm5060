from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import ClaimType, DynamicFormField, Claim, ClaimDynamicData, InsuranceCompany
from app.forms import DynamicClaimForm
import json
from datetime import datetime

dynamic_forms_bp = Blueprint('dynamic_forms', __name__)

@dynamic_forms_bp.route('/api/claim-types')
@login_required
def get_claim_types():
    """Get all active claim types"""
    try:
        claim_types = ClaimType.query.filter_by(active=True).order_by(ClaimType.sort_order).all()
        
        claim_types_data = []
        for ct in claim_types:
            claim_types_data.append({
                'id': ct.id,
                'name_ar': ct.name_ar,
                'name_en': ct.name_en,
                'code': ct.code,
                'description_ar': ct.description_ar,
                'description_en': ct.description_en,
                'icon': ct.icon,
                'color': ct.color
            })
        
        return jsonify({
            'success': True,
            'claim_types': claim_types_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dynamic_forms_bp.route('/api/claim-types/<int:claim_type_id>/fields')
@login_required
def get_claim_type_fields(claim_type_id):
    """Get dynamic fields for a specific claim type"""
    try:
        claim_type = ClaimType.query.get_or_404(claim_type_id)
        fields = DynamicFormField.query.filter_by(
            claim_type_id=claim_type_id, 
            active=True
        ).order_by(DynamicFormField.field_order).all()
        
        fields_data = []
        for field in fields:
            field_data = {
                'id': field.id,
                'field_name': field.field_name,
                'field_label_ar': field.field_label_ar,
                'field_label_en': field.field_label_en,
                'field_type': field.field_type,
                'field_order': field.field_order,
                'required': field.required,
                'min_length': field.min_length,
                'max_length': field.max_length,
                'min_value': field.min_value,
                'max_value': field.max_value,
                'pattern': field.pattern,
                'field_options': field.get_options(),
                'conditional_logic': field.get_conditional_logic(),
                'placeholder_ar': field.placeholder_ar,
                'placeholder_en': field.placeholder_en,
                'help_text_ar': field.help_text_ar,
                'help_text_en': field.help_text_en,
                'css_class': field.css_class
            }
            fields_data.append(field_data)
        
        return jsonify({
            'success': True,
            'fields': fields_data,
            'claim_type': {
                'id': claim_type.id,
                'name_ar': claim_type.name_ar,
                'code': claim_type.code
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dynamic_forms_bp.route('/claims/new-dynamic')
@login_required
def new_dynamic_claim():
    """Show dynamic claim form"""
    form = DynamicClaimForm()
    return render_template('claims/new_dynamic.html', form=form)

@dynamic_forms_bp.route('/claims/new-dynamic', methods=['POST'])
@login_required
def create_dynamic_claim():
    """Create a new claim with dynamic fields"""
    form = DynamicClaimForm()
    
    if form.validate_on_submit():
        try:
            # Create the main claim
            claim = Claim(
                company_id=form.company_id.data,
                claim_type_id=form.claim_type_id.data,
                client_name=form.client_name.data,
                client_national_id=form.client_national_id.data,
                policy_number=form.policy_number.data,
                incident_date=form.incident_date.data,
                claim_amount=form.claim_amount.data,
                claim_details=form.claim_details.data,
                coverage_type='other',  # Default for dynamic forms
                created_by_user_id=current_user.id
            )
            
            db.session.add(claim)
            db.session.flush()  # Get the claim ID
            
            # Save dynamic field data
            dynamic_data = {}
            for key, value in request.form.items():
                if key.startswith('dynamic_') or key in get_dynamic_field_names(form.claim_type_id.data):
                    if value:  # Only save non-empty values
                        dynamic_field_data = ClaimDynamicData(
                            claim_id=claim.id,
                            field_name=key,
                            field_value=value
                        )
                        db.session.add(dynamic_field_data)
                        dynamic_data[key] = value
            
            # Handle file uploads
            if form.files.data:
                from app.utils.file_handler import save_claim_files
                save_claim_files(claim, form.files.data)
            
            db.session.commit()
            
            flash('تم إنشاء المطالبة بنجاح!', 'success')
            return redirect(url_for('claims.view_claim', claim_id=claim.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في إنشاء المطالبة: {str(e)}', 'error')
            return render_template('claims/new_dynamic.html', form=form)
    
    return render_template('claims/new_dynamic.html', form=form)

@dynamic_forms_bp.route('/claims/<string:claim_id>/view-dynamic')
@login_required
def view_dynamic_claim(claim_id):
    """View a claim with dynamic data"""
    claim = Claim.query.get_or_404(claim_id)
    
    # Check permissions
    if not current_user.is_admin() and claim.created_by_user_id != current_user.id:
        flash('غير مصرح لك بعرض هذه المطالبة', 'error')
        return redirect(url_for('claims.index'))
    
    # Get claim type and dynamic data
    claim_type = None
    dynamic_data = {}
    
    if claim.claim_type_id:
        claim_type = ClaimType.query.get(claim.claim_type_id)
        if claim_type:
            # Get dynamic data
            dynamic_records = ClaimDynamicData.query.filter_by(claim_id=claim.id).all()
            for record in dynamic_records:
                dynamic_data[record.field_name] = record.field_value
    
    return render_template('claims/view_dynamic.html', 
                         claim=claim, 
                         claim_type=claim_type,
                         dynamic_data=dynamic_data)

def get_dynamic_field_names(claim_type_id):
    """Get list of dynamic field names for a claim type"""
    if not claim_type_id:
        return []
    
    fields = DynamicFormField.query.filter_by(
        claim_type_id=claim_type_id,
        active=True
    ).all()
    
    return [field.field_name for field in fields]

@dynamic_forms_bp.route('/admin/claim-types')
@login_required
def manage_claim_types():
    """Manage claim types (admin only)"""
    if not current_user.is_admin():
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.dashboard'))
    
    claim_types = ClaimType.query.order_by(ClaimType.sort_order).all()
    return render_template('admin/claim_types.html', claim_types=claim_types)

@dynamic_forms_bp.route('/admin/claim-types/new')
@login_required
def new_claim_type():
    """Create new claim type (admin only)"""
    if not current_user.is_admin():
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('admin/new_claim_type.html')

@dynamic_forms_bp.route('/admin/claim-types/<int:claim_type_id>/fields')
@login_required
def manage_claim_type_fields(claim_type_id):
    """Manage fields for a specific claim type (admin only)"""
    if not current_user.is_admin():
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.dashboard'))
    
    claim_type = ClaimType.query.get_or_404(claim_type_id)
    fields = DynamicFormField.query.filter_by(claim_type_id=claim_type_id).order_by(DynamicFormField.field_order).all()
    
    return render_template('admin/claim_type_fields.html', claim_type=claim_type, fields=fields)

# Initialize default claim types and fields
def init_default_claim_types():
    """Initialize default claim types and their fields"""
    
    # Check if claim types already exist
    if ClaimType.query.first():
        return
    
    # Car Insurance
    car_type = ClaimType(
        name_ar='تأمين السيارات',
        name_en='Car Insurance',
        code='car',
        description_ar='مطالبات تأمين المركبات والحوادث المرورية',
        description_en='Vehicle insurance and traffic accident claims',
        icon='fas fa-car',
        color='#dc3545',
        sort_order=1
    )
    db.session.add(car_type)
    db.session.flush()
    
    # Car insurance fields
    car_fields = [
        {
            'field_name': 'vehicle_make',
            'field_label_ar': 'ماركة السيارة',
            'field_label_en': 'Vehicle Make',
            'field_type': 'text',
            'required': True,
            'field_order': 1,
            'placeholder_ar': 'مثال: تويوتا، هوندا، نيسان'
        },
        {
            'field_name': 'vehicle_model',
            'field_label_ar': 'موديل السيارة',
            'field_label_en': 'Vehicle Model',
            'field_type': 'text',
            'required': True,
            'field_order': 2,
            'placeholder_ar': 'مثال: كامري، أكورد، التيما'
        },
        {
            'field_name': 'vehicle_year',
            'field_label_ar': 'سنة الصنع',
            'field_label_en': 'Manufacturing Year',
            'field_type': 'number',
            'required': True,
            'field_order': 3,
            'min_value': 1990,
            'max_value': 2025
        },
        {
            'field_name': 'license_plate',
            'field_label_ar': 'رقم اللوحة',
            'field_label_en': 'License Plate',
            'field_type': 'text',
            'required': True,
            'field_order': 4,
            'placeholder_ar': 'مثال: أ ب ج 1234'
        },
        {
            'field_name': 'accident_location',
            'field_label_ar': 'موقع الحادث',
            'field_label_en': 'Accident Location',
            'field_type': 'text',
            'required': True,
            'field_order': 5,
            'placeholder_ar': 'وصف تفصيلي لموقع الحادث'
        },
        {
            'field_name': 'has_injuries',
            'field_label_ar': 'هل يوجد إصابات؟',
            'field_label_en': 'Any Injuries?',
            'field_type': 'radio',
            'required': True,
            'field_order': 6,
            'field_options': [
                {'value': 'yes', 'label_ar': 'نعم', 'label_en': 'Yes'},
                {'value': 'no', 'label_ar': 'لا', 'label_en': 'No'}
            ]
        },
        {
            'field_name': 'injury_details',
            'field_label_ar': 'تفاصيل الإصابات',
            'field_label_en': 'Injury Details',
            'field_type': 'textarea',
            'required': False,
            'field_order': 7,
            'conditional_logic': {
                'depends_on': 'has_injuries',
                'condition': 'equals',
                'value': 'yes'
            },
            'placeholder_ar': 'وصف الإصابات والعلاج المطلوب'
        },
        {
            'field_name': 'police_report_number',
            'field_label_ar': 'رقم تقرير الشرطة',
            'field_label_en': 'Police Report Number',
            'field_type': 'text',
            'required': False,
            'field_order': 8,
            'placeholder_ar': 'رقم التقرير من الشرطة (إن وجد)'
        }
    ]
    
    for field_data in car_fields:
        field = DynamicFormField(
            claim_type_id=car_type.id,
            **field_data
        )
        db.session.add(field)
    
    # Health Insurance
    health_type = ClaimType(
        name_ar='التأمين الطبي',
        name_en='Health Insurance',
        code='health',
        description_ar='مطالبات التأمين الطبي والعلاج',
        description_en='Medical insurance and treatment claims',
        icon='fas fa-heartbeat',
        color='#28a745',
        sort_order=2
    )
    db.session.add(health_type)
    db.session.flush()
    
    # Health insurance fields
    health_fields = [
        {
            'field_name': 'hospital_name',
            'field_label_ar': 'اسم المستشفى',
            'field_label_en': 'Hospital Name',
            'field_type': 'text',
            'required': True,
            'field_order': 1,
            'placeholder_ar': 'اسم المستشفى أو المركز الطبي'
        },
        {
            'field_name': 'doctor_name',
            'field_label_ar': 'اسم الطبيب',
            'field_label_en': 'Doctor Name',
            'field_type': 'text',
            'required': True,
            'field_order': 2,
            'placeholder_ar': 'اسم الطبيب المعالج'
        },
        {
            'field_name': 'treatment_type',
            'field_label_ar': 'نوع العلاج',
            'field_label_en': 'Treatment Type',
            'field_type': 'select',
            'required': True,
            'field_order': 3,
            'field_options': [
                {'value': 'consultation', 'label_ar': 'استشارة طبية', 'label_en': 'Medical Consultation'},
                {'value': 'surgery', 'label_ar': 'عملية جراحية', 'label_en': 'Surgery'},
                {'value': 'emergency', 'label_ar': 'طوارئ', 'label_en': 'Emergency'},
                {'value': 'medication', 'label_ar': 'أدوية', 'label_en': 'Medication'},
                {'value': 'tests', 'label_ar': 'فحوصات', 'label_en': 'Tests'}
            ]
        },
        {
            'field_name': 'diagnosis',
            'field_label_ar': 'التشخيص',
            'field_label_en': 'Diagnosis',
            'field_type': 'textarea',
            'required': True,
            'field_order': 4,
            'placeholder_ar': 'التشخيص الطبي'
        },
        {
            'field_name': 'surgery_details',
            'field_label_ar': 'تفاصيل العملية',
            'field_label_en': 'Surgery Details',
            'field_type': 'textarea',
            'required': False,
            'field_order': 5,
            'conditional_logic': {
                'depends_on': 'treatment_type',
                'condition': 'equals',
                'value': 'surgery'
            },
            'placeholder_ar': 'تفاصيل العملية الجراحية'
        },
        {
            'field_name': 'treatment_duration',
            'field_label_ar': 'مدة العلاج (بالأيام)',
            'field_label_en': 'Treatment Duration (Days)',
            'field_type': 'number',
            'required': False,
            'field_order': 6,
            'min_value': 1,
            'max_value': 365
        }
    ]
    
    for field_data in health_fields:
        field = DynamicFormField(
            claim_type_id=health_type.id,
            **field_data
        )
        db.session.add(field)
    
    # Home Insurance
    home_type = ClaimType(
        name_ar='تأمين المنزل',
        name_en='Home Insurance',
        code='home',
        description_ar='مطالبات تأمين المنازل والممتلكات',
        description_en='Home and property insurance claims',
        icon='fas fa-home',
        color='#ffc107',
        sort_order=3
    )
    db.session.add(home_type)
    db.session.flush()
    
    # Home insurance fields
    home_fields = [
        {
            'field_name': 'property_address',
            'field_label_ar': 'عنوان العقار',
            'field_label_en': 'Property Address',
            'field_type': 'textarea',
            'required': True,
            'field_order': 1,
            'placeholder_ar': 'العنوان الكامل للعقار'
        },
        {
            'field_name': 'damage_type',
            'field_label_ar': 'نوع الضرر',
            'field_label_en': 'Damage Type',
            'field_type': 'select',
            'required': True,
            'field_order': 2,
            'field_options': [
                {'value': 'fire', 'label_ar': 'حريق', 'label_en': 'Fire'},
                {'value': 'water', 'label_ar': 'أضرار مياه', 'label_en': 'Water Damage'},
                {'value': 'theft', 'label_ar': 'سرقة', 'label_en': 'Theft'},
                {'value': 'natural', 'label_ar': 'كوارث طبيعية', 'label_en': 'Natural Disasters'},
                {'value': 'vandalism', 'label_ar': 'تخريب', 'label_en': 'Vandalism'}
            ]
        },
        {
            'field_name': 'affected_rooms',
            'field_label_ar': 'الغرف المتضررة',
            'field_label_en': 'Affected Rooms',
            'field_type': 'checkbox',
            'required': False,
            'field_order': 3,
            'field_options': [
                {'value': 'living_room', 'label_ar': 'غرفة المعيشة', 'label_en': 'Living Room'},
                {'value': 'bedroom', 'label_ar': 'غرفة النوم', 'label_en': 'Bedroom'},
                {'value': 'kitchen', 'label_ar': 'المطبخ', 'label_en': 'Kitchen'},
                {'value': 'bathroom', 'label_ar': 'الحمام', 'label_en': 'Bathroom'},
                {'value': 'garage', 'label_ar': 'الجراج', 'label_en': 'Garage'}
            ]
        },
        {
            'field_name': 'fire_cause',
            'field_label_ar': 'سبب الحريق',
            'field_label_en': 'Fire Cause',
            'field_type': 'select',
            'required': False,
            'field_order': 4,
            'conditional_logic': {
                'depends_on': 'damage_type',
                'condition': 'equals',
                'value': 'fire'
            },
            'field_options': [
                {'value': 'electrical', 'label_ar': 'كهربائي', 'label_en': 'Electrical'},
                {'value': 'gas', 'label_ar': 'غاز', 'label_en': 'Gas'},
                {'value': 'cooking', 'label_ar': 'طبخ', 'label_en': 'Cooking'},
                {'value': 'unknown', 'label_ar': 'غير معروف', 'label_en': 'Unknown'}
            ]
        },
        {
            'field_name': 'stolen_items',
            'field_label_ar': 'الأشياء المسروقة',
            'field_label_en': 'Stolen Items',
            'field_type': 'textarea',
            'required': False,
            'field_order': 5,
            'conditional_logic': {
                'depends_on': 'damage_type',
                'condition': 'equals',
                'value': 'theft'
            },
            'placeholder_ar': 'قائمة بالأشياء المسروقة وقيمتها التقديرية'
        }
    ]
    
    for field_data in home_fields:
        field = DynamicFormField(
            claim_type_id=home_type.id,
            **field_data
        )
        db.session.add(field)
    
    # Travel Insurance
    travel_type = ClaimType(
        name_ar='تأمين السفر',
        name_en='Travel Insurance',
        code='travel',
        description_ar='مطالبات تأمين السفر والرحلات',
        description_en='Travel and trip insurance claims',
        icon='fas fa-plane',
        color='#17a2b8',
        sort_order=4
    )
    db.session.add(travel_type)
    db.session.flush()
    
    # Travel insurance fields
    travel_fields = [
        {
            'field_name': 'trip_destination',
            'field_label_ar': 'وجهة السفر',
            'field_label_en': 'Trip Destination',
            'field_type': 'text',
            'required': True,
            'field_order': 1,
            'placeholder_ar': 'البلد أو المدينة'
        },
        {
            'field_name': 'departure_date',
            'field_label_ar': 'تاريخ المغادرة',
            'field_label_en': 'Departure Date',
            'field_type': 'date',
            'required': True,
            'field_order': 2
        },
        {
            'field_name': 'return_date',
            'field_label_ar': 'تاريخ العودة',
            'field_label_en': 'Return Date',
            'field_type': 'date',
            'required': True,
            'field_order': 3
        },
        {
            'field_name': 'claim_reason',
            'field_label_ar': 'سبب المطالبة',
            'field_label_en': 'Claim Reason',
            'field_type': 'select',
            'required': True,
            'field_order': 4,
            'field_options': [
                {'value': 'trip_cancellation', 'label_ar': 'إلغاء الرحلة', 'label_en': 'Trip Cancellation'},
                {'value': 'trip_delay', 'label_ar': 'تأخير الرحلة', 'label_en': 'Trip Delay'},
                {'value': 'lost_luggage', 'label_ar': 'فقدان الأمتعة', 'label_en': 'Lost Luggage'},
                {'value': 'medical_emergency', 'label_ar': 'طوارئ طبية', 'label_en': 'Medical Emergency'},
                {'value': 'missed_connection', 'label_ar': 'فوات الرحلة', 'label_en': 'Missed Connection'}
            ]
        },
        {
            'field_name': 'flight_number',
            'field_label_ar': 'رقم الرحلة',
            'field_label_en': 'Flight Number',
            'field_type': 'text',
            'required': False,
            'field_order': 5,
            'placeholder_ar': 'رقم رحلة الطيران'
        },
        {
            'field_name': 'airline_name',
            'field_label_ar': 'اسم شركة الطيران',
            'field_label_en': 'Airline Name',
            'field_type': 'text',
            'required': False,
            'field_order': 6,
            'placeholder_ar': 'اسم شركة الطيران'
        },
        {
            'field_name': 'luggage_weight',
            'field_label_ar': 'وزن الأمتعة (كيلو)',
            'field_label_en': 'Luggage Weight (KG)',
            'field_type': 'number',
            'required': False,
            'field_order': 7,
            'conditional_logic': {
                'depends_on': 'claim_reason',
                'condition': 'equals',
                'value': 'lost_luggage'
            },
            'min_value': 1,
            'max_value': 50
        }
    ]
    
    for field_data in travel_fields:
        field = DynamicFormField(
            claim_type_id=travel_type.id,
            **field_data
        )
        db.session.add(field)
    
    try:
        db.session.commit()
        print("✅ Default claim types and fields created successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating default claim types: {e}")