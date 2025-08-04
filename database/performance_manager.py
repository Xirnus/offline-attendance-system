"""
Database Connection Pool and Performance Manager for Offline Attendance System

This module provides database connection pooling, query optimization, and caching
to improve performance and scalability.

Features:
- Connection pooling for SQLite
- Query result caching
- Database optimization utilities
- Connection management
- Performance monitoring
- Automatic cleanup and maintenance

Replaces direct database connections with managed pool connections.
"""

import sqlite3
import threading
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from contextlib import contextmanager
from config.config import Config
from utils.logging_system import get_logger, monitor_performance, DatabaseOperationLogger

class ConnectionPool:
    """SQLite connection pool manager"""
    
    def __init__(self, database_path: str, max_connections: int = 10):
        self.database_path = database_path
        self.max_connections = max_connections
        self.connections = []
        self.in_use = set()
        self.lock = threading.Lock()
        self.logger = get_logger()
        
        # Initialize pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            for _ in range(min(3, self.max_connections)):  # Start with 3 connections
                conn = self._create_connection()
                if conn:
                    self.connections.append(conn)
            
            self.logger.log_event('info', f"Connection pool initialized with {len(self.connections)} connections",
                                component='database', action='pool_init')
        except Exception as e:
            self.logger.log_error(e, "connection_pool_init")
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new database connection with optimizations"""
        try:
            conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=30.0
            )
            
            # Enable optimizations
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA mmap_size = 268435456")  # 256MB
            
            # Set row factory for easier data access
            conn.row_factory = sqlite3.Row
            
            return conn
        except Exception as e:
            self.logger.log_error(e, "create_connection")
            return None
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool (context manager)"""
        conn = None
        try:
            conn = self._acquire_connection()
            yield conn
        finally:
            if conn:
                self._release_connection(conn)
    
    def _acquire_connection(self) -> sqlite3.Connection:
        """Acquire connection from pool"""
        with self.lock:
            # Try to get existing connection
            for conn in self.connections:
                if conn not in self.in_use:
                    try:
                        # Test connection
                        conn.execute("SELECT 1")
                        self.in_use.add(conn)
                        return conn
                    except sqlite3.Error:
                        # Connection is broken, remove it
                        self.connections.remove(conn)
                        try:
                            conn.close()
                        except:
                            pass
            
            # Create new connection if under limit
            if len(self.connections) < self.max_connections:
                conn = self._create_connection()
                if conn:
                    self.connections.append(conn)
                    self.in_use.add(conn)
                    return conn
            
            # Wait for connection to become available
            self.logger.log_event('warning', "Connection pool exhausted, waiting...",
                                component='database', action='pool_wait')
        
        # Retry after brief wait
        time.sleep(0.1)
        return self._acquire_connection()
    
    def _release_connection(self, conn: sqlite3.Connection):
        """Release connection back to pool"""
        with self.lock:
            if conn in self.in_use:
                self.in_use.remove(conn)
                
                # Test connection health
                try:
                    conn.execute("SELECT 1")
                    # Connection is healthy, keep it
                except sqlite3.Error:
                    # Connection is broken, remove it
                    if conn in self.connections:
                        self.connections.remove(conn)
                    try:
                        conn.close()
                    except:
                        pass
    
    def close_all(self):
        """Close all connections in pool"""
        with self.lock:
            for conn in self.connections:
                try:
                    conn.close()
                except:
                    pass
            self.connections.clear()
            self.in_use.clear()

class QueryCache:
    """Simple query result cache"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.lock = threading.Lock()
        self.logger = get_logger()
    
    def get(self, query: str, params: tuple = None) -> Optional[List[sqlite3.Row]]:
        """Get cached query result"""
        cache_key = self._make_key(query, params)
        
        with self.lock:
            if cache_key in self.cache:
                data, timestamp = self.cache[cache_key]
                
                # Check if expired
                if time.time() - timestamp > self.ttl_seconds:
                    del self.cache[cache_key]
                    if cache_key in self.access_times:
                        del self.access_times[cache_key]
                    return None
                
                # Update access time
                self.access_times[cache_key] = time.time()
                self.logger.log_event('debug', "Cache hit", component='cache', action='hit')
                return data
        
        return None
    
    def set(self, query: str, params: tuple = None, result: List[sqlite3.Row] = None):
        """Cache query result"""
        cache_key = self._make_key(query, params)
        
        with self.lock:
            # Evict old entries if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            self.cache[cache_key] = (result, time.time())
            self.access_times[cache_key] = time.time()
            self.logger.log_event('debug', "Cache set", component='cache', action='set')
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        with self.lock:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
            
            if keys_to_remove:
                self.logger.log_event('debug', f"Invalidated {len(keys_to_remove)} cache entries",
                                    component='cache', action='invalidate')
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.logger.log_event('debug', "Cache cleared", component='cache', action='clear')
    
    def _make_key(self, query: str, params: tuple = None) -> str:
        """Generate cache key"""
        key_data = query
        if params:
            key_data += str(params)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]

class OptimizedDatabase:
    """High-performance database manager with pooling and caching"""
    
    def __init__(self, database_path: str = None):
        self.database_path = database_path or Config.DATABASE_PATH
        self.pool = ConnectionPool(self.database_path)
        self.cache = QueryCache()
        self.logger = get_logger()
        
        # Track query performance
        self.query_stats = {}
        self.stats_lock = threading.Lock()
    
    @monitor_performance("database_query")
    def execute_query(self, query: str, params: tuple = None, 
                     fetch: str = None, cache_result: bool = False) -> Any:
        """Execute query with performance monitoring and caching"""
        
        # Check cache first for SELECT queries
        if cache_result and query.strip().upper().startswith('SELECT'):
            cached_result = self.cache.get(query, params)
            if cached_result is not None:
                return cached_result
        
        start_time = time.time()
        
        try:
            with self.pool.get_connection() as conn:
                with DatabaseOperationLogger("query", self._extract_table_name(query)):
                    cursor = conn.cursor()
                    
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    # Handle different fetch types
                    if fetch == 'one':
                        result = cursor.fetchone()
                    elif fetch == 'all':
                        result = cursor.fetchall()
                    elif fetch is None and query.strip().upper().startswith('SELECT'):
                        result = cursor.fetchall()
                    else:
                        result = cursor.rowcount
                        conn.commit()
                    
                    # Cache SELECT results if requested
                    if cache_result and query.strip().upper().startswith('SELECT') and result:
                        self.cache.set(query, params, result)
                    
                    # Track query performance
                    self._track_query_performance(query, time.time() - start_time)
                    
                    return result
                    
        except Exception as e:
            self.logger.log_error(e, f"database_query: {query[:100]}...")
            raise
    
    @monitor_performance("database_transaction")
    def execute_transaction(self, queries: List[Tuple[str, tuple]]) -> bool:
        """Execute multiple queries in a transaction"""
        try:
            with self.pool.get_connection() as conn:
                with DatabaseOperationLogger("transaction", "multiple"):
                    cursor = conn.cursor()
                    
                    try:
                        for query, params in queries:
                            if params:
                                cursor.execute(query, params)
                            else:
                                cursor.execute(query)
                        
                        conn.commit()
                        
                        # Invalidate relevant cache entries
                        for query, _ in queries:
                            if not query.strip().upper().startswith('SELECT'):
                                table_name = self._extract_table_name(query)
                                self.cache.invalidate_pattern(table_name)
                        
                        return True
                        
                    except Exception as e:
                        conn.rollback()
                        raise e
                        
        except Exception as e:
            self.logger.log_error(e, "database_transaction")
            return False
    
    def get_student_attendance_summary(self, student_id: str) -> Optional[sqlite3.Row]:
        """Get student attendance summary with caching"""
        query = """
            SELECT s.*, sas.total_sessions, sas.present_count, sas.absent_count, 
                   sas.last_check_in, sas.status
            FROM students s
            LEFT JOIN student_attendance_summary sas ON s.student_id = sas.student_id
            WHERE s.student_id = ?
        """
        
        result = self.execute_query(query, (student_id,), fetch='one', cache_result=True)
        return result
    
    def get_active_session(self) -> Optional[sqlite3.Row]:
        """Get active session with caching"""
        query = "SELECT * FROM attendance_sessions WHERE is_active = 1 LIMIT 1"
        return self.execute_query(query, fetch='one', cache_result=True)
    
    def update_attendance_summary(self, student_id: str):
        """Update student attendance summary and invalidate cache"""
        queries = [
            ("""
                UPDATE student_attendance_summary 
                SET total_sessions = (
                    SELECT COUNT(DISTINCT session_id) 
                    FROM class_attendees 
                    WHERE student_id = ?
                ),
                present_count = (
                    SELECT COUNT(*) 
                    FROM class_attendees 
                    WHERE student_id = ?
                ),
                updated_at = datetime('now')
                WHERE student_id = ?
            """, (student_id, student_id, student_id))
        ]
        
        success = self.execute_transaction(queries)
        
        if success:
            # Invalidate related cache entries
            self.cache.invalidate_pattern('student_attendance_summary')
            self.cache.invalidate_pattern('students')
        
        return success
    
    def optimize_database(self):
        """Run database optimization"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                self.logger.log_event('info', "Starting database optimization",
                                    component='database', action='optimize')
                
                # Update statistics
                cursor.execute("ANALYZE")
                
                # Rebuild database
                cursor.execute("VACUUM")
                
                self.logger.log_event('info', "Database optimization completed",
                                    component='database', action='optimize')
                
        except Exception as e:
            self.logger.log_error(e, "database_optimization")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        with self.stats_lock:
            stats = {
                'total_queries': sum(data['count'] for data in self.query_stats.values()),
                'avg_query_time': 0,
                'slow_queries': [],
                'cache_stats': {
                    'size': len(self.cache.cache),
                    'max_size': self.cache.max_size
                },
                'pool_stats': {
                    'total_connections': len(self.pool.connections),
                    'active_connections': len(self.pool.in_use),
                    'max_connections': self.pool.max_connections
                }
            }
            
            if self.query_stats:
                total_time = sum(data['total_time'] for data in self.query_stats.values())
                total_count = sum(data['count'] for data in self.query_stats.values())
                stats['avg_query_time'] = total_time / total_count if total_count > 0 else 0
                
                # Find slow queries
                for query, data in self.query_stats.items():
                    avg_time = data['total_time'] / data['count']
                    if avg_time > 1.0:  # Slower than 1 second
                        stats['slow_queries'].append({
                            'query': query[:100] + '...' if len(query) > 100 else query,
                            'avg_time': avg_time,
                            'count': data['count']
                        })
            
            return stats
    
    def _extract_table_name(self, query: str) -> str:
        """Extract table name from SQL query"""
        query_upper = query.upper().strip()
        
        if query_upper.startswith('SELECT'):
            if ' FROM ' in query_upper:
                parts = query_upper.split(' FROM ')[1].split()
                return parts[0] if parts else 'unknown'
        elif query_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
            if query_upper.startswith('INSERT INTO'):
                parts = query_upper.split('INSERT INTO ')[1].split()
            elif query_upper.startswith('UPDATE'):
                parts = query_upper.split('UPDATE ')[1].split()
            elif query_upper.startswith('DELETE FROM'):
                parts = query_upper.split('DELETE FROM ')[1].split()
            else:
                return 'unknown'
            
            return parts[0] if parts else 'unknown'
        
        return 'unknown'
    
    def _track_query_performance(self, query: str, duration: float):
        """Track query performance statistics"""
        with self.stats_lock:
            query_key = query[:200]  # Limit key length
            
            if query_key not in self.query_stats:
                self.query_stats[query_key] = {
                    'count': 0,
                    'total_time': 0.0,
                    'max_time': 0.0
                }
            
            stats = self.query_stats[query_key]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['max_time'] = max(stats['max_time'], duration)
    
    def close(self):
        """Close database connections and cleanup"""
        self.pool.close_all()
        self.cache.clear()

# Global database instance
_db_instance = None

def get_optimized_db() -> OptimizedDatabase:
    """Get global optimized database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = OptimizedDatabase()
    return _db_instance

# Context manager for database operations
@contextmanager
def db_operation(operation_name: str = "database_operation"):
    """Context manager for database operations with logging"""
    start_time = time.time()
    logger = get_logger()
    
    try:
        yield get_optimized_db()
        duration_ms = (time.time() - start_time) * 1000
        logger.log_performance(operation_name, duration_ms)
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.log_error(e, operation_name)
        raise
