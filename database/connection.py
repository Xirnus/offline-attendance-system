"""
Database Connection Module for Offline Attendance System

This module handles all database connection management and provides robust SQLite connectivity with concurrency support, retry mechanisms, and performance optimizations.

Main Features:
- Connection Management: Creates and manages SQLite database connections
- Retry Logic: Automatic retry mechanism for database lock scenarios
- Concurrency Support: WAL mode and optimized settings for multi-user access
- Performance Optimization: Caching, memory storage, and connection pooling
- Error Handling: Graceful handling of database errors and timeouts

Key Functions:
- get_db_connection(): Creates optimized SQLite connection with performance settings
- get_db_connection_with_retry(): Connection with automatic retry on database locks
- retry_db_operation(): Decorator for adding retry logic to database operations
- execute_with_retry(): Execute queries with built-in retry mechanism

Database Optimizations:
- WAL (Write-Ahead Logging) mode for better concurrency
- Increased cache size and memory-based temp storage
- Extended timeout settings for busy database scenarios
- Foreign key constraints enabled for data integrity

Used by: All database operation modules throughout the application
Dependencies: SQLite3, config settings, database models
"""

import sqlite3
import os
import time
from functools import wraps
from config import Config

def retry_db_operation(max_retries=3, delay=0.1):
    """Decorator to retry database operations if database is locked"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _delay = delay  # Initialize local delay variable
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        time.sleep(_delay)
                        _delay *= 2  # Exponential backoff
                        continue
                    else:
                        raise e
            return None
        return wrapper
    return decorator

def get_db_connection():
    """Get database connection with optimized settings for concurrency"""
    try:
        if not os.path.exists(Config.DATABASE_PATH):
            from .models import create_all_tables
            create_all_tables()
        
        conn = sqlite3.connect(
            Config.DATABASE_PATH,
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        
        # Enable optimizations for better concurrency
        conn.execute('PRAGMA journal_mode = WAL')
        conn.execute('PRAGMA synchronous = NORMAL')
        conn.execute('PRAGMA cache_size = 10000')
        conn.execute('PRAGMA temp_store = memory')
        conn.execute('PRAGMA mmap_size = 268435456')
        conn.execute('PRAGMA busy_timeout = 30000')
        conn.execute('PRAGMA foreign_keys = ON')
        
        return conn
    except Exception as e:
        raise e

@retry_db_operation()
def get_db_connection_with_retry():
    """Get database connection with automatic retry on lock"""
    return get_db_connection()

def execute_with_retry(query, params=None, fetch=False):
    """Execute a query with automatic retry on database lock"""
    @retry_db_operation()
    def _execute():
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                if fetch == 'one':
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
            else:
                result = cursor.rowcount
            
            conn.commit()
            return result
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    return _execute()