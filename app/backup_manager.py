#!/usr/bin/env python3
"""
Comprehensive Backup Manager
Handles database backups, file backups, and system restoration
"""
import os
import shutil
import sqlite3
import zipfile
import json
import hashlib
from datetime import datetime, timedelta
from flask import current_app
from app import db
import tempfile
import subprocess

class BackupManager:
    """Comprehensive backup and restoration system"""
    
    BACKUP_TYPES = {
        'database': 'قاعدة البيانات',
        'files': 'الملفات',
        'full': 'نسخة كاملة',
        'config': 'الإعدادات'
    }
    
    @staticmethod
    def create_backup(backup_type='full', description=None):
        """Create a comprehensive backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{backup_type}_{timestamp}"
            
            # Create backup directory
            backup_dir = os.path.join(current_app.config.get('BACKUP_FOLDER', 'backups'), backup_name)
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_info = {
                'name': backup_name,
                'type': backup_type,
                'description': description or f"Automated {backup_type} backup",
                'created_at': datetime.now().isoformat(),
                'size': 0,
                'files_count': 0,
                'status': 'in_progress',
                'components': []
            }
            
            total_size = 0
            files_count = 0
            
            # Database backup
            if backup_type in ['database', 'full']:
                db_backup_path = BackupManager._backup_database(backup_dir)
                if db_backup_path:
                    db_size = os.path.getsize(db_backup_path)
                    total_size += db_size
                    files_count += 1
                    backup_info['components'].append({
                        'type': 'database',
                        'path': os.path.basename(db_backup_path),
                        'size': db_size,
                        'status': 'completed'
                    })
            
            # Files backup
            if backup_type in ['files', 'full']:
                files_backup_path = BackupManager._backup_files(backup_dir)
                if files_backup_path:
                    files_size = os.path.getsize(files_backup_path)
                    total_size += files_size
                    files_count += 1
                    backup_info['components'].append({
                        'type': 'files',
                        'path': os.path.basename(files_backup_path),
                        'size': files_size,
                        'status': 'completed'
                    })
            
            # Configuration backup
            if backup_type in ['config', 'full']:
                config_backup_path = BackupManager._backup_config(backup_dir)
                if config_backup_path:
                    config_size = os.path.getsize(config_backup_path)
                    total_size += config_size
                    files_count += 1
                    backup_info['components'].append({
                        'type': 'config',
                        'path': os.path.basename(config_backup_path),
                        'size': config_size,
                        'status': 'completed'
                    })
            
            # Update backup info
            backup_info['size'] = total_size
            backup_info['files_count'] = files_count
            backup_info['status'] = 'completed'
            
            # Save backup metadata
            metadata_path = os.path.join(backup_dir, 'backup_info.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            # Create compressed archive
            archive_path = f"{backup_dir}.zip"
            BackupManager._create_archive(backup_dir, archive_path)
            
            # Remove uncompressed directory
            shutil.rmtree(backup_dir)
            
            # Update backup info with final archive size
            backup_info['archive_path'] = archive_path
            backup_info['archive_size'] = os.path.getsize(archive_path)
            backup_info['checksum'] = BackupManager._calculate_checksum(archive_path)
            
            current_app.logger.info(f"Backup created successfully: {backup_name}")
            return backup_info
            
        except Exception as e:
            current_app.logger.error(f"Failed to create backup: {e}")
            return None
    
    @staticmethod
    def _backup_database(backup_dir):
        """Backup database"""
        try:
            db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
            if not db_path or not os.path.exists(db_path):
                return None
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'database_{timestamp}.db')
            
            # Create database backup using SQLite backup API
            source_conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(backup_path)
            
            source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # Also create SQL dump
            sql_dump_path = os.path.join(backup_dir, f'database_{timestamp}.sql')
            with open(sql_dump_path, 'w', encoding='utf-8') as f:
                conn = sqlite3.connect(db_path)
                for line in conn.iterdump():
                    f.write(f'{line}\n')
                conn.close()
            
            return backup_path
            
        except Exception as e:
            current_app.logger.error(f"Failed to backup database: {e}")
            return None
    
    @staticmethod
    def _backup_files(backup_dir):
        """Backup uploaded files and attachments"""
        try:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_folder):
                return None
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            files_backup_path = os.path.join(backup_dir, f'files_{timestamp}.zip')
            
            with zipfile.ZipFile(files_backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(upload_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, upload_folder)
                        zipf.write(file_path, arcname)
            
            return files_backup_path
            
        except Exception as e:
            current_app.logger.error(f"Failed to backup files: {e}")
            return None
    
    @staticmethod
    def _backup_config(backup_dir):
        """Backup configuration files"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            config_backup_path = os.path.join(backup_dir, f'config_{timestamp}.zip')
            
            config_files = [
                'config.py',
                '.env',
                'requirements.txt',
                'app/models.py'
            ]
            
            with zipfile.ZipFile(config_backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for config_file in config_files:
                    if os.path.exists(config_file):
                        zipf.write(config_file, os.path.basename(config_file))
            
            return config_backup_path
            
        except Exception as e:
            current_app.logger.error(f"Failed to backup config: {e}")
            return None
    
    @staticmethod
    def _create_archive(source_dir, archive_path):
        """Create compressed archive of backup directory"""
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to create archive: {e}")
            return False
    
    @staticmethod
    def _calculate_checksum(file_path):
        """Calculate MD5 checksum of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    @staticmethod
    def list_backups():
        """List all available backups"""
        try:
            backup_folder = current_app.config.get('BACKUP_FOLDER', 'backups')
            if not os.path.exists(backup_folder):
                return []
            
            backups = []
            for item in os.listdir(backup_folder):
                if item.endswith('.zip'):
                    backup_path = os.path.join(backup_folder, item)
                    backup_info = BackupManager._get_backup_info(backup_path)
                    if backup_info:
                        backups.append(backup_info)
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return backups
            
        except Exception as e:
            current_app.logger.error(f"Failed to list backups: {e}")
            return []
    
    @staticmethod
    def _get_backup_info(backup_path):
        """Extract backup information from archive"""
        try:
            backup_info = {
                'name': os.path.basename(backup_path).replace('.zip', ''),
                'path': backup_path,
                'size': os.path.getsize(backup_path),
                'created_at': datetime.fromtimestamp(os.path.getctime(backup_path)).isoformat(),
                'checksum': BackupManager._calculate_checksum(backup_path)
            }
            
            # Try to extract metadata from archive
            try:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    if 'backup_info.json' in zipf.namelist():
                        with zipf.open('backup_info.json') as f:
                            metadata = json.loads(f.read().decode('utf-8'))
                            backup_info.update(metadata)
            except Exception:
                pass  # Use basic info if metadata extraction fails
            
            return backup_info
            
        except Exception as e:
            current_app.logger.error(f"Failed to get backup info: {e}")
            return None
    
    @staticmethod
    def restore_backup(backup_path, components=None):
        """Restore from backup"""
        try:
            if not os.path.exists(backup_path):
                return {'success': False, 'error': 'Backup file not found'}
            
            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract backup archive
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Load backup metadata
                metadata_path = os.path.join(temp_dir, 'backup_info.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        backup_info = json.load(f)
                else:
                    backup_info = {'components': []}
                
                restored_components = []
                
                # Restore database if requested
                if not components or 'database' in components:
                    db_restored = BackupManager._restore_database(temp_dir)
                    if db_restored:
                        restored_components.append('database')
                
                # Restore files if requested
                if not components or 'files' in components:
                    files_restored = BackupManager._restore_files(temp_dir)
                    if files_restored:
                        restored_components.append('files')
                
                # Restore config if requested
                if not components or 'config' in components:
                    config_restored = BackupManager._restore_config(temp_dir)
                    if config_restored:
                        restored_components.append('config')
                
                return {
                    'success': True,
                    'restored_components': restored_components,
                    'backup_info': backup_info
                }
            
        except Exception as e:
            current_app.logger.error(f"Failed to restore backup: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _restore_database(temp_dir):
        """Restore database from backup"""
        try:
            # Find database backup file
            db_files = [f for f in os.listdir(temp_dir) if f.startswith('database_') and f.endswith('.db')]
            if not db_files:
                return False
            
            db_backup_path = os.path.join(temp_dir, db_files[0])
            db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
            
            if not db_path:
                return False
            
            # Create backup of current database
            current_backup = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, current_backup)
            
            # Restore database
            shutil.copy2(db_backup_path, db_path)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to restore database: {e}")
            return False
    
    @staticmethod
    def _restore_files(temp_dir):
        """Restore files from backup"""
        try:
            # Find files backup
            files_backups = [f for f in os.listdir(temp_dir) if f.startswith('files_') and f.endswith('.zip')]
            if not files_backups:
                return False
            
            files_backup_path = os.path.join(temp_dir, files_backups[0])
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            
            # Create backup of current files
            if os.path.exists(upload_folder):
                backup_folder = f"{upload_folder}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copytree(upload_folder, backup_folder)
                shutil.rmtree(upload_folder)
            
            # Extract files
            os.makedirs(upload_folder, exist_ok=True)
            with zipfile.ZipFile(files_backup_path, 'r') as zipf:
                zipf.extractall(upload_folder)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to restore files: {e}")
            return False
    
    @staticmethod
    def _restore_config(temp_dir):
        """Restore configuration from backup"""
        try:
            # Find config backup
            config_backups = [f for f in os.listdir(temp_dir) if f.startswith('config_') and f.endswith('.zip')]
            if not config_backups:
                return False
            
            config_backup_path = os.path.join(temp_dir, config_backups[0])
            
            # Extract config files to temporary location
            config_temp_dir = os.path.join(temp_dir, 'config_restore')
            os.makedirs(config_temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(config_backup_path, 'r') as zipf:
                zipf.extractall(config_temp_dir)
            
            # Note: In production, you might want to be more careful about restoring config files
            # For now, we'll just log what would be restored
            current_app.logger.info("Config files available for restoration in: " + config_temp_dir)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to restore config: {e}")
            return False
    
    @staticmethod
    def delete_backup(backup_path):
        """Delete a backup file"""
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                current_app.logger.info(f"Backup deleted: {backup_path}")
                return True
            return False
            
        except Exception as e:
            current_app.logger.error(f"Failed to delete backup: {e}")
            return False
    
    @staticmethod
    def cleanup_old_backups(days_to_keep=30):
        """Clean up old backup files"""
        try:
            backup_folder = current_app.config.get('BACKUP_FOLDER', 'backups')
            if not os.path.exists(backup_folder):
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for item in os.listdir(backup_folder):
                if item.endswith('.zip'):
                    backup_path = os.path.join(backup_folder, item)
                    creation_time = datetime.fromtimestamp(os.path.getctime(backup_path))
                    
                    if creation_time < cutoff_date:
                        if BackupManager.delete_backup(backup_path):
                            deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            current_app.logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    @staticmethod
    def get_backup_statistics():
        """Get backup system statistics"""
        try:
            backup_folder = current_app.config.get('BACKUP_FOLDER', 'backups')
            
            stats = {
                'total_backups': 0,
                'total_size': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'backup_types': {}
            }
            
            if not os.path.exists(backup_folder):
                return stats
            
            backups = BackupManager.list_backups()
            
            stats['total_backups'] = len(backups)
            
            if backups:
                stats['total_size'] = sum(backup.get('size', 0) for backup in backups)
                stats['oldest_backup'] = min(backups, key=lambda x: x['created_at'])
                stats['newest_backup'] = max(backups, key=lambda x: x['created_at'])
                
                # Count by type
                for backup in backups:
                    backup_type = backup.get('type', 'unknown')
                    stats['backup_types'][backup_type] = stats['backup_types'].get(backup_type, 0) + 1
            
            return stats
            
        except Exception as e:
            current_app.logger.error(f"Failed to get backup statistics: {e}")
            return {
                'total_backups': 0,
                'total_size': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'backup_types': {}
            }
