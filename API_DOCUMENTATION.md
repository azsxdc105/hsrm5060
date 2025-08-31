# نظام إدارة مطالبات التأمين - وثائق API

## نظرة عامة

يوفر هذا النظام REST API شامل للتكامل مع الأنظمة الخارجية. جميع endpoints تتطلب مصادقة JWT باستثناء endpoint تسجيل الدخول.

**Base URL:** `http://localhost:5000/api/v1`

## المصادقة

### تسجيل الدخول
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "admin@claims.com",
    "password": "admin123"
}
```

**الاستجابة:**
```json
{
    "success": true,
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "admin@claims.com",
        "full_name": "مدير النظام",
        "role": "admin"
    },
    "expires_in": 86400
}
```

### تجديد الرمز المميز
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

### استخدام الرمز المميز
جميع الطلبات الأخرى تتطلب إضافة header:
```http
Authorization: Bearer <access_token>
```

## إدارة المطالبات

### الحصول على قائمة المطالبات
```http
GET /api/v1/claims?page=1&per_page=20&status=sent&company_id=1&start_date=2025-01-01&end_date=2025-12-31
Authorization: Bearer <access_token>
```

**المعاملات:**
- `page`: رقم الصفحة (افتراضي: 1)
- `per_page`: عدد العناصر في الصفحة (افتراضي: 20، الحد الأقصى: 100)
- `status`: فلترة حسب الحالة (draft, ready, sent, failed, acknowledged, paid)
- `company_id`: فلترة حسب شركة التأمين
- `start_date`: تاريخ البداية (YYYY-MM-DD)
- `end_date`: تاريخ النهاية (YYYY-MM-DD)

### إنشاء مطالبة جديدة
```http
POST /api/v1/claims
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "company_id": 1,
    "client_name": "أحمد محمد",
    "client_national_id": "1234567890",
    "policy_number": "POL-2025-001",
    "incident_number": "INC-2025-001",
    "incident_date": "2025-01-15",
    "claim_amount": 5000.00,
    "currency": "SAR",
    "coverage_type": "comprehensive",
    "claim_details": "تفاصيل المطالبة...",
    "city": "الرياض",
    "tags": "حادث,سيارة"
}
```

### الحصول على تفاصيل مطالبة
```http
GET /api/v1/claims/{claim_id}
Authorization: Bearer <access_token>
```

### تحديث مطالبة
```http
PUT /api/v1/claims/{claim_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "client_name": "أحمد محمد علي",
    "claim_amount": 5500.00,
    "claim_details": "تفاصيل محدثة..."
}
```

### تحديث حالة المطالبة
```http
PUT /api/v1/claims/{claim_id}/status
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "status": "paid"
}
```

## إدارة شركات التأمين

### الحصول على قائمة الشركات
```http
GET /api/v1/companies?active_only=true
Authorization: Bearer <access_token>
```

### الحصول على تفاصيل شركة
```http
GET /api/v1/companies/{company_id}
Authorization: Bearer <access_token>
```

### إنشاء شركة جديدة (مدير فقط)
```http
POST /api/v1/companies
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name_ar": "شركة التأمين الجديدة",
    "name_en": "New Insurance Company",
    "claims_email_primary": "claims@newinsurance.com",
    "claims_email_cc": "backup@newinsurance.com",
    "policy_portal_url": "https://portal.newinsurance.com",
    "notes": "ملاحظات...",
    "active": true
}
```

## التقارير والإحصائيات

### تقرير شامل
```http
GET /api/v1/reports?type=overview&start_date=2025-01-01&end_date=2025-01-31
Authorization: Bearer <access_token>
```

**أنواع التقارير:**
- `overview`: تقرير شامل
- `status`: توزيع حسب الحالة
- `companies`: أداء الشركات

### التحليلات المتقدمة
```http
GET /api/v1/analytics?period=30&metric=all
Authorization: Bearer <access_token>
```

**المعاملات:**
- `period`: فترة بالأيام (افتراضي: 30)
- `metric`: نوع المقياس (all, trends, performance)

## إدارة المستخدمين (مدير فقط)

### الحصول على قائمة المستخدمين
```http
GET /api/v1/users?active_only=true&role=claims_agent
Authorization: Bearer <access_token>
```

### إنشاء مستخدم جديد
```http
POST /api/v1/users
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "full_name": "موظف جديد",
    "email": "employee@company.com",
    "password": "secure_password",
    "role": "claims_agent",
    "active": true
}
```

## رموز الاستجابة

- `200 OK`: نجح الطلب
- `201 Created`: تم إنشاء المورد بنجاح
- `400 Bad Request`: خطأ في البيانات المرسلة
- `401 Unauthorized`: مطلوب مصادقة
- `403 Forbidden`: غير مسموح بالوصول
- `404 Not Found`: المورد غير موجود
- `409 Conflict`: تعارض في البيانات
- `500 Internal Server Error`: خطأ في الخادم

## أمثلة الاستخدام

### Python
```python
import requests

# تسجيل الدخول
login_response = requests.post('http://localhost:5000/api/v1/auth/login', json={
    'email': 'admin@claims.com',
    'password': 'admin123'
})
token = login_response.json()['access_token']

# الحصول على المطالبات
headers = {'Authorization': f'Bearer {token}'}
claims_response = requests.get('http://localhost:5000/api/v1/claims', headers=headers)
claims = claims_response.json()['claims']
```

### JavaScript
```javascript
// تسجيل الدخول
const loginResponse = await fetch('http://localhost:5000/api/v1/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'admin@claims.com',
        password: 'admin123'
    })
});
const {access_token} = await loginResponse.json();

// إنشاء مطالبة جديدة
const claimResponse = await fetch('http://localhost:5000/api/v1/claims', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${access_token}`
    },
    body: JSON.stringify({
        company_id: 1,
        client_name: 'أحمد محمد',
        client_national_id: '1234567890',
        incident_date: '2025-01-15',
        claim_amount: 5000.00,
        coverage_type: 'comprehensive',
        claim_details: 'تفاصيل المطالبة'
    })
});
```

## الأمان

- جميع كلمات المرور مشفرة باستخدام bcrypt
- الرموز المميزة JWT صالحة لمدة 24 ساعة
- رموز التجديد صالحة لمدة 30 يوم
- CORS مفعل للـ API endpoints
- التحقق من الأدوار والصلاحيات

## معدل الطلبات

حالياً لا يوجد حد لمعدل الطلبات، لكن يُنصح بعدم تجاوز 100 طلب في الدقيقة.

## الدعم

للحصول على الدعم أو الإبلاغ عن مشاكل، يرجى التواصل مع فريق التطوير.
