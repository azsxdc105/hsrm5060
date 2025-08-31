#!/usr/bin/env python3
"""
Simplified OCR utilities without Google Vision API dependency
"""
import os
import re
import logging
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal

# Configure logging
logger = logging.getLogger(__name__)

class SimpleOCRProcessor:
    """Simple OCR processor for basic text extraction"""
    
    def __init__(self):
        self.enabled = True
        logger.info("Simple OCR processor initialized")
    
    def extract_text_from_image(self, image_path: str) -> Dict:
        """Extract text from image (mock implementation)"""
        try:
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': 'Image file not found',
                    'text': '',
                    'confidence': 0
                }
            
            # Mock OCR result - in real implementation you would use pytesseract or similar
            mock_text = """
            تقرير حادث مروري
            رقم الحادث: 12345
            التاريخ: 2025-01-15
            اسم المؤمن له: أحمد محمد علي
            رقم الهوية: 1234567890
            رقم الوثيقة: POL-2025-001
            مبلغ الضرر: 15000 ريال
            نوع التغطية: شامل
            المدينة: الرياض
            """
            
            return {
                'success': True,
                'text': mock_text.strip(),
                'confidence': 85,
                'method': 'mock_ocr'
            }
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0
            }
    
    def extract_claim_data_from_text(self, text: str) -> Dict:
        """Extract structured claim data from OCR text"""
        try:
            data = {
                'client_name': '',
                'client_national_id': '',
                'policy_number': '',
                'incident_number': '',
                'incident_date': None,
                'claim_amount': None,
                'coverage_type': '',
                'city': '',
                'confidence': 0
            }
            
            # Extract client name
            name_match = re.search(r'اسم المؤمن له[:\s]*([^\n]+)', text)
            if name_match:
                data['client_name'] = name_match.group(1).strip()
            
            # Extract national ID
            id_match = re.search(r'رقم الهوية[:\s]*(\d+)', text)
            if id_match:
                data['client_national_id'] = id_match.group(1).strip()
            
            # Extract policy number
            policy_match = re.search(r'رقم الوثيقة[:\s]*([^\n]+)', text)
            if policy_match:
                data['policy_number'] = policy_match.group(1).strip()
            
            # Extract incident number
            incident_match = re.search(r'رقم الحادث[:\s]*([^\n]+)', text)
            if incident_match:
                data['incident_number'] = incident_match.group(1).strip()
            
            # Extract incident date
            date_match = re.search(r'التاريخ[:\s]*(\d{4}-\d{2}-\d{2})', text)
            if date_match:
                try:
                    data['incident_date'] = datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
                except:
                    pass
            
            # Extract claim amount
            amount_match = re.search(r'مبلغ الضرر[:\s]*(\d+(?:\.\d+)?)', text)
            if amount_match:
                try:
                    data['claim_amount'] = Decimal(amount_match.group(1))
                except:
                    pass
            
            # Extract coverage type
            if 'شامل' in text:
                data['coverage_type'] = 'comprehensive'
            elif 'ضد الغير' in text:
                data['coverage_type'] = 'third_party'
            
            # Extract city
            city_match = re.search(r'المدينة[:\s]*([^\n]+)', text)
            if city_match:
                data['city'] = city_match.group(1).strip()
            
            # Calculate confidence based on extracted fields
            filled_fields = sum(1 for v in data.values() if v and v != '')
            data['confidence'] = min(95, (filled_fields / 8) * 100)
            
            return {
                'success': True,
                'data': data,
                'extracted_fields': filled_fields
            }
            
        except Exception as e:
            logger.error(f"Error extracting claim data: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }
    
    def process_document(self, file_path: str) -> Dict:
        """Process document and extract claim data"""
        try:
            # Extract text from image
            ocr_result = self.extract_text_from_image(file_path)
            
            if not ocr_result['success']:
                return ocr_result
            
            # Extract structured data
            data_result = self.extract_claim_data_from_text(ocr_result['text'])
            
            return {
                'success': True,
                'ocr_text': ocr_result['text'],
                'ocr_confidence': ocr_result['confidence'],
                'extracted_data': data_result['data'] if data_result['success'] else {},
                'extraction_success': data_result['success'],
                'method': 'simple_ocr'
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def is_available(self) -> bool:
        """Check if OCR is available"""
        return self.enabled

# Global instance
simple_ocr = SimpleOCRProcessor()

def extract_text_from_image(image_path: str) -> Dict:
    """Convenience function for text extraction"""
    return simple_ocr.extract_text_from_image(image_path)

def extract_claim_data_from_text(text: str) -> Dict:
    """Convenience function for data extraction"""
    return simple_ocr.extract_claim_data_from_text(text)

def process_document(file_path: str) -> Dict:
    """Convenience function for document processing"""
    return simple_ocr.process_document(file_path)

def is_ocr_available() -> bool:
    """Check if OCR is available"""
    return simple_ocr.is_available()
