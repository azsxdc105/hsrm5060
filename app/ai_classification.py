#!/usr/bin/env python3
"""
AI-Powered Claims Classification System
Automatically classifies claims, suggests compensation amounts, and detects potential fraud
"""
import logging
import re
import json
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from collections import Counter
import math

from app import db
from app.models import Claim, InsuranceCompany, User

logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    """Result of claim classification"""
    category: str
    confidence: float
    subcategory: Optional[str] = None
    risk_level: str = 'medium'  # low, medium, high
    suggested_amount: Optional[float] = None
    fraud_probability: float = 0.0
    reasoning: List[str] = None
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []

@dataclass
class FraudIndicator:
    """Fraud detection indicator"""
    indicator: str
    severity: str  # low, medium, high
    description: str
    confidence: float

class AIClaimsClassifier:
    """AI-powered claims classification system"""
    
    def __init__(self):
        self.categories = {
            'vehicle_accident': {
                'name_ar': 'حادث مركبة',
                'name_en': 'Vehicle Accident',
                'keywords_ar': ['حادث', 'تصادم', 'سيارة', 'مركبة', 'طريق', 'اصطدام', 'انقلاب'],
                'keywords_en': ['accident', 'collision', 'car', 'vehicle', 'road', 'crash', 'rollover'],
                'typical_range': (1000, 50000),
                'high_risk_threshold': 30000
            },
            'medical': {
                'name_ar': 'طبي',
                'name_en': 'Medical',
                'keywords_ar': ['طبي', 'مستشفى', 'علاج', 'طبيب', 'دواء', 'عملية', 'إصابة', 'مرض'],
                'keywords_en': ['medical', 'hospital', 'treatment', 'doctor', 'medicine', 'surgery', 'injury', 'illness'],
                'typical_range': (500, 100000),
                'high_risk_threshold': 50000
            },
            'property_damage': {
                'name_ar': 'أضرار الممتلكات',
                'name_en': 'Property Damage',
                'keywords_ar': ['منزل', 'بيت', 'مبنى', 'حريق', 'فيضان', 'سرقة', 'كسر', 'تلف'],
                'keywords_en': ['house', 'home', 'building', 'fire', 'flood', 'theft', 'break', 'damage'],
                'typical_range': (2000, 200000),
                'high_risk_threshold': 100000
            },
            'theft': {
                'name_ar': 'سرقة',
                'name_en': 'Theft',
                'keywords_ar': ['سرقة', 'سطو', 'اختلاس', 'فقدان', 'اختفاء', 'نهب'],
                'keywords_en': ['theft', 'robbery', 'burglary', 'loss', 'missing', 'stolen'],
                'typical_range': (500, 30000),
                'high_risk_threshold': 20000
            },
            'natural_disaster': {
                'name_ar': 'كارثة طبيعية',
                'name_en': 'Natural Disaster',
                'keywords_ar': ['زلزال', 'فيضان', 'عاصفة', 'برد', 'رياح', 'أمطار', 'كارثة'],
                'keywords_en': ['earthquake', 'flood', 'storm', 'hail', 'wind', 'rain', 'disaster'],
                'typical_range': (5000, 500000),
                'high_risk_threshold': 200000
            }
        }
        
        self.fraud_patterns = [
            {
                'pattern': r'مبلغ كبير|مبلغ ضخم|مبلغ هائل',
                'severity': 'medium',
                'description': 'استخدام كلمات تشير إلى مبالغ كبيرة'
            },
            {
                'pattern': r'عاجل جداً|ضروري فوراً|يجب الدفع اليوم',
                'severity': 'high',
                'description': 'إلحاح مشبوه في الطلب'
            },
            {
                'pattern': r'لا يوجد شهود|لا أحد رأى|وحدي',
                'severity': 'medium',
                'description': 'عدم وجود شهود قد يكون مشبوهاً'
            }
        ]
    
    def classify_claim(self, claim: Claim) -> ClassificationResult:
        """Classify a claim using AI techniques"""
        try:
            # Extract text features
            text_content = self._extract_text_content(claim)
            
            # Classify category
            category, confidence = self._classify_category(text_content)
            
            # Determine risk level
            risk_level = self._assess_risk_level(claim, category)
            
            # Suggest compensation amount
            suggested_amount = self._suggest_compensation(claim, category)
            
            # Detect fraud probability
            fraud_probability, fraud_indicators = self._detect_fraud(claim, text_content)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(claim, category, confidence, risk_level, fraud_probability)
            
            return ClassificationResult(
                category=category,
                confidence=confidence,
                risk_level=risk_level,
                suggested_amount=suggested_amount,
                fraud_probability=fraud_probability,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error classifying claim {claim.id}: {e}")
            return ClassificationResult(
                category='unknown',
                confidence=0.0,
                reasoning=[f'خطأ في التصنيف: {str(e)}']
            )
    
    def _extract_text_content(self, claim: Claim) -> str:
        """Extract all text content from claim"""
        content_parts = []
        
        if claim.claim_details:
            content_parts.append(claim.claim_details)
        
        if claim.client_name:
            content_parts.append(claim.client_name)
        
        if claim.city:
            content_parts.append(claim.city)
        
        # Add tags if available
        if hasattr(claim, 'tags') and claim.tags:
            content_parts.append(claim.tags)
        
        return ' '.join(content_parts).lower()
    
    def _classify_category(self, text_content: str) -> Tuple[str, float]:
        """Classify claim category based on text content"""
        category_scores = {}
        
        for category_id, category_info in self.categories.items():
            score = 0
            keyword_matches = 0
            
            # Check Arabic keywords
            for keyword in category_info['keywords_ar']:
                if keyword in text_content:
                    score += 1
                    keyword_matches += 1
            
            # Check English keywords
            for keyword in category_info['keywords_en']:
                if keyword in text_content:
                    score += 1
                    keyword_matches += 1
            
            # Calculate confidence based on keyword density
            if keyword_matches > 0:
                confidence = min(keyword_matches / len(category_info['keywords_ar']), 1.0)
                category_scores[category_id] = confidence
        
        if not category_scores:
            return 'unknown', 0.0
        
        # Return category with highest score
        best_category = max(category_scores.items(), key=lambda x: x[1])
        return best_category[0], best_category[1]
    
    def _assess_risk_level(self, claim: Claim, category: str) -> str:
        """Assess risk level of the claim"""
        risk_factors = []
        
        # Amount-based risk
        if category in self.categories:
            high_threshold = self.categories[category]['high_risk_threshold']
            if float(claim.claim_amount) > high_threshold:
                risk_factors.append('high_amount')
        
        # Time-based risk (very recent claims might be suspicious)
        if claim.incident_date and claim.created_at:
            days_diff = (claim.created_at.date() - claim.incident_date).days
            if days_diff < 1:
                risk_factors.append('immediate_reporting')
            elif days_diff > 30:
                risk_factors.append('delayed_reporting')
        
        # Client history risk (would need historical data)
        # This is a placeholder for future implementation
        
        # Determine overall risk level
        if len(risk_factors) >= 2:
            return 'high'
        elif len(risk_factors) == 1:
            return 'medium'
        else:
            return 'low'
    
    def _suggest_compensation(self, claim: Claim, category: str) -> Optional[float]:
        """Suggest compensation amount based on historical data and category"""
        try:
            if category not in self.categories:
                return None
            
            category_info = self.categories[category]
            min_amount, max_amount = category_info['typical_range']
            
            # Get historical data for similar claims
            similar_claims = Claim.query.filter(
                Claim.company_id == claim.company_id,
                Claim.coverage_type == claim.coverage_type,
                Claim.status.in_(['sent', 'acknowledged', 'paid'])
            ).limit(50).all()
            
            if similar_claims:
                amounts = [float(c.claim_amount) for c in similar_claims]
                avg_amount = sum(amounts) / len(amounts)
                
                # Adjust based on claim specifics
                suggested = avg_amount
                
                # Adjust for claim amount (if significantly different from average)
                claim_amount = float(claim.claim_amount)
                if claim_amount > avg_amount * 1.5:
                    suggested = min(claim_amount * 0.8, max_amount)
                elif claim_amount < avg_amount * 0.5:
                    suggested = max(claim_amount * 1.2, min_amount)
                else:
                    suggested = claim_amount
                
                return round(suggested, 2)
            else:
                # No historical data, use category average
                return round((min_amount + max_amount) / 2, 2)
                
        except Exception as e:
            logger.error(f"Error suggesting compensation: {e}")
            return None
    
    def _detect_fraud(self, claim: Claim, text_content: str) -> Tuple[float, List[FraudIndicator]]:
        """Detect potential fraud indicators"""
        fraud_indicators = []
        fraud_score = 0.0
        
        # Text pattern analysis
        for pattern_info in self.fraud_patterns:
            if re.search(pattern_info['pattern'], text_content):
                severity_weight = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
                weight = severity_weight.get(pattern_info['severity'], 0.3)
                fraud_score += weight
                
                fraud_indicators.append(FraudIndicator(
                    indicator=pattern_info['pattern'],
                    severity=pattern_info['severity'],
                    description=pattern_info['description'],
                    confidence=weight
                ))
        
        # Amount analysis
        if claim.claim_amount:
            amount = float(claim.claim_amount)
            
            # Very high amounts are suspicious
            if amount > 100000:
                fraud_score += 0.3
                fraud_indicators.append(FraudIndicator(
                    indicator='high_amount',
                    severity='medium',
                    description=f'مبلغ عالي: {amount:,.2f}',
                    confidence=0.3
                ))
            
            # Round numbers might be suspicious
            if amount % 1000 == 0 and amount > 10000:
                fraud_score += 0.1
                fraud_indicators.append(FraudIndicator(
                    indicator='round_amount',
                    severity='low',
                    description='مبلغ مدور (قد يكون مقدر)',
                    confidence=0.1
                ))
        
        # Timing analysis
        if claim.incident_date and claim.created_at:
            days_diff = (claim.created_at.date() - claim.incident_date).days
            
            # Same day reporting might be suspicious for some claim types
            if days_diff == 0:
                fraud_score += 0.2
                fraud_indicators.append(FraudIndicator(
                    indicator='immediate_reporting',
                    severity='low',
                    description='تم الإبلاغ في نفس يوم الحادث',
                    confidence=0.2
                ))
            
            # Very delayed reporting
            elif days_diff > 60:
                fraud_score += 0.4
                fraud_indicators.append(FraudIndicator(
                    indicator='delayed_reporting',
                    severity='medium',
                    description=f'تأخير في الإبلاغ: {days_diff} يوم',
                    confidence=0.4
                ))
        
        # Normalize fraud score to 0-1 range
        fraud_probability = min(fraud_score, 1.0)
        
        return fraud_probability, fraud_indicators
    
    def _generate_reasoning(self, claim: Claim, category: str, confidence: float, 
                          risk_level: str, fraud_probability: float) -> List[str]:
        """Generate human-readable reasoning for the classification"""
        reasoning = []
        
        # Category reasoning
        if category in self.categories:
            category_name = self.categories[category]['name_ar']
            reasoning.append(f'تم تصنيف المطالبة كـ "{category_name}" بثقة {confidence:.1%}')
        else:
            reasoning.append('لم يتم تحديد فئة واضحة للمطالبة')
        
        # Risk level reasoning
        risk_text = {'low': 'منخفض', 'medium': 'متوسط', 'high': 'عالي'}
        reasoning.append(f'مستوى المخاطر: {risk_text.get(risk_level, "غير محدد")}')
        
        # Amount reasoning
        if claim.claim_amount:
            amount = float(claim.claim_amount)
            if category in self.categories:
                min_amt, max_amt = self.categories[category]['typical_range']
                if amount < min_amt:
                    reasoning.append(f'المبلغ أقل من المتوسط لهذه الفئة ({min_amt:,.0f} - {max_amt:,.0f})')
                elif amount > max_amt:
                    reasoning.append(f'المبلغ أعلى من المتوسط لهذه الفئة ({min_amt:,.0f} - {max_amt:,.0f})')
                else:
                    reasoning.append('المبلغ ضمن النطاق المتوقع لهذه الفئة')
        
        # Fraud reasoning
        if fraud_probability > 0.5:
            reasoning.append(f'احتمالية الاحتيال عالية ({fraud_probability:.1%})')
        elif fraud_probability > 0.3:
            reasoning.append(f'احتمالية الاحتيال متوسطة ({fraud_probability:.1%})')
        else:
            reasoning.append('احتمالية الاحتيال منخفضة')
        
        return reasoning
    
    def get_category_statistics(self) -> Dict[str, Any]:
        """Get statistics about claim categories"""
        try:
            stats = {}
            
            for category_id, category_info in self.categories.items():
                # This would require implementing a way to track classified claims
                # For now, return basic category info
                stats[category_id] = {
                    'name_ar': category_info['name_ar'],
                    'name_en': category_info['name_en'],
                    'typical_range': category_info['typical_range'],
                    'count': 0  # Placeholder
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting category statistics: {e}")
            return {}


# Global classifier instance
ai_classifier = AIClaimsClassifier()

def classify_claim_ai(claim: Claim) -> ClassificationResult:
    """Convenient function to classify a claim"""
    return ai_classifier.classify_claim(claim)

def get_fraud_risk_assessment(claim: Claim) -> Dict[str, Any]:
    """Get detailed fraud risk assessment for a claim"""
    result = ai_classifier.classify_claim(claim)
    
    return {
        'fraud_probability': result.fraud_probability,
        'risk_level': result.risk_level,
        'category': result.category,
        'confidence': result.confidence,
        'reasoning': result.reasoning,
        'suggested_amount': result.suggested_amount
    }
