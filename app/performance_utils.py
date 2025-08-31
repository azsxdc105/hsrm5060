"""
Performance optimization utilities
"""
import time
import psutil
import sqlite3
from datetime import datetime, timedelta
from flask import current_app, g
from functools import wraps
import logging
from app import db, cache

# Configure performance logger
perf_logger = logging.getLogger('performance')
perf_logger.setLevel(logging.INFO)

class PerformanceMonitor:
    """Monitor application performance"""
    
    @staticmethod
    def get_system_stats():
        """Get system performance statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
    
    @staticmethod
    def get_database_stats():
        """Get database performance statistics"""
        try:
            # For SQLite
            db_path = current_app.config.get('DATABASE_URL', '').replace('sqlite:///', '')
            if not db_path:
                return {'error': 'Database path not found'}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            
            # Get table sizes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            table_stats = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                table_stats[table_name] = row_count
            
            conn.close()
            
            return {
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'table_counts': table_stats,
                'total_records': sum(table_stats.values())
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_cache_stats():
        """Get cache performance statistics"""
        try:
            # This depends on your cache implementation
            # For simple cache, we'll return basic info
            return {
                'cache_type': 'SimpleCache',
                'status': 'active'
            }
        except Exception as e:
            return {'error': str(e)}

class DatabaseOptimizer:
    """Database optimization utilities"""
    
    @staticmethod
    def analyze_slow_queries():
        """Analyze slow queries (SQLite specific)"""
        try:
            # Enable query logging for SQLite
            slow_queries = []
            
            # This is a placeholder - in production you'd use proper query logging
            return {
                'slow_queries': slow_queries,
                'total_queries': 0,
                'avg_query_time': 0
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def optimize_database():
        """Optimize database performance"""
        try:
            # Run VACUUM on SQLite to reclaim space
            db.engine.execute('VACUUM')
            
            # Analyze tables for better query planning
            db.engine.execute('ANALYZE')
            
            perf_logger.info('Database optimization completed')
            return True
            
        except Exception as e:
            perf_logger.error(f'Database optimization failed: {e}')
            return False
    
    @staticmethod
    def get_table_sizes():
        """Get table sizes and statistics"""
        try:
            tables_info = []
            
            # Get all table names
            result = db.engine.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            
            for row in result:
                table_name = row[0]
                
                # Get row count
                count_result = db.engine.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = count_result.fetchone()[0]
                
                tables_info.append({
                    'table_name': table_name,
                    'row_count': row_count
                })
            
            return tables_info
            
        except Exception as e:
            return {'error': str(e)}

def performance_monitor(threshold_seconds=1.0):
    """Decorator to monitor function performance"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if execution_time > threshold_seconds:
                    perf_logger.warning(
                        f'Slow function: {f.__name__} took {execution_time:.2f}s'
                    )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                perf_logger.error(
                    f'Function {f.__name__} failed after {execution_time:.2f}s: {e}'
                )
                raise
                
        return decorated_function
    return decorator

def cache_result(timeout=300, key_prefix=''):
    """Decorator to cache function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}{f.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            
            return result
            
        return decorated_function
    return decorator

class HealthChecker:
    """System health monitoring"""
    
    @staticmethod
    def check_database_health():
        """Check database connectivity and health"""
        try:
            # Simple query to test database
            db.engine.execute('SELECT 1')
            return {'status': 'healthy', 'message': 'Database connection OK'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Database error: {e}'}
    
    @staticmethod
    def check_disk_space():
        """Check available disk space"""
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            if free_percent < 10:
                return {'status': 'critical', 'message': f'Low disk space: {free_percent:.1f}% free'}
            elif free_percent < 20:
                return {'status': 'warning', 'message': f'Disk space getting low: {free_percent:.1f}% free'}
            else:
                return {'status': 'healthy', 'message': f'Disk space OK: {free_percent:.1f}% free'}
                
        except Exception as e:
            return {'status': 'unknown', 'message': f'Cannot check disk space: {e}'}
    
    @staticmethod
    def check_memory_usage():
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                return {'status': 'critical', 'message': f'High memory usage: {memory.percent}%'}
            elif memory.percent > 80:
                return {'status': 'warning', 'message': f'Memory usage high: {memory.percent}%'}
            else:
                return {'status': 'healthy', 'message': f'Memory usage OK: {memory.percent}%'}
                
        except Exception as e:
            return {'status': 'unknown', 'message': f'Cannot check memory: {e}'}
    
    @staticmethod
    def get_health_status():
        """Get overall system health status"""
        checks = {
            'database': HealthChecker.check_database_health(),
            'disk_space': HealthChecker.check_disk_space(),
            'memory': HealthChecker.check_memory_usage()
        }
        
        return checks

class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def get_query_plan(query):
        """Get query execution plan (SQLite)"""
        try:
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            result = db.engine.execute(explain_query)
            return [dict(row) for row in result]
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def suggest_indexes():
        """Suggest database indexes for better performance"""
        suggestions = []
        
        # Common index suggestions based on typical queries
        common_indexes = [
            {
                'table': 'claims',
                'columns': ['status', 'created_at'],
                'reason': 'Filtering by status and sorting by date'
            },
            {
                'table': 'claims',
                'columns': ['company_id'],
                'reason': 'Foreign key lookups'
            },
            {
                'table': 'claims',
                'columns': ['client_national_id'],
                'reason': 'Client lookups'
            },
            {
                'table': 'email_logs',
                'columns': ['created_at', 'status'],
                'reason': 'Email log queries'
            }
        ]
        
        return common_indexes

# Global instances
performance_monitor_instance = PerformanceMonitor()
db_optimizer = DatabaseOptimizer()
health_checker = HealthChecker()
query_optimizer = QueryOptimizer()

def init_performance_monitoring(app):
    """Initialize performance monitoring for the app"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Log slow requests
            if duration > 2.0:  # 2 seconds threshold
                perf_logger.warning(
                    f'Slow request: {request.method} {request.path} took {duration:.2f}s'
                )
        
        return response
    
    # Schedule periodic health checks
    @app.cli.command()
    def health_check():
        """Run health check"""
        status = health_checker.get_health_status()
        print("System Health Status:")
        for component, health in status.items():
            print(f"  {component}: {health['status']} - {health['message']}")
    
    return app
