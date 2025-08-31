#!/usr/bin/env python3
"""
Tesseract OCR utilities for text extraction from images
"""
import os
import re
import logging
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal
import pytesseract
from PIL import Image
import pdf2image

# Configure logging
logger = logging.getLogger(__name__)

class TesseractOCRProcessor:
    """Tesseract OCR processor for text extraction"""
    
    def __init__(self):
        self.enabled = False
        self.tesseract_path = None
        self._setup_tesseract()
    
    def _setup_tesseract(self):
        """Setup Tesseract OCR"""
        try:
            # Common Tesseract installation paths on Windows
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\USER\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
            ]
            
            # Try to find Tesseract executable
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.tesseract_path = path
                    self.enabled = True
                    logger.info(f"Tesseract found at: {path}")
                    break
            
            if not self.enabled:
                # Try to use tesseract from PATH
                try:
                    pytesseract.get_tesseract_version()
                    self.enabled = True
                    logger.info("Tesseract found in PATH")
                except:
                    logger.warning("Tesseract not found. OCR functionality will be disabled.")
                    
        except Exception as e:
            logger.error(f"Error setting up Tesseract: {e}")
            self.enabled = False
    
    def extract_text_from_image(self, image_path: str, languages: str = 'ara+eng') -> Dict:
        """Extract text from image using Tesseract OCR"""
        try:
            if not self.enabled:
                return {
                    'success': False,
                    'error': 'Tesseract OCR is not available',
                    'text': '',
                    'confidence': 0
                }
            
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': 'Image file not found',
                    'text': '',
                    'confidence': 0
                }
            
            # Open and process image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text with confidence scores
            try:
                # Get text with confidence data
                data = pytesseract.image_to_data(image, lang=languages, output_type=pytesseract.Output.DICT)
                
                # Extract text
                text = pytesseract.image_to_string(image, lang=languages)
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                return {
                    'success': True,
                    'text': text.strip(),
                    'confidence': round(avg_confidence, 2),
                    'method': 'tesseract_ocr',
                    'languages': languages
                }
                
            except Exception as e:
                logger.error(f"Tesseract OCR error: {e}")
                return {
                    'success': False,
                    'error': f'OCR processing failed: {str(e)}',
                    'text': '',
                    'confidence': 0
                }
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0
            }
    
    def extract_text_from_pdf(self, pdf_path: str, languages: str = 'ara+eng') -> Dict:
        """Extract text from PDF using OCR"""
        try:
            if not self.enabled:
                return {
                    'success': False,
                    'error': 'Tesseract OCR is not available',
                    'text': '',
                    'confidence': 0
                }
            
            # Convert PDF to images
            try:
                images = pdf2image.convert_from_path(pdf_path)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to convert PDF to images: {str(e)}',
                    'text': '',
                    'confidence': 0
                }
            
            all_text = []
            all_confidences = []
            
            # Process each page
            for i, image in enumerate(images):
                result = self.extract_text_from_image_object(image, languages)
                if result['success']:
                    all_text.append(result['text'])
                    all_confidences.append(result['confidence'])
            
            # Combine results
            combined_text = '\n\n--- Page Break ---\n\n'.join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
            
            return {
                'success': True,
                'text': combined_text,
                'confidence': round(avg_confidence, 2),
                'method': 'tesseract_ocr_pdf',
                'pages_processed': len(images)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0
            }
    
    def extract_text_from_image_object(self, image: Image.Image, languages: str = 'ara+eng') -> Dict:
        """Extract text from PIL Image object"""
        try:
            if not self.enabled:
                return {
                    'success': False,
                    'error': 'Tesseract OCR is not available',
                    'text': '',
                    'confidence': 0
                }
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text with confidence scores
            data = pytesseract.image_to_data(image, lang=languages, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(image, lang=languages)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'success': True,
                'text': text.strip(),
                'confidence': round(avg_confidence, 2),
                'method': 'tesseract_ocr'
            }
            
        except Exception as e:
            logger.error(f"Error processing image object: {e}")
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
            
            # Arabic patterns
            patterns = {
                'client_name': [
                    r'اسم المؤمن له[:\s]*([^\n]+)',
                    r'اسم العميل[:\s]*([^\n]+)',
                    r'المؤمن له[:\s]*([^\n]+)',
                    r'Name[:\s]*([^\n]+)'
                ],
                'client_national_id': [
                    r'رقم الهوية[:\s]*(\d+)',
                    r'الهوية[:\s]*(\d+)',
                    r'ID[:\s]*(\d+)',
                    r'National ID[:\s]*(\d+)'
                ],
                'policy_number': [
                    r'رقم الوثيقة[:\s]*([^\n]+)',
                    r'رقم البوليصة[:\s]*([^\n]+)',
                    r'Policy[:\s]*([^\n]+)',
                    r'POL[-\s]*(\w+)'
                ],
                'incident_number': [
                    r'رقم الحادث[:\s]*([^\n]+)',
                    r'رقم البلاغ[:\s]*([^\n]+)',
                    r'Incident[:\s]*([^\n]+)',
                    r'Report[:\s]*([^\n]+)'
                ],
                'incident_date': [
                    r'التاريخ[:\s]*(\d{4}[-/]\d{2}[-/]\d{2})',
                    r'تاريخ الحادث[:\s]*(\d{4}[-/]\d{2}[-/]\d{2})',
                    r'Date[:\s]*(\d{4}[-/]\d{2}[-/]\d{2})',
                    r'(\d{2}[-/]\d{2}[-/]\d{4})'
                ],
                'claim_amount': [
                    r'مبلغ الضرر[:\s]*(\d+(?:[.,]\d+)?)',
                    r'قيمة الضرر[:\s]*(\d+(?:[.,]\d+)?)',
                    r'Amount[:\s]*(\d+(?:[.,]\d+)?)',
                    r'(\d+(?:[.,]\d+)?)\s*ريال'
                ],
                'city': [
                    r'المدينة[:\s]*([^\n]+)',
                    r'City[:\s]*([^\n]+)',
                    r'الرياض|جدة|الدمام|مكة|المدينة'
                ]
            }
            
            # Extract data using patterns
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        if field == 'incident_date':
                            try:
                                date_str = match.group(1).replace('/', '-')
                                if len(date_str.split('-')[0]) == 2:  # DD-MM-YYYY format
                                    parts = date_str.split('-')
                                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
                                data[field] = datetime.strptime(date_str, '%Y-%m-%d').date()
                            except:
                                continue
                        elif field == 'claim_amount':
                            try:
                                amount_str = match.group(1).replace(',', '.')
                                data[field] = Decimal(amount_str)
                            except:
                                continue
                        else:
                            data[field] = match.group(1).strip()
                        break
            
            # Extract coverage type from keywords
            if any(word in text.lower() for word in ['شامل', 'comprehensive', 'full']):
                data['coverage_type'] = 'comprehensive'
            elif any(word in text.lower() for word in ['ضد الغير', 'third party', 'liability']):
                data['coverage_type'] = 'third_party'
            
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
            # Determine file type and extract text
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                ocr_result = self.extract_text_from_pdf(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                ocr_result = self.extract_text_from_image(file_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_ext}'
                }
            
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
                'method': ocr_result.get('method', 'tesseract_ocr'),
                'file_type': file_ext
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def is_available(self) -> bool:
        """Check if Tesseract OCR is available"""
        return self.enabled
    
    def get_available_languages(self) -> list:
        """Get list of available OCR languages"""
        try:
            if not self.enabled:
                return []
            return pytesseract.get_languages()
        except:
            return ['eng', 'ara']  # Default fallback

# Global instance
tesseract_ocr = TesseractOCRProcessor()

# Convenience functions
def extract_text_from_image(image_path: str, languages: str = 'ara+eng') -> Dict:
    """Extract text from image using Tesseract"""
    return tesseract_ocr.extract_text_from_image(image_path, languages)

def extract_text_from_pdf(pdf_path: str, languages: str = 'ara+eng') -> Dict:
    """Extract text from PDF using Tesseract"""
    return tesseract_ocr.extract_text_from_pdf(pdf_path, languages)

def extract_claim_data_from_text(text: str) -> Dict:
    """Extract structured claim data from text"""
    return tesseract_ocr.extract_claim_data_from_text(text)

def process_document(file_path: str) -> Dict:
    """Process document and extract claim data"""
    return tesseract_ocr.process_document(file_path)

def is_ocr_available() -> bool:
    """Check if OCR is available"""
    return tesseract_ocr.is_available()

def get_available_languages() -> list:
    """Get available OCR languages"""
    return tesseract_ocr.get_available_languages()