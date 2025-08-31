#!/usr/bin/env python3
"""
Database optimization script - Add indexes and optimize performance
"""
from app import create_app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_database_indexes():
    """Add database indexes for better performance"""
    app = create_app()
    
    with app.app_context():
        try:
            # Claims table indexes
            logger.info("Adding indexes to claims table...")
            
            # Index on status for filtering
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status)"))

            # Index on company_id for filtering by company
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_claims_company_id ON claims(company_id)"))

            # Index on created_at for date filtering and sorting
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_claims_created_at ON claims(created_at)"))

            # Index on client_national_id for searching
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_claims_client_national_id ON claims(client_national_id)"))

            # Index on incident_date for date filtering
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_claims_incident_date ON claims(incident_date)"))

            # Index on email_sent_at for filtering sent claims
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_claims_email_sent_at ON claims(email_sent_at)"))

            # Composite index for common queries
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_claims_status_company ON claims(status, company_id)"))
            
            # Users table indexes
            logger.info("Adding indexes to users table...")
            
            # Index on email for login
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))

            # Index on active status
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)"))

            # Index on role for authorization
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"))
            
            # Audit logs table indexes
            logger.info("Adding indexes to audit_logs table...")
            
            # Index on timestamp for date filtering
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)")
            
            # Index on user_id for filtering by user
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)")
            
            # Index on action for filtering by action type
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)")
            
            # Index on resource_type for filtering by resource
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type)")
            
            # Composite index for common audit queries
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp)")
            
            # Payments table indexes
            logger.info("Adding indexes to payments table...")
            
            # Index on claim_id for finding payments by claim
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_payments_claim_id ON payments(claim_id)")
            
            # Index on status for filtering by payment status
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)")
            
            # Index on payment_date for date filtering
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_payments_payment_date ON payments(payment_date)")
            
            # Index on created_at for sorting
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at)")
            
            # Index on payment_method for filtering
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_payments_payment_method ON payments(payment_method)")
            
            # Notifications table indexes
            logger.info("Adding indexes to notifications table...")
            
            # Index on user_id for user notifications
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)")
            
            # Index on is_read for filtering read/unread
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)")
            
            # Index on created_at for sorting
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)")
            
            # Index on related_claim_id for claim notifications
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_notifications_claim_id ON notifications(related_claim_id)")
            
            # Email logs table indexes
            logger.info("Adding indexes to email_logs table...")
            
            # Index on claim_id for finding emails by claim
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_claim_id ON email_logs(claim_id)")
            
            # Index on sent_at for date filtering
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at)")
            
            # Index on status for filtering by email status
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status)")
            
            # Insurance companies table indexes
            logger.info("Adding indexes to insurance_companies table...")
            
            # Index on active status
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_insurance_companies_active ON insurance_companies(active)")
            
            # Index on name_ar for searching
            db.session.execute("CREATE INDEX IF NOT EXISTS idx_insurance_companies_name_ar ON insurance_companies(name_ar)")
            
            # Commit all changes
            db.session.commit()
            logger.info("✅ All database indexes added successfully!")
            
            # Analyze tables for better query planning
            logger.info("Analyzing tables for query optimization...")
            db.session.execute("ANALYZE")
            db.session.commit()
            
            logger.info("✅ Database optimization completed!")
            
        except Exception as e:
            logger.error(f"❌ Error adding database indexes: {e}")
            db.session.rollback()
            raise

def optimize_database_settings():
    """Optimize database settings for better performance"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Optimizing database settings...")
            
            # SQLite specific optimizations
            db.session.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            db.session.execute("PRAGMA synchronous = NORMAL")  # Balance between safety and speed
            db.session.execute("PRAGMA cache_size = 10000")  # Increase cache size
            db.session.execute("PRAGMA temp_store = MEMORY")  # Store temp tables in memory
            db.session.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O
            
            logger.info("✅ Database settings optimized!")
            
        except Exception as e:
            logger.error(f"❌ Error optimizing database settings: {e}")
            raise

def vacuum_database():
    """Vacuum database to reclaim space and optimize"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Vacuuming database...")
            db.session.execute("VACUUM")
            logger.info("✅ Database vacuumed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error vacuuming database: {e}")
            raise

def get_database_stats():
    """Get database statistics"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Getting database statistics...")
            
            # Get table sizes
            tables = ['users', 'claims', 'insurance_companies', 'payments', 'audit_logs', 'notifications', 'email_logs']
            
            for table in tables:
                try:
                    result = db.session.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    logger.info(f"📊 {table}: {count:,} rows")
                except Exception as e:
                    logger.error(f"❌ Error getting stats for {table}: {e}")
            
            # Get database size (SQLite specific)
            try:
                result = db.session.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                size = result.scalar()
                size_mb = size / (1024 * 1024)
                logger.info(f"💾 Database size: {size_mb:.2f} MB")
            except Exception as e:
                logger.error(f"❌ Error getting database size: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error getting database statistics: {e}")
            raise

if __name__ == '__main__':
    print("🚀 Starting database optimization...")
    
    try:
        # Get initial stats
        print("\n📊 Initial database statistics:")
        get_database_stats()
        
        # Add indexes
        print("\n🔧 Adding database indexes...")
        add_database_indexes()
        
        # Optimize settings
        print("\n⚙️ Optimizing database settings...")
        optimize_database_settings()
        
        # Vacuum database
        print("\n🧹 Vacuuming database...")
        vacuum_database()
        
        # Get final stats
        print("\n📊 Final database statistics:")
        get_database_stats()
        
        print("\n✅ Database optimization completed successfully!")
        print("🎯 Your application should now perform better!")
        
    except Exception as e:
        print(f"\n❌ Database optimization failed: {e}")
        exit(1)
