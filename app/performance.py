#!/usr/bin/env python3
"""
Performance monitoring and optimization utilities
"""
import time
import functools
import psutil
import logging
from datetime import datetime, timedelta
from flask import request, g, current_app
from app import db, cache
from app.models import AuditLog
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = {}
        self.slow_queries = []
        self.error_count = 0
        self.request_count = 0
    
    def record_request_time(self, endpoint, duration):
        """Record request processing time"""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = {
                'total_time': 0,
                'request_count': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': float('inf')
            }
        
        metric = self.metrics[endpoint]
        metric['total_time'] += duration
        metric['request_count'] += 1
        metric['avg_time'] = metric['total_time'] / metric['request_count']
        metric['max_time'] = max(metric['max_time'], duration)
        metric['min_time'] = min(metric['min_time'], duration)
        
        # Log slow requests
        if duration > 2.0:  # Requests taking more than 2 seconds
            self.slow_queries.append({
                'endpoint': endpoint,
                'duration': duration,
                'timestamp': datetime.utcnow(),
                'method': request.method if request else 'Unknown',
                'ip': request.remote_addr if request else 'Unknown'
            })
    
    def get_system_metrics(self):
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_total': memory.total,
                'disk_percent': disk.percent,
                'disk_free': disk.free,
                'disk_total': disk.total,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_database_metrics(self):
        """Get database performance metrics"""
        try:
            # Get database connection info
            engine = db.engine
            pool = engine.pool
            
            return {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {}
    
    def get_performance_report(self):
        """Generate comprehensive performance report"""
        return {
            'request_metrics': self.metrics,
            'slow_queries': self.slow_queries[-50:],  # Last 50 slow queries
            'system_metrics': self.get_system_metrics(),
            'database_metrics': self.get_database_metrics(),
            'error_count': self.error_count,
            'total_requests': self.request_count,
            'generated_at': datetime.utcnow().isoformat()
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_performance(f):
    """Decorator to monitor function performance"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            performance_monitor.error_count += 1
            logger.error(f"Error in {f.__name__}: {e}")
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Record performance metrics
            endpoint = f.__name__
            if hasattr(request, 'endpoint'):
                endpoint = request.endpoint
            
            performance_monitor.record_request_time(endpoint, duration)
            performance_monitor.request_count += 1
            
            # Log slow operations
            if duration > 1.0:
                logger.warning(f"Slow operation: {endpoint} took {duration:.2f}s")
    
    return decorated_function

def cache_key_generator(*args, **kwargs):
    """Generate cache key from function arguments"""
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(f"{type(arg).__name__}_{arg.id}")
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'id'):
            key_parts.append(f"{k}_{type(v).__name__}_{v.id}")
        else:
            key_parts.append(f"{k}_{v}")
    
    return "_".join(key_parts)

def cached_query(timeout=300):
    """Decorator for caching database queries"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = f"{f.__name__}_{cache_key_generator(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {cache_key}")
            result = f(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate cache entries matching a pattern"""
    try:
        # This would work with Redis cache
        if hasattr(cache.cache, 'delete_many'):
            cache.cache.delete_many(pattern)
        else:
            # For simple cache, we need to clear all
            cache.clear()
        logger.info(f"Invalidated cache pattern: {pattern}")
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")

class DatabaseOptimizer:
    """Database optimization utilities"""
    
    @staticmethod
    def analyze_slow_queries():
        """Analyze and report slow database queries"""
        slow_queries = []
        
        # Get recent audit logs for database operations
        recent_logs = AuditLog.query.filter(
            AuditLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        # Analyze query patterns
        query_patterns = {}
        for log in recent_logs:
            action = log.action
            resource_type = log.resource_type
            
            key = f"{action}_{resource_type}"
            if key not in query_patterns:
                query_patterns[key] = {
                    'count': 0,
                    'resource_type': resource_type,
                    'action': action
                }
            query_patterns[key]['count'] += 1
        
        return {
            'query_patterns': query_patterns,
            'total_operations': len(recent_logs),
            'analysis_period': '24 hours'
        }
    
    @staticmethod
    def get_table_sizes():
        """Get database table sizes"""
        try:
            # This would work with PostgreSQL
            # For SQLite, we'll use a simpler approach
            tables = ['users', 'claims', 'insurance_companies', 'payments', 'audit_logs', 'notifications']
            table_info = {}
            
            for table in tables:
                try:
                    result = db.session.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    table_info[table] = {'row_count': count}
                except Exception as e:
                    table_info[table] = {'error': str(e)}
            
            return table_info
        except Exception as e:
            logger.error(f"Error getting table sizes: {e}")
            return {}
    
    @staticmethod
    def optimize_database():
        """Run database optimization tasks"""
        try:
            # Analyze tables (SQLite specific)
            db.session.execute("ANALYZE")
            
            # Vacuum database to reclaim space
            db.session.execute("VACUUM")
            
            db.session.commit()
            
            logger.info("Database optimization completed")
            return True
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            db.session.rollback()
            return False

class HealthChecker:
    """Application health monitoring"""
    
    @staticmethod
    def check_database():
        """Check database connectivity"""
        try:
            db.session.execute("SELECT 1")
            return {'status': 'healthy', 'response_time': 0}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    @staticmethod
    def check_cache():
        """Check cache connectivity"""
        try:
            test_key = 'health_check_test'
            cache.set(test_key, 'test_value', timeout=10)
            value = cache.get(test_key)
            cache.delete(test_key)
            
            if value == 'test_value':
                return {'status': 'healthy'}
            else:
                return {'status': 'unhealthy', 'error': 'Cache read/write failed'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    @staticmethod
    def check_disk_space():
        """Check available disk space"""
        try:
            disk = psutil.disk_usage('/')
            free_percent = (disk.free / disk.total) * 100
            
            if free_percent < 10:
                return {'status': 'critical', 'free_percent': free_percent}
            elif free_percent < 20:
                return {'status': 'warning', 'free_percent': free_percent}
            else:
                return {'status': 'healthy', 'free_percent': free_percent}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    @staticmethod
    def get_health_status():
        """Get comprehensive health status"""
        return {
            'database': HealthChecker.check_database(),
            'cache': HealthChecker.check_cache(),
            'disk_space': HealthChecker.check_disk_space(),
            'system_metrics': performance_monitor.get_system_metrics(),
            'timestamp': datetime.utcnow().isoformat()
        }

# Initialize components
db_optimizer = DatabaseOptimizer()
health_checker = HealthChecker()
