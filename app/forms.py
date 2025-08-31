from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DecimalField, DateField, HiddenField, PasswordField, BooleanField, MultipleFileField, SubmitField, IntegerField, TimeField, RadioField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo
from wtforms.widgets import TextArea
from app.models import InsuranceCompany, ClaimType

class LoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember_me = BooleanField('تذكرني')

class ClaimForm(FlaskForm):
    company_id = SelectField('شركة التأمين', validators=[DataRequired()], coerce=int)
    client_name = StringField('اسم العميل', validators=[DataRequired(), Length(min=2, max=120)])
    client_national_id = StringField('رقم الهوية/الإقامة', validators=[DataRequired(), Length(min=10, max=20)])
    policy_number = StringField('رقم الوثيقة', validators=[Optional(), Length(max=50)])
    incident_number = StringField('رقم الحادث', validators=[Optional(), Length(max=50)])
    incident_date = DateField('تاريخ الحادث', validators=[DataRequired()])
    claim_amount = DecimalField('مبلغ المطالبة', validators=[DataRequired(), NumberRange(min=0)])
    coverage_type = SelectField('نوع التغطية', validators=[DataRequired()], 
                               choices=[
                                   ('third_party', 'ضد الغير'),
                                   ('comprehensive', 'شامل'),
                                   ('other', 'أخرى')
                               ])
    claim_details = TextAreaField('تفاصيل المطالبة', validators=[DataRequired()], widget=TextArea())
    city = StringField('المدينة', validators=[Optional(), Length(max=100)])
    tags = StringField('العلامات', validators=[Optional()], 
                       description='افصل العلامات بفاصلة (مثال: طبي، مركبة، إصلاح)')
    files = MultipleFileField('المرفقات', validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'docx'], 'الملفات المسموحة: PDF, JPG, PNG, DOCX فقط')])
    
    def __init__(self, *args, **kwargs):
        super(ClaimForm, self).__init__(*args, **kwargs)
        self.company_id.choices = [(c.id, c.name_ar) for c in InsuranceCompany.query.filter_by(active=True).all()]

# Dynamic Claim Form with claim type selection
class DynamicClaimForm(FlaskForm):
    # Basic fields (always present)
    claim_type_id = SelectField('نوع المطالبة', validators=[DataRequired()], coerce=int)
    company_id = SelectField('شركة التأمين', validators=[DataRequired()], coerce=int)
    client_name = StringField('اسم العميل', validators=[DataRequired(), Length(min=2, max=120)])
    client_national_id = StringField('رقم الهوية/الإقامة', validators=[DataRequired(), Length(min=10, max=20)])
    policy_number = StringField('رقم الوثيقة', validators=[Optional(), Length(max=50)])
    incident_date = DateField('تاريخ الحادث', validators=[DataRequired()])
    claim_amount = DecimalField('مبلغ المطالبة', validators=[DataRequired(), NumberRange(min=0)])
    claim_details = TextAreaField('تفاصيل المطالبة', validators=[DataRequired()], widget=TextArea())
    files = MultipleFileField('المرفقات', validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'docx'], 'الملفات المسموحة: PDF, JPG, PNG, DOCX فقط')])
    
    def __init__(self, *args, **kwargs):
        super(DynamicClaimForm, self).__init__(*args, **kwargs)
        self.company_id.choices = [(c.id, c.name_ar) for c in InsuranceCompany.query.filter_by(active=True).all()]
        self.claim_type_id.choices = [(ct.id, ct.name_ar) for ct in ClaimType.query.filter_by(active=True).order_by(ClaimType.sort_order).all()]

class EditClaimForm(ClaimForm):
    status = SelectField('حالة المطالبة', validators=[DataRequired()],
                        choices=[
                            ('draft', 'مسودة'),
                            ('ready', 'جاهز'),
                            ('sent', 'مرسل'),
                            ('failed', 'فشل'),
                            ('acknowledged', 'مستلم'),
                            ('paid', 'مدفوع')
                        ])

class InsuranceCompanyForm(FlaskForm):
    name_ar = StringField('الاسم بالعربية', validators=[DataRequired(), Length(min=2, max=200)])
    name_en = StringField('الاسم بالإنجليزية', validators=[DataRequired(), Length(min=2, max=200)])
    claims_email_primary = StringField('البريد الإلكتروني الرئيسي', validators=[DataRequired(), Email()])
    claims_email_cc = TextAreaField('البريدات الإلكترونية للنسخ (CC)', validators=[Optional()],
                                   description='ادخل البريدات الإلكترونية مفصولة بفاصلة')
    policy_portal_url = StringField('رابط بوابة الوثائق', validators=[Optional(), Length(max=500)])
    notes = TextAreaField('ملاحظات', validators=[Optional()])
    active = BooleanField('نشط', default=True)
    email_template_ar = TextAreaField('قالب البريد الإلكتروني (عربي)', validators=[Optional()],
                                     description='استخدم {{متغير}} للبيانات الديناميكية')
    email_template_en = TextAreaField('قالب البريد الإلكتروني (إنجليزي)', validators=[Optional()],
                                     description='استخدم {{متغير}} للبيانات الديناميكية')

# UserForm moved to end of file to avoid duplication

class SearchForm(FlaskForm):
    search_term = StringField('البحث', validators=[Optional()])
    company_id = SelectField('شركة التأمين', validators=[Optional()], coerce=lambda x: int(x) if x else None)
    status = SelectField('الحالة', validators=[Optional()], 
                        choices=[
                            ('', 'جميع الحالات'),
                            ('draft', 'مسودة'),
                            ('ready', 'جاهز'),
                            ('sent', 'مرسل'),
                            ('failed', 'فشل'),
                            ('acknowledged', 'مستلم'),
                            ('paid', 'مدفوع')
                        ])
    date_from = DateField('من تاريخ', validators=[Optional()])
    date_to = DateField('إلى تاريخ', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        choices = [('', 'جميع الشركات')]
        try:
            choices.extend([(c.id, c.name_ar) for c in InsuranceCompany.query.filter_by(active=True).all()])
        except:
            pass  # Handle case when database is not available
        self.company_id.choices = choices

class SettingsForm(FlaskForm):
    mail_server = StringField('خادم البريد الإلكتروني', validators=[DataRequired()])
    mail_port = StringField('منفذ البريد الإلكتروني', validators=[DataRequired()])
    mail_username = StringField('اسم المستخدم', validators=[DataRequired()])
    mail_password = PasswordField('كلمة المرور', validators=[Optional()])
    mail_use_tls = BooleanField('استخدام TLS', default=True)
    mail_use_ssl = BooleanField('استخدام SSL', default=False)
    max_upload_mb = StringField('الحد الأقصى لحجم الملف (MB)', validators=[DataRequired()])
    ai_enabled = BooleanField('تفعيل الذكاء الاصطناعي', default=False)
    ocr_enabled = BooleanField('تفعيل استخراج النص من الصور', default=False)



class OCRUploadForm(FlaskForm):
    """Form for uploading files for OCR processing"""
    file = FileField('رفع ملف للمعالجة',
                     validators=[FileRequired(), FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp'],
                                                           'يُسمح فقط بملفات PDF والصور!')],
                     description='ارفع ملف PDF أو صورة لاستخراج البيانات تلقائياً')
    extract_data = SubmitField('استخراج البيانات')

class AutoFillClaimForm(FlaskForm):
    """Form for auto-filling claim data from OCR"""
    # OCR extracted data (hidden fields)
    ocr_data = HiddenField('بيانات OCR')
    ocr_confidence = HiddenField('مستوى الثقة')

    # Editable fields that can be auto-filled
    client_name = StringField('اسم العميل', validators=[Optional(), Length(min=2, max=120)])
    client_national_id = StringField('رقم الهوية/الإقامة', validators=[Optional(), Length(min=10, max=20)])
    policy_number = StringField('رقم الوثيقة', validators=[Optional(), Length(max=50)])
    incident_number = StringField('رقم الحادث', validators=[Optional(), Length(max=50)])
    incident_date = DateField('تاريخ الحادث', validators=[Optional()])
    claim_amount = DecimalField('مبلغ المطالبة', validators=[Optional(), NumberRange(min=0)], places=2)

    # Action buttons
    use_extracted_data = SubmitField('استخدام البيانات المستخرجة')
    manual_entry = SubmitField('إدخال يدوي')
    re_extract = SubmitField('إعادة الاستخراج')

class AdvancedSearchForm(FlaskForm):
    """Advanced search form with multiple filters"""
    # Text search fields
    search_query = StringField('البحث العام', validators=[Optional()],
                              render_kw={'placeholder': 'ابحث في جميع الحقول...'})
    client_name = StringField('اسم العميل', validators=[Optional()],
                             render_kw={'placeholder': 'ابحث باسم العميل...'})
    client_national_id = StringField('رقم الهوية/الإقامة', validators=[Optional()],
                                   render_kw={'placeholder': 'رقم الهوية أو الإقامة...'})
    policy_number = StringField('رقم الوثيقة', validators=[Optional()],
                               render_kw={'placeholder': 'رقم وثيقة التأمين...'})
    incident_number = StringField('رقم الحادث', validators=[Optional()],
                                 render_kw={'placeholder': 'رقم الحادث...'})

    # Dropdown filters
    company_id = SelectField('شركة التأمين', coerce=int, validators=[Optional()])
    status = SelectField('الحالة', choices=[
        ('', 'الكل'),
        ('draft', 'مسودة'),
        ('ready', 'جاهز'),
        ('sent', 'مرسل'),
        ('failed', 'فشل'),
        ('acknowledged', 'مستلم'),
        ('paid', 'مدفوع')
    ], validators=[Optional()])
    coverage_type = SelectField('نوع التغطية', choices=[
        ('', 'الكل'),
        ('third_party', 'ضد الغير'),
        ('comprehensive', 'شامل')
    ], validators=[Optional()])
    created_by = SelectField('أنشأها', coerce=int, validators=[Optional()])

    # Date range filters
    incident_date_from = DateField('تاريخ الحادث من', validators=[Optional()])
    incident_date_to = DateField('تاريخ الحادث إلى', validators=[Optional()])
    created_date_from = DateField('تاريخ الإنشاء من', validators=[Optional()])
    created_date_to = DateField('تاريخ الإنشاء إلى', validators=[Optional()])
    email_sent_date_from = DateField('تاريخ الإرسال من', validators=[Optional()])
    email_sent_date_to = DateField('تاريخ الإرسال إلى', validators=[Optional()])

    # Amount range filters
    amount_from = DecimalField('المبلغ من', validators=[Optional(), NumberRange(min=0)], places=2)
    amount_to = DecimalField('المبلغ إلى', validators=[Optional(), NumberRange(min=0)], places=2)

    # City filter
    city = StringField('المدينة', validators=[Optional()],
                      render_kw={'placeholder': 'ابحث بالمدينة...'})

    # Tags filter
    tags = StringField('العلامات', validators=[Optional()],
                      render_kw={'placeholder': 'ابحث بالعلامات...'})

    # Sorting options
    sort_by = SelectField('ترتيب حسب', choices=[
        ('created_at_desc', 'تاريخ الإنشاء (الأحدث أولاً)'),
        ('created_at_asc', 'تاريخ الإنشاء (الأقدم أولاً)'),
        ('incident_date_desc', 'تاريخ الحادث (الأحدث أولاً)'),
        ('incident_date_asc', 'تاريخ الحادث (الأقدم أولاً)'),
        ('amount_desc', 'المبلغ (الأعلى أولاً)'),
        ('amount_asc', 'المبلغ (الأقل أولاً)'),
        ('client_name_asc', 'اسم العميل (أ-ي)'),
        ('client_name_desc', 'اسم العميل (ي-أ)')
    ], default='created_at_desc', validators=[Optional()])

    # Results per page
    per_page = SelectField('عدد النتائج في الصفحة', choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ], default='25', coerce=int, validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(AdvancedSearchForm, self).__init__(*args, **kwargs)

        # Populate company choices
        self.company_id.choices = [('', 'الكل')] + [(c.id, c.name_ar) for c in InsuranceCompany.query.filter_by(active=True).all()]

        # Populate created_by choices
        from app.models import User
        self.created_by.choices = [('', 'الكل')] + [(u.id, u.full_name) for u in User.query.filter_by(active=True).all()]

class PaymentForm(FlaskForm):
    """Form for adding/editing payments"""
    amount = DecimalField('المبلغ', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    currency = SelectField('العملة', choices=[
        ('SAR', 'ريال سعودي'),
        ('USD', 'دولار أمريكي'),
        ('EUR', 'يورو')
    ], default='SAR', validators=[DataRequired()])

    payment_method = SelectField('طريقة الدفع', choices=[
        ('bank_transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
        ('cash', 'نقدي'),
        ('online', 'دفع إلكتروني')
    ], validators=[DataRequired()])

    payment_reference = StringField('رقم المرجع', validators=[Optional()])
    payment_date = DateField('تاريخ الدفع', validators=[DataRequired()])
    received_date = DateField('تاريخ الاستلام', validators=[Optional()])

    status = SelectField('الحالة', choices=[
        ('pending', 'في الانتظار'),
        ('received', 'مستلم'),
        ('failed', 'فشل'),
        ('cancelled', 'ملغي')
    ], default='pending', validators=[DataRequired()])

    # Bank transfer fields
    bank_name = StringField('اسم البنك', validators=[Optional()])
    account_number = StringField('رقم الحساب', validators=[Optional()])
    iban = StringField('رقم الآيبان', validators=[Optional(), Length(max=34)])

    # Check fields
    check_number = StringField('رقم الشيك', validators=[Optional()])
    check_bank = StringField('بنك الشيك', validators=[Optional()])

    # Online payment fields
    transaction_id = StringField('رقم المعاملة', validators=[Optional()])

    notes = TextAreaField('ملاحظات', validators=[Optional()])

    submit = SubmitField('حفظ الدفعة')

class PaymentSearchForm(FlaskForm):
    """Form for searching payments"""
    claim_id = StringField('رقم المطالبة', validators=[Optional()])
    payment_method = SelectField('طريقة الدفع', choices=[
        ('', 'الكل'),
        ('bank_transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
        ('cash', 'نقدي'),
        ('online', 'دفع إلكتروني')
    ], validators=[Optional()])

    status = SelectField('الحالة', choices=[
        ('', 'الكل'),
        ('pending', 'في الانتظار'),
        ('received', 'مستلم'),
        ('failed', 'فشل'),
        ('cancelled', 'ملغي')
    ], validators=[Optional()])

    date_from = DateField('من تاريخ', validators=[Optional()])
    date_to = DateField('إلى تاريخ', validators=[Optional()])

    amount_from = DecimalField('المبلغ من', validators=[Optional(), NumberRange(min=0)], places=2)
    amount_to = DecimalField('المبلغ إلى', validators=[Optional(), NumberRange(min=0)], places=2)

class EmailSettingsForm(FlaskForm):
    mail_server = StringField('خادم البريد الإلكتروني', validators=[DataRequired()],
                             default='smtp.gmail.com')
    mail_port = IntegerField('منفذ الخادم', validators=[DataRequired(), NumberRange(min=1, max=65535)],
                            default=587)
    mail_use_tls = BooleanField('استخدام TLS', default=True)
    mail_use_ssl = BooleanField('استخدام SSL', default=False)
    mail_username = StringField('اسم المستخدم (البريد الإلكتروني)', validators=[DataRequired(), Email()])
    mail_password = PasswordField('كلمة المرور (App Password)', validators=[DataRequired()])
    mail_default_sender = StringField('المرسل الافتراضي', validators=[DataRequired(), Email()])
    submit = SubmitField('حفظ الإعدادات')

class UserForm(FlaskForm):
    full_name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    phone = StringField('رقم الهاتف', validators=[Optional(), Length(max=20)],
                       render_kw={'placeholder': '+966501234567'})
    whatsapp_number = StringField('رقم الواتساب', validators=[Optional(), Length(max=20)],
                                 render_kw={'placeholder': '+966501234567'})
    role = SelectField('الدور', validators=[DataRequired()],
                      choices=[
                          ('admin', 'مدير'),
                          ('claims_agent', 'موظف مطالبات'),
                          ('viewer', 'مشاهد فقط')
                      ])
    is_active = BooleanField('نشط', default=True)
    password = PasswordField('كلمة المرور', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور',
                                   validators=[EqualTo('password', message='كلمات المرور غير متطابقة')])
    submit = SubmitField('حفظ المستخدم')

class PaymentForm(FlaskForm):
    """Form for creating/editing payments"""
    claim_id = SelectField('المطالبة', validators=[DataRequired()], coerce=str)
    amount = DecimalField('المبلغ', validators=[DataRequired(), NumberRange(min=0.01)],
                         render_kw={'step': '0.01', 'min': '0.01'})
    currency = SelectField('العملة', validators=[DataRequired()],
                          choices=[('SAR', 'ريال سعودي'), ('USD', 'دولار أمريكي'), ('EUR', 'يورو')],
                          default='SAR')
    payment_method = SelectField('طريقة الدفع', validators=[DataRequired()],
                                choices=[
                                    ('bank_transfer', 'تحويل بنكي'),
                                    ('check', 'شيك'),
                                    ('cash', 'نقداً'),
                                    ('online', 'دفع إلكتروني')
                                ])
    payment_date = DateField('تاريخ الدفع', validators=[DataRequired()])
    payment_reference = StringField('رقم المرجع', validators=[Optional(), Length(max=100)])

    # Bank transfer fields
    bank_name = StringField('اسم البنك', validators=[Optional(), Length(max=100)])
    account_number = StringField('رقم الحساب', validators=[Optional(), Length(max=50)])
    iban = StringField('رقم الآيبان', validators=[Optional(), Length(max=34)])

    # Check fields
    check_number = StringField('رقم الشيك', validators=[Optional(), Length(max=50)])

    # Online payment fields
    transaction_id = StringField('رقم المعاملة', validators=[Optional(), Length(max=100)])

    notes = TextAreaField('ملاحظات', validators=[Optional(), Length(max=500)])
    status = SelectField('الحالة', validators=[DataRequired()],
                        choices=[
                            ('pending', 'في الانتظار'),
                            ('completed', 'مكتمل'),
                            ('failed', 'فشل'),
                            ('cancelled', 'ملغي')
                        ],
                        default='pending')
    submit = SubmitField('حفظ المدفوعة')

class PaymentSearchForm(FlaskForm):
    """Form for searching payments"""
    claim_id = StringField('رقم المطالبة', validators=[Optional()])
    payment_method = SelectField('طريقة الدفع', validators=[Optional()],
                                choices=[('', 'جميع الطرق')] + [
                                    ('bank_transfer', 'تحويل بنكي'),
                                    ('check', 'شيك'),
                                    ('cash', 'نقداً'),
                                    ('online', 'دفع إلكتروني')
                                ])
    status = SelectField('الحالة', validators=[Optional()],
                        choices=[('', 'جميع الحالات')] + [
                            ('pending', 'في الانتظار'),
                            ('completed', 'مكتمل'),
                            ('failed', 'فشل'),
                            ('cancelled', 'ملغي')
                        ])
    date_from = DateField('من تاريخ', validators=[Optional()])
    date_to = DateField('إلى تاريخ', validators=[Optional()])
    amount_from = DecimalField('من مبلغ', validators=[Optional(), NumberRange(min=0)],
                              render_kw={'step': '0.01', 'min': '0'})
    amount_to = DecimalField('إلى مبلغ', validators=[Optional(), NumberRange(min=0)],
                            render_kw={'step': '0.01', 'min': '0'})
    submit = SubmitField('بحث')


# ============================================================================
# ADVANCED NOTIFICATIONS FORMS
# ============================================================================

class NotificationSettingsForm(FlaskForm):
    """Form for user notification settings"""
    # Global notification type settings
    email_enabled = BooleanField('تفعيل الإشعارات عبر البريد الإلكتروني', default=True)
    sms_enabled = BooleanField('تفعيل الإشعارات عبر الرسائل النصية', default=False)
    push_enabled = BooleanField('تفعيل الإشعارات المنبثقة', default=True)
    whatsapp_enabled = BooleanField('تفعيل إشعارات واتساب', default=False)
    in_app_enabled = BooleanField('تفعيل الإشعارات داخل التطبيق', default=True)

    # Contact information
    whatsapp_phone = StringField('رقم واتساب', validators=[Optional(), Length(max=20)],
                                render_kw={'placeholder': '+966501234567'})

    # Quiet hours
    quiet_hours_enabled = BooleanField('تفعيل ساعات الهدوء', default=False)
    quiet_hours_start = TimeField('بداية ساعات الهدوء', validators=[Optional()])
    quiet_hours_end = TimeField('نهاية ساعات الهدوء', validators=[Optional()])

    # Event-specific settings
    claim_created_email = BooleanField('إشعار بريد إلكتروني عند إنشاء مطالبة', default=True)
    claim_created_sms = BooleanField('إشعار رسالة نصية عند إنشاء مطالبة', default=False)
    claim_created_push = BooleanField('إشعار منبثق عند إنشاء مطالبة', default=True)
    claim_created_whatsapp = BooleanField('إشعار واتساب عند إنشاء مطالبة', default=False)

    claim_sent_email = BooleanField('إشعار بريد إلكتروني عند إرسال مطالبة', default=True)
    claim_sent_sms = BooleanField('إشعار رسالة نصية عند إرسال مطالبة', default=False)
    claim_sent_push = BooleanField('إشعار منبثق عند إرسال مطالبة', default=True)
    claim_sent_whatsapp = BooleanField('إشعار واتساب عند إرسال مطالبة', default=False)

    claim_status_changed_email = BooleanField('إشعار بريد إلكتروني عند تغيير حالة المطالبة', default=True)
    claim_status_changed_sms = BooleanField('إشعار رسالة نصية عند تغيير حالة المطالبة', default=False)
    claim_status_changed_push = BooleanField('إشعار منبثق عند تغيير حالة المطالبة', default=True)
    claim_status_changed_whatsapp = BooleanField('إشعار واتساب عند تغيير حالة المطالبة', default=False)

    submit = SubmitField('حفظ الإعدادات')


class SendNotificationForm(FlaskForm):
    """Form for sending custom notifications"""
    title = StringField('عنوان الإشعار', validators=[DataRequired(), Length(min=1, max=200)])
    message = TextAreaField('رسالة الإشعار', validators=[DataRequired(), Length(min=1, max=1000)],
                           widget=TextArea(), render_kw={'rows': 5})

    # Notification types
    notification_types = SelectField('أنواع الإشعارات', validators=[DataRequired()],
                                   choices=[
                                       ('email', 'بريد إلكتروني فقط'),
                                       ('sms', 'رسالة نصية فقط'),
                                       ('push', 'إشعار منبثق فقط'),
                                       ('whatsapp', 'واتساب فقط'),
                                       ('in_app', 'داخل التطبيق فقط'),
                                       ('all', 'جميع الأنواع المفعلة'),
                                       ('email,push', 'بريد إلكتروني + منبثق'),
                                       ('email,sms', 'بريد إلكتروني + رسالة نصية')
                                   ])

    # Priority
    priority = SelectField('الأولوية', validators=[DataRequired()],
                          choices=[
                              ('low', 'منخفضة'),
                              ('normal', 'عادية'),
                              ('high', 'عالية'),
                              ('urgent', 'عاجلة')
                          ], default='normal')

    # Recipients
    recipient_type = SelectField('المستلمون', validators=[DataRequired()],
                               choices=[
                                   ('all_users', 'جميع المستخدمين'),
                                   ('admins', 'المديرون فقط'),
                                   ('agents', 'موظفو المطالبات فقط'),
                                   ('specific', 'مستخدمون محددون')
                               ])

    specific_users = StringField('المستخدمون المحددون', validators=[Optional()],
                               description='أدخل أرقام المستخدمين مفصولة بفاصلة (مثال: 1,2,3)')

    # Scheduling
    send_immediately = BooleanField('إرسال فوري', default=True)
    scheduled_date = DateField('تاريخ الإرسال المجدول', validators=[Optional()])
    scheduled_time = TimeField('وقت الإرسال المجدول', validators=[Optional()])

    submit = SubmitField('إرسال الإشعار')


class NotificationTemplateForm(FlaskForm):
    """Form for managing notification templates"""
    name = StringField('اسم القالب', validators=[DataRequired(), Length(min=1, max=100)])
    event_type = SelectField('نوع الحدث', validators=[DataRequired()],
                           choices=[
                               ('claim_created', 'إنشاء مطالبة'),
                               ('claim_sent', 'إرسال مطالبة'),
                               ('claim_status_changed', 'تغيير حالة المطالبة'),
                               ('payment_received', 'استلام دفعة'),
                               ('system_maintenance', 'صيانة النظام'),
                               ('custom', 'مخصص')
                           ])

    notification_type = SelectField('نوع الإشعار', validators=[DataRequired()],
                                  choices=[
                                      ('email', 'بريد إلكتروني'),
                                      ('sms', 'رسالة نصية'),
                                      ('push', 'إشعار منبثق'),
                                      ('whatsapp', 'واتساب'),
                                      ('in_app', 'داخل التطبيق')
                                  ])

    # Arabic content
    subject_ar = StringField('العنوان (عربي)', validators=[Optional(), Length(max=200)])
    content_ar = TextAreaField('المحتوى (عربي)', validators=[DataRequired()],
                              widget=TextArea(), render_kw={'rows': 8})

    # English content
    subject_en = StringField('العنوان (إنجليزي)', validators=[Optional(), Length(max=200)])
    content_en = TextAreaField('المحتوى (إنجليزي)', validators=[Optional()],
                              widget=TextArea(), render_kw={'rows': 8})

    # Template variables
    variables = TextAreaField('المتغيرات المتاحة', validators=[Optional()],
                            description='قائمة بالمتغيرات المتاحة في القالب (مثال: claim_id, client_name)',
                            render_kw={'rows': 3})

    active = BooleanField('مفعل', default=True)

    submit = SubmitField('حفظ القالب')


class BulkNotificationForm(FlaskForm):
    """Form for sending bulk notifications"""
    batch_name = StringField('اسم المجموعة', validators=[DataRequired(), Length(min=1, max=100)])

    # Template or custom content
    use_template = BooleanField('استخدام قالب', default=False)
    template_id = SelectField('القالب', validators=[Optional()], coerce=int)

    # Custom content (if not using template)
    title = StringField('العنوان', validators=[Optional(), Length(max=200)])
    message = TextAreaField('الرسالة', validators=[Optional()],
                           widget=TextArea(), render_kw={'rows': 5})

    # Notification settings
    notification_type = SelectField('نوع الإشعار', validators=[DataRequired()],
                                  choices=[
                                      ('email', 'بريد إلكتروني'),
                                      ('sms', 'رسالة نصية'),
                                      ('push', 'إشعار منبثق'),
                                      ('whatsapp', 'واتساب'),
                                      ('in_app', 'داخل التطبيق')
                                  ])

    # Recipients
    recipient_filter = SelectField('فلتر المستلمين', validators=[DataRequired()],
                                 choices=[
                                     ('all', 'جميع المستخدمين النشطين'),
                                     ('role_admin', 'المديرون'),
                                     ('role_agent', 'موظفو المطالبات'),
                                     ('role_viewer', 'المشاهدون'),
                                     ('custom', 'قائمة مخصصة')
                                 ])

    custom_recipients = TextAreaField('قائمة المستلمين المخصصة', validators=[Optional()],
                                    description='أدخل عناوين البريد الإلكتروني أو أرقام الهواتف، كل واحد في سطر منفصل',
                                    render_kw={'rows': 5})

    # Scheduling
    scheduled_for = DateField('تاريخ الإرسال', validators=[Optional()])
    scheduled_time = TimeField('وقت الإرسال', validators=[Optional()])

    submit = SubmitField('إضافة إلى قائمة الانتظار')

class WhatsAppTestForm(FlaskForm):
    """Form for testing WhatsApp functionality"""
    phone_number = StringField('رقم الواتساب', validators=[DataRequired(), Length(max=20)],
                              render_kw={'placeholder': '+966501234567'})
    message = TextAreaField('الرسالة', validators=[DataRequired(), Length(max=500)],
                           default='مرحباً! هذه رسالة تجريبية من نظام إدارة مطالبات التأمين. ✅')
    use_business_api = BooleanField('استخدام WhatsApp Business API', default=False)
    submit = SubmitField('إرسال الرسالة')