/**
 * UI Enhancements and User Experience Improvements
 */

// Global loading state management
class LoadingManager {
    constructor() {
        this.activeRequests = 0;
        this.loadingOverlay = null;
        this.init();
    }

    init() {
        // Create loading overlay
        this.createLoadingOverlay();
        
        // Intercept all AJAX requests
        this.interceptAjaxRequests();
        
        // Add loading to forms
        this.enhanceForms();
        
        // Add loading to buttons
        this.enhanceButtons();
    }

    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">جاري التحميل...</span>
                </div>
                <div class="loading-text mt-3">جاري التحميل...</div>
            </div>
        `;
        document.body.appendChild(overlay);
        this.loadingOverlay = overlay;
    }

    show(message = 'جاري التحميل...') {
        this.activeRequests++;
        if (this.loadingOverlay) {
            this.loadingOverlay.querySelector('.loading-text').textContent = message;
            this.loadingOverlay.style.display = 'flex';
        }
    }

    hide() {
        this.activeRequests = Math.max(0, this.activeRequests - 1);
        if (this.activeRequests === 0 && this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }

    interceptAjaxRequests() {
        // Intercept fetch requests
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            this.show();
            return originalFetch(...args).finally(() => this.hide());
        };

        // Intercept jQuery AJAX if available
        if (window.jQuery) {
            $(document).ajaxStart(() => this.show());
            $(document).ajaxStop(() => this.hide());
        }
    }

    enhanceForms() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM') {
                this.show('جاري الإرسال...');
                
                // Add loading state to submit button
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    const originalText = submitBtn.textContent || submitBtn.value;
                    submitBtn.dataset.originalText = originalText;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>جاري الإرسال...';
                }
            }
        });
    }

    enhanceButtons() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button[data-loading]');
            if (button && !button.disabled) {
                const loadingText = button.dataset.loading || 'جاري التحميل...';
                this.showButtonLoading(button, loadingText);
            }
        });
    }

    showButtonLoading(button, text) {
        button.disabled = true;
        const originalText = button.innerHTML;
        button.dataset.originalText = originalText;
        button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${text}`;
        
        // Auto-restore after 10 seconds if not manually restored
        setTimeout(() => {
            if (button.dataset.originalText) {
                this.hideButtonLoading(button);
            }
        }, 10000);
    }

    hideButtonLoading(button) {
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
            button.disabled = false;
            delete button.dataset.originalText;
        }
    }
}

// Toast notification system
class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create toast container
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        this.container = container;
    }

    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${this.getIcon(type)} ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        this.container.appendChild(toast);

        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();

        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });

        return toast;
    }

    getIcon(type) {
        const icons = {
            'success': '<i class="fas fa-check-circle me-2"></i>',
            'error': '<i class="fas fa-exclamation-circle me-2"></i>',
            'warning': '<i class="fas fa-exclamation-triangle me-2"></i>',
            'info': '<i class="fas fa-info-circle me-2"></i>',
            'danger': '<i class="fas fa-times-circle me-2"></i>'
        };
        return icons[type] || icons['info'];
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'danger', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// Progress bar for file uploads
class ProgressManager {
    constructor() {
        this.progressBars = new Map();
    }

    create(id, container) {
        const progressHtml = `
            <div class="progress mb-3" id="progress-${id}">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%">
                    <span class="progress-text">0%</span>
                </div>
            </div>
        `;
        
        if (typeof container === 'string') {
            container = document.querySelector(container);
        }
        
        container.insertAdjacentHTML('beforeend', progressHtml);
        
        const progressElement = document.getElementById(`progress-${id}`);
        this.progressBars.set(id, progressElement);
        
        return progressElement;
    }

    update(id, percentage, text = null) {
        const progressElement = this.progressBars.get(id);
        if (progressElement) {
            const progressBar = progressElement.querySelector('.progress-bar');
            const progressText = progressElement.querySelector('.progress-text');
            
            progressBar.style.width = `${percentage}%`;
            progressText.textContent = text || `${percentage}%`;
            
            if (percentage >= 100) {
                progressBar.classList.remove('progress-bar-animated');
                progressBar.classList.add('bg-success');
                progressText.textContent = 'مكتمل';
            }
        }
    }

    remove(id) {
        const progressElement = this.progressBars.get(id);
        if (progressElement) {
            progressElement.remove();
            this.progressBars.delete(id);
        }
    }
}

// Form validation enhancements
class FormValidator {
    constructor() {
        this.init();
    }

    init() {
        // Add real-time validation
        document.addEventListener('input', (e) => {
            if (e.target.matches('input, textarea, select')) {
                this.validateField(e.target);
            }
        });

        // Add form submission validation
        document.addEventListener('submit', (e) => {
            if (e.target.tagName === 'FORM') {
                if (!this.validateForm(e.target)) {
                    e.preventDefault();
                }
            }
        });
    }

    validateField(field) {
        const value = field.value.trim();
        const fieldType = field.type;
        const isRequired = field.hasAttribute('required');
        
        let isValid = true;
        let message = '';

        // Required field validation
        if (isRequired && !value) {
            isValid = false;
            message = 'هذا الحقل مطلوب';
        }

        // Email validation
        if (fieldType === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'البريد الإلكتروني غير صحيح';
            }
        }

        // Phone validation
        if (field.name === 'phone' && value) {
            const phoneRegex = /^[0-9+\-\s()]+$/;
            if (!phoneRegex.test(value) || value.length < 10) {
                isValid = false;
                message = 'رقم الهاتف غير صحيح';
            }
        }

        // National ID validation
        if (field.name === 'client_national_id' && value) {
            if (value.length !== 10 || !/^\d+$/.test(value)) {
                isValid = false;
                message = 'رقم الهوية يجب أن يكون 10 أرقام';
            }
        }

        this.showFieldValidation(field, isValid, message);
        return isValid;
    }

    validateForm(form) {
        const fields = form.querySelectorAll('input, textarea, select');
        let isFormValid = true;

        fields.forEach(field => {
            if (!this.validateField(field)) {
                isFormValid = false;
            }
        });

        return isFormValid;
    }

    showFieldValidation(field, isValid, message) {
        // Remove existing validation
        field.classList.remove('is-valid', 'is-invalid');
        const existingFeedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }

        if (field.value.trim()) {
            if (isValid) {
                field.classList.add('is-valid');
            } else {
                field.classList.add('is-invalid');
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = message;
                field.parentNode.appendChild(feedback);
            }
        }
    }
}

// Auto-save functionality
class AutoSave {
    constructor(formSelector, saveUrl, interval = 30000) {
        this.form = document.querySelector(formSelector);
        this.saveUrl = saveUrl;
        this.interval = interval;
        this.lastSaved = {};
        this.saveTimer = null;
        
        if (this.form) {
            this.init();
        }
    }

    init() {
        // Save initial state
        this.lastSaved = this.getFormData();
        
        // Add change listeners
        this.form.addEventListener('input', () => {
            this.scheduleAutoSave();
        });

        // Add visual indicator
        this.createSaveIndicator();
    }

    scheduleAutoSave() {
        if (this.saveTimer) {
            clearTimeout(this.saveTimer);
        }
        
        this.saveTimer = setTimeout(() => {
            this.autoSave();
        }, this.interval);
    }

    async autoSave() {
        const currentData = this.getFormData();
        
        // Check if data has changed
        if (JSON.stringify(currentData) === JSON.stringify(this.lastSaved)) {
            return;
        }

        try {
            this.showSaveStatus('saving');
            
            const response = await fetch(this.saveUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(currentData)
            });

            if (response.ok) {
                this.lastSaved = currentData;
                this.showSaveStatus('saved');
            } else {
                this.showSaveStatus('error');
            }
        } catch (error) {
            this.showSaveStatus('error');
        }
    }

    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        return data;
    }

    createSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'auto-save-indicator';
        indicator.className = 'auto-save-indicator';
        indicator.innerHTML = '<i class="fas fa-save me-1"></i><span>محفوظ</span>';
        this.form.appendChild(indicator);
    }

    showSaveStatus(status) {
        const indicator = document.getElementById('auto-save-indicator');
        if (!indicator) return;

        const icon = indicator.querySelector('i');
        const text = indicator.querySelector('span');

        indicator.className = 'auto-save-indicator';
        
        switch (status) {
            case 'saving':
                icon.className = 'fas fa-spinner fa-spin me-1';
                text.textContent = 'جاري الحفظ...';
                indicator.classList.add('saving');
                break;
            case 'saved':
                icon.className = 'fas fa-check me-1';
                text.textContent = 'محفوظ';
                indicator.classList.add('saved');
                setTimeout(() => {
                    indicator.classList.remove('saved');
                }, 2000);
                break;
            case 'error':
                icon.className = 'fas fa-exclamation-triangle me-1';
                text.textContent = 'خطأ في الحفظ';
                indicator.classList.add('error');
                setTimeout(() => {
                    indicator.classList.remove('error');
                }, 3000);
                break;
        }
    }
}

// Initialize all enhancements when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize managers
    window.loadingManager = new LoadingManager();
    window.toastManager = new ToastManager();
    window.progressManager = new ProgressManager();
    window.formValidator = new FormValidator();

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+S to save forms
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            const form = document.querySelector('form');
            if (form) {
                form.submit();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modal = document.querySelector('.modal.show');
            if (modal) {
                bootstrap.Modal.getInstance(modal).hide();
            }
        }
    });

    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add tooltips to all elements with title attribute
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add confirmation dialogs to dangerous actions
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'هل أنت متأكد؟';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});

// Export for global use
window.UIEnhancements = {
    LoadingManager,
    ToastManager,
    ProgressManager,
    FormValidator,
    AutoSave
};
