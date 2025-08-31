#!/usr/bin/env python3
"""
Enhanced File Management System
Handles file uploads, validation, compression, and organization
"""
import os
import uuid
import mimetypes
from datetime import datetime
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
from flask import current_app
import hashlib

class FileManager:
    """Enhanced file management with validation, compression, and organization"""
    
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'},
        'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
        'spreadsheets': {'xls', 'xlsx', 'csv'},
        'archives': {'zip', 'rar', '7z'},
        'other': {'json', 'xml'}
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE = (1920, 1080)  # Max image dimensions
    THUMBNAIL_SIZE = (300, 300)  # Thumbnail dimensions
    
    @staticmethod
    def get_file_category(filename):
        """Determine file category based on extension"""
        if not filename:
            return 'other'
        
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        for category, extensions in FileManager.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return category
        
        return 'other'
    
    @staticmethod
    def is_allowed_file(filename):
        """Check if file extension is allowed"""
        if not filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        all_extensions = set()
        
        for extensions in FileManager.ALLOWED_EXTENSIONS.values():
            all_extensions.update(extensions)
        
        return ext in all_extensions
    
    @staticmethod
    def generate_unique_filename(original_filename):
        """Generate unique filename while preserving extension"""
        if not original_filename:
            return str(uuid.uuid4()) + '.bin'
        
        name, ext = os.path.splitext(secure_filename(original_filename))
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"{name}_{timestamp}_{unique_id[:8]}{ext}"
    
    @staticmethod
    def get_file_hash(file_path):
        """Calculate MD5 hash of file for duplicate detection"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    @staticmethod
    def create_directory_structure(base_path, claim_id=None):
        """Create organized directory structure"""
        try:
            # Base uploads directory
            uploads_dir = os.path.join(base_path, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Year/Month structure
            now = datetime.now()
            year_month = now.strftime('%Y/%m')
            date_dir = os.path.join(uploads_dir, year_month)
            os.makedirs(date_dir, exist_ok=True)
            
            # Claim-specific directory if provided
            if claim_id:
                claim_dir = os.path.join(date_dir, f'claim_{claim_id}')
                os.makedirs(claim_dir, exist_ok=True)
                
                # Create subdirectories for different file types
                for category in FileManager.ALLOWED_EXTENSIONS.keys():
                    category_dir = os.path.join(claim_dir, category)
                    os.makedirs(category_dir, exist_ok=True)
                
                # Create thumbnails directory
                thumbnails_dir = os.path.join(claim_dir, 'thumbnails')
                os.makedirs(thumbnails_dir, exist_ok=True)
                
                return claim_dir
            
            return date_dir
            
        except Exception as e:
            current_app.logger.error(f"Failed to create directory structure: {e}")
            return None
    
    @staticmethod
    def process_image(file_path, max_size=None, create_thumbnail=True):
        """Process image: resize, optimize, create thumbnail"""
        try:
            if max_size is None:
                max_size = FileManager.MAX_IMAGE_SIZE
            
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Auto-rotate based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Resize if too large
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save optimized image
                img.save(file_path, 'JPEG', quality=85, optimize=True)
                
                # Create thumbnail
                if create_thumbnail:
                    thumbnail_path = FileManager.create_thumbnail(file_path, img)
                    return thumbnail_path
                
                return None
                
        except Exception as e:
            current_app.logger.error(f"Failed to process image {file_path}: {e}")
            return None
    
    @staticmethod
    def create_thumbnail(original_path, img=None):
        """Create thumbnail for image"""
        try:
            if img is None:
                img = Image.open(original_path)
            
            # Create thumbnail
            thumbnail = img.copy()
            thumbnail.thumbnail(FileManager.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            # Generate thumbnail path
            dir_path = os.path.dirname(original_path)
            filename = os.path.basename(original_path)
            name, ext = os.path.splitext(filename)
            
            thumbnail_dir = os.path.join(dir_path, 'thumbnails')
            os.makedirs(thumbnail_dir, exist_ok=True)
            
            thumbnail_path = os.path.join(thumbnail_dir, f"{name}_thumb{ext}")
            thumbnail.save(thumbnail_path, 'JPEG', quality=80)
            
            return thumbnail_path
            
        except Exception as e:
            current_app.logger.error(f"Failed to create thumbnail for {original_path}: {e}")
            return None
    
    @staticmethod
    def get_file_info(file_path):
        """Get comprehensive file information"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            filename = os.path.basename(file_path)
            
            info = {
                'filename': filename,
                'size': stat.st_size,
                'size_human': FileManager.format_file_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': os.path.splitext(filename)[1].lower(),
                'mime_type': mimetypes.guess_type(file_path)[0],
                'category': FileManager.get_file_category(filename),
                'hash': FileManager.get_file_hash(file_path)
            }
            
            # Additional info for images
            if info['category'] == 'images':
                try:
                    with Image.open(file_path) as img:
                        info['dimensions'] = img.size
                        info['format'] = img.format
                        info['mode'] = img.mode
                except Exception:
                    pass
            
            return info
            
        except Exception as e:
            current_app.logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def validate_file(file, max_size=None):
        """Comprehensive file validation"""
        if max_size is None:
            max_size = FileManager.MAX_FILE_SIZE
        
        errors = []
        
        # Check if file exists
        if not file or not file.filename:
            errors.append("لم يتم اختيار ملف")
            return errors
        
        # Check filename
        if not FileManager.is_allowed_file(file.filename):
            errors.append("نوع الملف غير مسموح")
        
        # Check file size (if we can get it)
        try:
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if size > max_size:
                errors.append(f"حجم الملف كبير جداً. الحد الأقصى {FileManager.format_file_size(max_size)}")
        except Exception:
            pass  # Can't determine size, skip this check
        
        return errors
    
    @staticmethod
    def clean_old_files(directory, days_old=30):
        """Clean up old files"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception as e:
                            current_app.logger.error(f"Failed to delete old file {file_path}: {e}")
            
            return cleaned_count
            
        except Exception as e:
            current_app.logger.error(f"Failed to clean old files: {e}")
            return 0
