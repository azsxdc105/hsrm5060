#!/usr/bin/env python3
"""
Enhanced File Upload Routes
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.file_manager import FileManager
from app.security_manager import SecurityManager
import os
import json
from datetime import datetime

file_upload_bp = Blueprint('file_upload', __name__)

@file_upload_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Enhanced file upload with validation and processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'لم يتم اختيار ملف'})
        
        file = request.files['file']
        claim_id = request.form.get('claim_id')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'لم يتم اختيار ملف'})
        
        # Validate file
        validation_errors = FileManager.validate_file(file)
        if validation_errors:
            return jsonify({'success': False, 'error': validation_errors[0]})
        
        # Create directory structure
        upload_dir = FileManager.create_directory_structure(
            current_app.config.get('UPLOAD_FOLDER', 'uploads'),
            claim_id
        )
        
        if not upload_dir:
            return jsonify({'success': False, 'error': 'فشل في إنشاء مجلد الرفع'})
        
        # Generate unique filename
        unique_filename = FileManager.generate_unique_filename(file.filename)
        
        # Determine file category and create appropriate subdirectory
        file_category = FileManager.get_file_category(file.filename)
        category_dir = os.path.join(upload_dir, file_category)
        os.makedirs(category_dir, exist_ok=True)
        
        file_path = os.path.join(category_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Process file based on type
        thumbnail_path = None
        if file_category == 'images':
            thumbnail_path = FileManager.process_image(file_path, create_thumbnail=True)
        
        # Get file information
        file_info = FileManager.get_file_info(file_path)
        
        # Log security event
        SecurityManager.log_security_event(
            'file_uploaded',
            f'File uploaded: {file.filename} by user {current_user.email}',
            severity='info',
            user_id=current_user.id,
            additional_data={
                'filename': file.filename,
                'size': file_info['size'] if file_info else 0,
                'category': file_category
            }
        )
        
        response_data = {
            'success': True,
            'message': 'تم رفع الملف بنجاح',
            'file_id': unique_filename,
            'filename': file.filename,
            'unique_filename': unique_filename,
            'category': file_category,
            'size': file_info['size'] if file_info else 0,
            'size_human': file_info['size_human'] if file_info else '0 B',
            'url': f'/file-upload/download/{unique_filename}',
            'thumbnail_url': f'/file-upload/thumbnail/{unique_filename}' if thumbnail_path else None
        }
        
        if file_info:
            response_data.update({
                'mime_type': file_info['mime_type'],
                'hash': file_info['hash']
            })
            
            if file_category == 'images' and 'dimensions' in file_info:
                response_data['dimensions'] = file_info['dimensions']
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"File upload error: {e}")
        return jsonify({'success': False, 'error': 'حدث خطأ في رفع الملف'})

@file_upload_bp.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download uploaded file"""
    try:
        # Find file in upload directory structure
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # Search for file in all subdirectories
        file_path = None
        for root, dirs, files in os.walk(upload_folder):
            if filename in files:
                file_path = os.path.join(root, filename)
                break
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'الملف غير موجود'}), 404
        
        # Log download
        SecurityManager.log_security_event(
            'file_downloaded',
            f'File downloaded: {filename} by user {current_user.email}',
            severity='info',
            user_id=current_user.id
        )
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        current_app.logger.error(f"File download error: {e}")
        return jsonify({'error': 'حدث خطأ في تحميل الملف'}), 500

@file_upload_bp.route('/thumbnail/<filename>')
@login_required
def get_thumbnail(filename):
    """Get file thumbnail"""
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # Look for thumbnail
        thumbnail_path = None
        for root, dirs, files in os.walk(upload_folder):
            if 'thumbnails' in root and filename in files:
                thumbnail_path = os.path.join(root, filename)
                break
            elif filename in files:
                # Check if there's a thumbnail for this file
                file_dir = os.path.dirname(os.path.join(root, filename))
                thumb_dir = os.path.join(file_dir, 'thumbnails')
                thumb_file = os.path.join(thumb_dir, filename)
                if os.path.exists(thumb_file):
                    thumbnail_path = thumb_file
                    break
        
        if thumbnail_path and os.path.exists(thumbnail_path):
            return send_file(thumbnail_path)
        else:
            # Return default thumbnail based on file type
            return jsonify({'error': 'لا توجد صورة مصغرة'}), 404
            
    except Exception as e:
        current_app.logger.error(f"Thumbnail error: {e}")
        return jsonify({'error': 'حدث خطأ في عرض الصورة المصغرة'}), 500

@file_upload_bp.route('/api/file-info/<filename>')
@login_required
def get_file_info(filename):
    """Get detailed file information"""
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # Find file
        file_path = None
        for root, dirs, files in os.walk(upload_folder):
            if filename in files:
                file_path = os.path.join(root, filename)
                break
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'الملف غير موجود'}), 404
        
        file_info = FileManager.get_file_info(file_path)
        
        if file_info:
            # Add additional metadata
            file_info['download_url'] = f'/file-upload/download/{filename}'
            if file_info['category'] == 'images':
                file_info['thumbnail_url'] = f'/file-upload/thumbnail/{filename}'
            
            return jsonify({'success': True, 'file_info': file_info})
        else:
            return jsonify({'error': 'فشل في الحصول على معلومات الملف'}), 500
            
    except Exception as e:
        current_app.logger.error(f"File info error: {e}")
        return jsonify({'error': 'حدث خطأ في الحصول على معلومات الملف'}), 500

@file_upload_bp.route('/api/delete/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    """Delete uploaded file"""
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # Find and delete file
        file_path = None
        for root, dirs, files in os.walk(upload_folder):
            if filename in files:
                file_path = os.path.join(root, filename)
                break
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'الملف غير موجود'}), 404
        
        # Delete main file
        os.remove(file_path)
        
        # Delete thumbnail if exists
        file_dir = os.path.dirname(file_path)
        thumb_dir = os.path.join(file_dir, 'thumbnails')
        thumb_file = os.path.join(thumb_dir, filename)
        if os.path.exists(thumb_file):
            os.remove(thumb_file)
        
        # Log deletion
        SecurityManager.log_security_event(
            'file_deleted',
            f'File deleted: {filename} by user {current_user.email}',
            severity='medium',
            user_id=current_user.id
        )
        
        return jsonify({'success': True, 'message': 'تم حذف الملف بنجاح'})
        
    except Exception as e:
        current_app.logger.error(f"File deletion error: {e}")
        return jsonify({'error': 'حدث خطأ في حذف الملف'}), 500

@file_upload_bp.route('/api/list')
@login_required
def list_files():
    """List uploaded files"""
    try:
        claim_id = request.args.get('claim_id')
        category = request.args.get('category')
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        files_list = []
        
        search_path = upload_folder
        if claim_id:
            search_path = os.path.join(upload_folder, f'**/claim_{claim_id}')
        
        for root, dirs, files in os.walk(upload_folder):
            # Skip thumbnail directories
            if 'thumbnails' in root:
                continue
                
            # Filter by claim if specified
            if claim_id and f'claim_{claim_id}' not in root:
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                file_info = FileManager.get_file_info(file_path)
                
                if file_info:
                    # Filter by category if specified
                    if category and file_info['category'] != category:
                        continue
                    
                    file_data = {
                        'filename': file_info['filename'],
                        'size': file_info['size'],
                        'size_human': file_info['size_human'],
                        'category': file_info['category'],
                        'created': file_info['created'].isoformat(),
                        'download_url': f'/file-upload/download/{file}',
                        'mime_type': file_info['mime_type']
                    }
                    
                    if file_info['category'] == 'images':
                        file_data['thumbnail_url'] = f'/file-upload/thumbnail/{file}'
                        if 'dimensions' in file_info:
                            file_data['dimensions'] = file_info['dimensions']
                    
                    files_list.append(file_data)
        
        return jsonify({'success': True, 'files': files_list})
        
    except Exception as e:
        current_app.logger.error(f"File listing error: {e}")
        return jsonify({'error': 'حدث خطأ في عرض الملفات'}), 500

@file_upload_bp.route('/api/cleanup', methods=['POST'])
@login_required
def cleanup_old_files():
    """Clean up old files (admin only)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'error': 'غير مصرح'}), 403
        
        days_old = request.json.get('days_old', 30)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        cleaned_count = FileManager.clean_old_files(upload_folder, days_old)
        
        SecurityManager.log_security_event(
            'files_cleanup',
            f'Cleaned {cleaned_count} old files (older than {days_old} days)',
            severity='info',
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True, 
            'message': f'تم حذف {cleaned_count} ملف قديم',
            'cleaned_count': cleaned_count
        })
        
    except Exception as e:
        current_app.logger.error(f"File cleanup error: {e}")
        return jsonify({'error': 'حدث خطأ في تنظيف الملفات'}), 500
