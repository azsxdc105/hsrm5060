#!/bin/bash

# Automated backup script for Claims Management System
# This script creates backups of the database and uploads directory

set -e

# Configuration
BACKUP_DIR="/backups"
DB_HOST="db"
DB_NAME="claims_db"
DB_USER="claims_user"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database backup
echo "Creating database backup..."
PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

if [ $? -eq 0 ]; then
    echo "✅ Database backup created: db_backup_$TIMESTAMP.sql"
    
    # Compress the backup
    gzip "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    echo "✅ Database backup compressed: db_backup_$TIMESTAMP.sql.gz"
else
    echo "❌ Database backup failed"
    exit 1
fi

# Create uploads backup (if directory exists and has content)
if [ -d "/app/uploads" ] && [ "$(ls -A /app/uploads)" ]; then
    echo "Creating uploads backup..."
    tar -czf "$BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz" -C /app uploads/
    
    if [ $? -eq 0 ]; then
        echo "✅ Uploads backup created: uploads_backup_$TIMESTAMP.tar.gz"
    else
        echo "❌ Uploads backup failed"
    fi
else
    echo "ℹ️  No uploads to backup"
fi

# Clean up old backups (keep only last 30 days)
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "uploads_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup process completed successfully"

# Create backup summary
cat > "$BACKUP_DIR/backup_summary_$TIMESTAMP.txt" << EOF
Backup Summary - $TIMESTAMP
============================

Database Backup: db_backup_$TIMESTAMP.sql.gz
Uploads Backup: uploads_backup_$TIMESTAMP.tar.gz
Created: $(date)
Database Size: $(du -h "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz" 2>/dev/null | cut -f1 || echo "N/A")
Uploads Size: $(du -h "$BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz" 2>/dev/null | cut -f1 || echo "N/A")

Total Backups in Directory: $(ls -1 $BACKUP_DIR/*.gz 2>/dev/null | wc -l)
EOF

echo "📋 Backup summary created: backup_summary_$TIMESTAMP.txt"
