#!/usr/bin/env python3
"""
Quick database optimization script
"""
from app import create_app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_optimize():
    """Quick database optimization"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🚀 Starting quick database optimization...")
            
            # Add essential indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status)",
                "CREATE INDEX IF NOT EXISTS idx_claims_company_id ON claims(company_id)",
                "CREATE INDEX IF NOT EXISTS idx_claims_created_at ON claims(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_payments_claim_id ON payments(claim_id)",
                "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)"
            ]
            
            for index_sql in indexes:
                try:
                    db.session.execute(text(index_sql))
                    logger.info(f"✅ Added index: {index_sql.split()[-1]}")
                except Exception as e:
                    logger.warning(f"⚠️ Index might already exist: {e}")
            
            # Optimize SQLite settings
            optimizations = [
                "PRAGMA journal_mode = WAL",
                "PRAGMA synchronous = NORMAL", 
                "PRAGMA cache_size = 10000",
                "PRAGMA temp_store = MEMORY"
            ]
            
            for opt_sql in optimizations:
                try:
                    db.session.execute(text(opt_sql))
                    logger.info(f"✅ Applied: {opt_sql}")
                except Exception as e:
                    logger.warning(f"⚠️ Optimization failed: {e}")
            
            # Analyze tables
            db.session.execute(text("ANALYZE"))
            
            # Commit changes
            db.session.commit()
            
            logger.info("🎯 Quick optimization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Optimization failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    quick_optimize()
