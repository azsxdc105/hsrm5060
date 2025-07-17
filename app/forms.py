from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DecimalField, DateField, HiddenField, PasswordField, BooleanField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo
from wtforms.widgets import TextArea
from app.models import InsuranceCompany

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

class UserForm(FlaskForm):
    full_name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[EqualTo('password')])
    role = SelectField('الدور', validators=[DataRequired()],
                      choices=[
                          ('admin', 'مدير'),
                          ('claims_agent', 'موظف مطالبات'),
                          ('viewer', 'مشاهد')
                      ])
    active = BooleanField('نشط', default=True)

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

class SearchForm(FlaskForm):
    search_term = StringField('البحث', validators=[Optional()])
    company_id = SelectField('شركة التأمين', validators=[Optional()], coerce=int)
    status = SelectField('الحالة', validators=[Optional()],
                        choices=[
                            ('', 'الكل'),
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
        self.company_id.choices = [('', 'الكل')] + [(c.id, c.name_ar) for c in InsuranceCompany.query.filter_by(active=True).all()]