/**
 * Dynamic Forms System
 * Handles dynamic form generation based on claim types
 */

class DynamicFormManager {
    constructor() {
        this.currentClaimType = null;
        this.dynamicFields = {};
        this.conditionalLogic = {};
        this.init();
    }

    init() {
        // Initialize event listeners
        this.bindEvents();
        
        // Load initial form if claim type is already selected
        const claimTypeSelect = document.getElementById('claim_type_id');
        if (claimTypeSelect && claimTypeSelect.value) {
            this.loadDynamicForm(claimTypeSelect.value);
        }
    }

    bindEvents() {
        // Claim type change event
        const claimTypeSelect = document.getElementById('claim_type_id');
        if (claimTypeSelect) {
            claimTypeSelect.addEventListener('change', (e) => {
                this.loadDynamicForm(e.target.value);
            });
        }

        // Form submission
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (!this.validateDynamicFields()) {
                    e.preventDefault();
                }
            });
        }
    }

    async loadDynamicForm(claimTypeId) {
        if (!claimTypeId) {
            this.clearDynamicFields();
            return;
        }

        try {
            // Show loading
            this.showLoading();

            // Fetch dynamic fields for this claim type
            const response = await fetch(`/api/claim-types/${claimTypeId}/fields`);
            const data = await response.json();

            if (data.success) {
                this.renderDynamicFields(data.fields);
                this.currentClaimType = claimTypeId;
            } else {
                this.showError('فشل في تحميل الحقول الديناميكية');
            }
        } catch (error) {
            console.error('Error loading dynamic form:', error);
            this.showError('حدث خطأ في تحميل النموذج');
        } finally {
            this.hideLoading();
        }
    }

    renderDynamicFields(fields) {
        const container = document.getElementById('dynamic-fields-container');
        if (!container) return;

        // Clear existing fields
        container.innerHTML = '';

        // Sort fields by order
        fields.sort((a, b) => a.field_order - b.field_order);

        // Create fields
        fields.forEach(field => {
            const fieldElement = this.createFieldElement(field);
            container.appendChild(fieldElement);
            
            // Store field info for validation
            this.dynamicFields[field.field_name] = field;
            
            // Setup conditional logic
            if (field.conditional_logic) {
                this.conditionalLogic[field.field_name] = field.conditional_logic;
                this.setupConditionalLogic(field);
            }
        });

        // Initialize conditional logic
        this.initializeConditionalLogic();
    }

    createFieldElement(field) {
        const wrapper = document.createElement('div');
        wrapper.className = 'col-md-6 mb-3 dynamic-field';
        wrapper.setAttribute('data-field-name', field.field_name);

        let fieldHtml = '';
        const fieldId = `dynamic_${field.field_name}`;
        const isRequired = field.required ? 'required' : '';
        const requiredStar = field.required ? '<span class="text-danger">*</span>' : '';

        // Field label
        fieldHtml += `<label for="${fieldId}" class="form-label">${field.field_label_ar} ${requiredStar}</label>`;

        // Field input based on type
        switch (field.field_type) {
            case 'text':
                fieldHtml += `<input type="text" class="form-control" id="${fieldId}" name="${field.field_name}" 
                             placeholder="${field.placeholder_ar || ''}" ${isRequired}
                             ${field.min_length ? `minlength="${field.min_length}"` : ''}
                             ${field.max_length ? `maxlength="${field.max_length}"` : ''}
                             ${field.pattern ? `pattern="${field.pattern}"` : ''}>`;
                break;

            case 'number':
                fieldHtml += `<input type="number" class="form-control" id="${fieldId}" name="${field.field_name}" 
                             placeholder="${field.placeholder_ar || ''}" ${isRequired}
                             ${field.min_value !== null ? `min="${field.min_value}"` : ''}
                             ${field.max_value !== null ? `max="${field.max_value}"` : ''}
                             step="0.01">`;
                break;

            case 'date':
                fieldHtml += `<input type="date" class="form-control" id="${fieldId}" name="${field.field_name}" ${isRequired}>`;
                break;

            case 'select':
                fieldHtml += `<select class="form-select" id="${fieldId}" name="${field.field_name}" ${isRequired}>`;
                fieldHtml += `<option value="">اختر...</option>`;
                if (field.field_options) {
                    field.field_options.forEach(option => {
                        fieldHtml += `<option value="${option.value}">${option.label_ar}</option>`;
                    });
                }
                fieldHtml += `</select>`;
                break;

            case 'textarea':
                fieldHtml += `<textarea class="form-control" id="${fieldId}" name="${field.field_name}" 
                             placeholder="${field.placeholder_ar || ''}" ${isRequired} rows="3"></textarea>`;
                break;

            case 'radio':
                if (field.field_options) {
                    field.field_options.forEach((option, index) => {
                        fieldHtml += `
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="${field.field_name}" 
                                       id="${fieldId}_${index}" value="${option.value}" ${isRequired}>
                                <label class="form-check-label" for="${fieldId}_${index}">
                                    ${option.label_ar}
                                </label>
                            </div>`;
                    });
                }
                break;

            case 'checkbox':
                if (field.field_options) {
                    field.field_options.forEach((option, index) => {
                        fieldHtml += `
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="${field.field_name}" 
                                       id="${fieldId}_${index}" value="${option.value}">
                                <label class="form-check-label" for="${fieldId}_${index}">
                                    ${option.label_ar}
                                </label>
                            </div>`;
                    });
                }
                break;

            case 'file':
                fieldHtml += `<input type="file" class="form-control" id="${fieldId}" name="${field.field_name}" 
                             ${field.field_options && field.field_options.multiple ? 'multiple' : ''}
                             accept="${field.field_options && field.field_options.accept ? field.field_options.accept : '.pdf,.jpg,.jpeg,.png,.docx'}">`;
                break;

            default:
                fieldHtml += `<input type="text" class="form-control" id="${fieldId}" name="${field.field_name}" 
                             placeholder="${field.placeholder_ar || ''}" ${isRequired}>`;
        }

        // Help text
        if (field.help_text_ar) {
            fieldHtml += `<small class="form-text text-muted">${field.help_text_ar}</small>`;
        }

        // Error container
        fieldHtml += `<div class="invalid-feedback" id="${fieldId}_error"></div>`;

        wrapper.innerHTML = fieldHtml;
        return wrapper;
    }

    setupConditionalLogic(field) {
        const logic = field.conditional_logic;
        if (!logic || !logic.depends_on) return;

        // Find the field this depends on
        const dependsOnField = document.querySelector(`[name="${logic.depends_on}"]`);
        if (!dependsOnField) return;

        // Add event listener
        dependsOnField.addEventListener('change', () => {
            this.evaluateConditionalLogic(field.field_name);
        });
    }

    initializeConditionalLogic() {
        // Evaluate all conditional logic on load
        Object.keys(this.conditionalLogic).forEach(fieldName => {
            this.evaluateConditionalLogic(fieldName);
        });
    }

    evaluateConditionalLogic(fieldName) {
        const logic = this.conditionalLogic[fieldName];
        if (!logic) return;

        const fieldWrapper = document.querySelector(`[data-field-name="${fieldName}"]`);
        if (!fieldWrapper) return;

        const dependsOnField = document.querySelector(`[name="${logic.depends_on}"]`);
        if (!dependsOnField) return;

        const dependsOnValue = this.getFieldValue(dependsOnField);
        let shouldShow = false;

        // Evaluate condition
        switch (logic.condition) {
            case 'equals':
                shouldShow = dependsOnValue === logic.value;
                break;
            case 'not_equals':
                shouldShow = dependsOnValue !== logic.value;
                break;
            case 'in':
                shouldShow = logic.value.includes(dependsOnValue);
                break;
            case 'not_in':
                shouldShow = !logic.value.includes(dependsOnValue);
                break;
            case 'greater_than':
                shouldShow = parseFloat(dependsOnValue) > parseFloat(logic.value);
                break;
            case 'less_than':
                shouldShow = parseFloat(dependsOnValue) < parseFloat(logic.value);
                break;
        }

        // Show/hide field
        if (shouldShow) {
            fieldWrapper.style.display = 'block';
            fieldWrapper.classList.remove('d-none');
        } else {
            fieldWrapper.style.display = 'none';
            fieldWrapper.classList.add('d-none');
            // Clear field value when hidden
            this.clearFieldValue(fieldWrapper);
        }
    }

    getFieldValue(field) {
        if (field.type === 'radio') {
            const checked = document.querySelector(`[name="${field.name}"]:checked`);
            return checked ? checked.value : '';
        } else if (field.type === 'checkbox') {
            const checked = document.querySelectorAll(`[name="${field.name}"]:checked`);
            return Array.from(checked).map(cb => cb.value);
        } else {
            return field.value;
        }
    }

    clearFieldValue(fieldWrapper) {
        const inputs = fieldWrapper.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
    }

    validateDynamicFields() {
        let isValid = true;
        
        Object.keys(this.dynamicFields).forEach(fieldName => {
            const field = this.dynamicFields[fieldName];
            const fieldWrapper = document.querySelector(`[data-field-name="${fieldName}"]`);
            
            // Skip hidden fields
            if (!fieldWrapper || fieldWrapper.style.display === 'none') {
                return;
            }

            const input = fieldWrapper.querySelector(`[name="${fieldName}"]`);
            if (!input) return;

            const value = this.getFieldValue(input);
            const errorElement = fieldWrapper.querySelector('.invalid-feedback');

            // Clear previous errors
            input.classList.remove('is-invalid');
            if (errorElement) errorElement.textContent = '';

            // Required validation
            if (field.required && (!value || value === '')) {
                this.showFieldError(input, errorElement, 'هذا الحقل مطلوب');
                isValid = false;
                return;
            }

            // Type-specific validation
            if (value && value !== '') {
                switch (field.field_type) {
                    case 'number':
                        if (isNaN(value)) {
                            this.showFieldError(input, errorElement, 'يجب أن يكون رقماً');
                            isValid = false;
                        } else {
                            const numValue = parseFloat(value);
                            if (field.min_value !== null && numValue < field.min_value) {
                                this.showFieldError(input, errorElement, `القيمة يجب أن تكون أكبر من ${field.min_value}`);
                                isValid = false;
                            }
                            if (field.max_value !== null && numValue > field.max_value) {
                                this.showFieldError(input, errorElement, `القيمة يجب أن تكون أقل من ${field.max_value}`);
                                isValid = false;
                            }
                        }
                        break;

                    case 'text':
                    case 'textarea':
                        if (field.min_length && value.length < field.min_length) {
                            this.showFieldError(input, errorElement, `يجب أن يكون النص أطول من ${field.min_length} أحرف`);
                            isValid = false;
                        }
                        if (field.max_length && value.length > field.max_length) {
                            this.showFieldError(input, errorElement, `يجب أن يكون النص أقصر من ${field.max_length} أحرف`);
                            isValid = false;
                        }
                        if (field.pattern && !new RegExp(field.pattern).test(value)) {
                            this.showFieldError(input, errorElement, 'تنسيق البيانات غير صحيح');
                            isValid = false;
                        }
                        break;
                }
            }
        });

        return isValid;
    }

    showFieldError(input, errorElement, message) {
        input.classList.add('is-invalid');
        if (errorElement) {
            errorElement.textContent = message;
        }
    }

    clearDynamicFields() {
        const container = document.getElementById('dynamic-fields-container');
        if (container) {
            container.innerHTML = '';
        }
        this.dynamicFields = {};
        this.conditionalLogic = {};
        this.currentClaimType = null;
    }

    showLoading() {
        const container = document.getElementById('dynamic-fields-container');
        if (container) {
            container.innerHTML = `
                <div class="col-12 text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">جاري التحميل...</span>
                    </div>
                    <p class="mt-2 text-muted">جاري تحميل الحقول...</p>
                </div>
            `;
        }
    }

    hideLoading() {
        // Loading will be replaced by actual fields
    }

    showError(message) {
        const container = document.getElementById('dynamic-fields-container');
        if (container) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${message}
                    </div>
                </div>
            `;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dynamicFormManager = new DynamicFormManager();
});

// Utility functions for external use
window.DynamicFormUtils = {
    // Get all dynamic form data
    getDynamicFormData: function() {
        const data = {};
        const dynamicFields = document.querySelectorAll('.dynamic-field input, .dynamic-field select, .dynamic-field textarea');
        
        dynamicFields.forEach(field => {
            if (field.type === 'checkbox') {
                if (!data[field.name]) data[field.name] = [];
                if (field.checked) data[field.name].push(field.value);
            } else if (field.type === 'radio') {
                if (field.checked) data[field.name] = field.value;
            } else {
                data[field.name] = field.value;
            }
        });
        
        return data;
    },

    // Set dynamic form data
    setDynamicFormData: function(data) {
        Object.keys(data).forEach(fieldName => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (field) {
                if (field.type === 'checkbox' || field.type === 'radio') {
                    const values = Array.isArray(data[fieldName]) ? data[fieldName] : [data[fieldName]];
                    values.forEach(value => {
                        const specificField = document.querySelector(`[name="${fieldName}"][value="${value}"]`);
                        if (specificField) specificField.checked = true;
                    });
                } else {
                    field.value = data[fieldName];
                }
            }
        });
    }
};