#!/usr/bin/env python3
"""
AI Classification Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import json

from app import db
from app.models import Claim, ClaimClassification, FraudIndicator, User
from app.ai_classification import classify_claim_ai, get_fraud_risk_assessment, ai_classifier
from app.notification_services import send_claim_notification

ai_classification_bp = Blueprint('ai_classification', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('يجب أن تكون مديراً للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@ai_classification_bp.route('/')
@login_required
@admin_required
def index():
    """AI Classification dashboard"""
    # Get classification statistics
    total_classified = ClaimClassification.query.count()
    high_risk_count = ClaimClassification.query.filter_by(risk_level='high').count()
    fraud_suspects = ClaimClassification.query.filter(ClaimClassification.fraud_probability > 0.5).count()
    pending_review = ClaimClassification.query.filter_by(reviewed_by_user_id=None).count()
    
    # Get recent classifications
    recent_classifications = ClaimClassification.query\
        .order_by(ClaimClassification.created_at.desc())\
        .limit(10).all()
    
    # Get category distribution
    category_stats = db.session.query(
        ClaimClassification.category,
        db.func.count(ClaimClassification.id).label('count')
    ).group_by(ClaimClassification.category).all()
    
    stats = {
        'total_classified': total_classified,
        'high_risk_count': high_risk_count,
        'fraud_suspects': fraud_suspects,
        'pending_review': pending_review,
        'category_stats': [{'category': cat, 'count': count} for cat, count in category_stats]
    }
    
    return render_template('ai_classification/index.html',
                         stats=stats,
                         recent_classifications=recent_classifications)


@ai_classification_bp.route('/classify/<string:claim_id>')
@login_required
@admin_required
def classify_claim(claim_id):
    """Classify a specific claim"""
    claim = Claim.query.get_or_404(claim_id)
    
    # Check if already classified
    existing_classification = ClaimClassification.query.filter_by(claim_id=claim_id).first()
    if existing_classification:
        flash('هذه المطالبة مصنفة مسبقاً', 'info')
        return redirect(url_for('ai_classification.view_classification', claim_id=claim_id))
    
    try:
        # Run AI classification
        result = classify_claim_ai(claim)
        
        # Save classification to database
        classification = ClaimClassification(
            claim_id=claim_id,
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
        
        # Send notification if high risk or high fraud probability
        if result.risk_level == 'high' or result.fraud_probability > 0.6:
            try:
                send_claim_notification(
                    'claim_high_risk_detected',
                    claim,
                    custom_message=f'تم اكتشاف مطالبة عالية المخاطر: {claim.id}. '
                                 f'مستوى المخاطر: {result.risk_level}، '
                                 f'احتمالية الاحتيال: {result.fraud_probability:.1%}',
                    priority='high'
                )
            except Exception as e:
                logger.error(f"Failed to send high risk notification: {e}")
        
        flash(f'تم تصنيف المطالبة بنجاح. الفئة: {classification.get_category_display_name()}', 'success')
        return redirect(url_for('ai_classification.view_classification', claim_id=claim_id))
        
    except Exception as e:
        flash(f'حدث خطأ أثناء التصنيف: {str(e)}', 'error')
        return redirect(url_for('claims.view', id=claim_id))


@ai_classification_bp.route('/view/<string:claim_id>')
@login_required
def view_classification(claim_id):
    """View classification results for a claim"""
    claim = Claim.query.get_or_404(claim_id)
    classification = ClaimClassification.query.filter_by(claim_id=claim_id).first_or_404()
    
    # Get fraud indicators
    fraud_indicators = FraudIndicator.query.filter_by(classification_id=classification.id).all()
    
    return render_template('ai_classification/view.html',
                         claim=claim,
                         classification=classification,
                         fraud_indicators=fraud_indicators)


@ai_classification_bp.route('/review/<string:claim_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def review_classification(claim_id):
    """Review and potentially override AI classification"""
    claim = Claim.query.get_or_404(claim_id)
    classification = ClaimClassification.query.filter_by(claim_id=claim_id).first_or_404()
    
    if request.method == 'POST':
        # Get form data
        manual_category = request.form.get('manual_category')
        manual_risk = request.form.get('manual_risk')
        review_notes = request.form.get('review_notes')
        
        # Update classification
        classification.mark_as_reviewed(
            user_id=current_user.id,
            notes=review_notes,
            manual_category=manual_category if manual_category != classification.category else None,
            manual_risk=manual_risk if manual_risk != classification.risk_level else None
        )
        
        db.session.commit()
        
        flash('تم مراجعة التصنيف بنجاح', 'success')
        return redirect(url_for('ai_classification.view_classification', claim_id=claim_id))
    
    # Get available categories and risk levels
    categories = {
        'vehicle_accident': 'حادث مركبة',
        'medical': 'طبي',
        'property_damage': 'أضرار الممتلكات',
        'theft': 'سرقة',
        'natural_disaster': 'كارثة طبيعية',
        'unknown': 'غير محدد'
    }
    
    risk_levels = {
        'low': 'منخفض',
        'medium': 'متوسط',
        'high': 'عالي'
    }
    
    return render_template('ai_classification/review.html',
                         claim=claim,
                         classification=classification,
                         categories=categories,
                         risk_levels=risk_levels)


@ai_classification_bp.route('/batch_classify', methods=['POST'])
@login_required
@admin_required
def batch_classify():
    """Classify multiple unclassified claims"""
    try:
        # Get unclassified claims
        classified_claim_ids = db.session.query(ClaimClassification.claim_id).all()
        classified_ids = [row[0] for row in classified_claim_ids]
        
        unclassified_claims = Claim.query.filter(
            ~Claim.id.in_(classified_ids)
        ).limit(50).all()  # Process 50 at a time
        
        if not unclassified_claims:
            return jsonify({'success': True, 'message': 'لا توجد مطالبات غير مصنفة', 'count': 0})
        
        classified_count = 0
        high_risk_count = 0
        
        for claim in unclassified_claims:
            try:
                # Run AI classification
                result = classify_claim_ai(claim)
                
                # Save classification
                classification = ClaimClassification(
                    claim_id=claim.id,
                    category=result.category,
                    confidence=result.confidence,
                    risk_level=result.risk_level,
                    fraud_probability=result.fraud_probability,
                    suggested_amount=result.suggested_amount
                )
                
                if result.reasoning:
                    classification.set_reasoning_list(result.reasoning)
                
                db.session.add(classification)
                classified_count += 1
                
                if result.risk_level == 'high':
                    high_risk_count += 1
                
            except Exception as e:
                logger.error(f"Failed to classify claim {claim.id}: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم تصنيف {classified_count} مطالبة بنجاح',
            'count': classified_count,
            'high_risk_count': high_risk_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@ai_classification_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """View detailed AI classification statistics"""
    # Category distribution
    category_stats = db.session.query(
        ClaimClassification.category,
        db.func.count(ClaimClassification.id).label('count'),
        db.func.avg(ClaimClassification.confidence).label('avg_confidence'),
        db.func.avg(ClaimClassification.fraud_probability).label('avg_fraud_prob')
    ).group_by(ClaimClassification.category).all()
    
    # Risk level distribution
    risk_stats = db.session.query(
        ClaimClassification.risk_level,
        db.func.count(ClaimClassification.id).label('count')
    ).group_by(ClaimClassification.risk_level).all()
    
    # Monthly classification trends
    monthly_stats = db.session.query(
        db.func.date_trunc('month', ClaimClassification.created_at).label('month'),
        db.func.count(ClaimClassification.id).label('count')
    ).group_by(db.func.date_trunc('month', ClaimClassification.created_at))\
     .order_by(db.func.date_trunc('month', ClaimClassification.created_at)).all()
    
    # Fraud detection stats
    fraud_stats = {
        'high_risk': ClaimClassification.query.filter(ClaimClassification.fraud_probability > 0.7).count(),
        'medium_risk': ClaimClassification.query.filter(
            ClaimClassification.fraud_probability.between(0.3, 0.7)
        ).count(),
        'low_risk': ClaimClassification.query.filter(ClaimClassification.fraud_probability < 0.3).count()
    }
    
    # Manual review stats
    review_stats = {
        'reviewed': ClaimClassification.query.filter(ClaimClassification.reviewed_by_user_id.isnot(None)).count(),
        'pending': ClaimClassification.query.filter(ClaimClassification.reviewed_by_user_id.is_(None)).count(),
        'overridden': ClaimClassification.query.filter_by(manual_override=True).count()
    }
    
    return render_template('ai_classification/statistics.html',
                         category_stats=category_stats,
                         risk_stats=risk_stats,
                         monthly_stats=monthly_stats,
                         fraud_stats=fraud_stats,
                         review_stats=review_stats)


@ai_classification_bp.route('/api/classify/<string:claim_id>')
@login_required
def api_classify_claim(claim_id):
    """API endpoint to get classification for a claim"""
    try:
        classification = ClaimClassification.query.filter_by(claim_id=claim_id).first()
        
        if not classification:
            return jsonify({'success': False, 'error': 'Classification not found'})
        
        return jsonify({
            'success': True,
            'classification': {
                'category': classification.get_category_display_name(),
                'confidence': classification.confidence,
                'risk_level': classification.get_risk_level_display_name(),
                'fraud_probability': classification.fraud_probability,
                'suggested_amount': float(classification.suggested_amount) if classification.suggested_amount else None,
                'reasoning': classification.get_reasoning_list(),
                'is_reviewed': classification.reviewed_by_user_id is not None,
                'manual_override': classification.manual_override
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@ai_classification_bp.route('/api/fraud_assessment/<string:claim_id>')
@login_required
def api_fraud_assessment(claim_id):
    """API endpoint to get fraud risk assessment"""
    try:
        claim = Claim.query.get_or_404(claim_id)
        assessment = get_fraud_risk_assessment(claim)

        return jsonify({
            'success': True,
            'assessment': assessment
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@ai_classification_bp.route('/api/statistics')
@login_required
def api_statistics():
    """API endpoint for dashboard statistics"""
    try:
        total_classified = ClaimClassification.query.count()
        high_risk_count = ClaimClassification.query.filter_by(risk_level='high').count()
        fraud_suspects = ClaimClassification.query.filter(ClaimClassification.fraud_probability > 0.5).count()
        pending_review = ClaimClassification.query.filter_by(reviewed_by_user_id=None).count()

        return jsonify({
            'success': True,
            'total_classified': total_classified,
            'high_risk_count': high_risk_count,
            'fraud_suspects': fraud_suspects,
            'pending_review': pending_review
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@ai_classification_bp.route('/pending_review')
@login_required
@admin_required
def pending_review():
    """View claims pending manual review"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get classifications pending review, prioritize high risk and high fraud probability
    classifications = ClaimClassification.query\
        .filter_by(reviewed_by_user_id=None)\
        .order_by(
            ClaimClassification.risk_level.desc(),
            ClaimClassification.fraud_probability.desc(),
            ClaimClassification.created_at.desc()
        )\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('ai_classification/pending_review.html',
                         classifications=classifications)
