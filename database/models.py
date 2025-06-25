"""
Database Models Module for Offline Attendance System

This module defines all database table schemas and handles database initialization
for the SQLite-based attendance tracking system.

Main Features:
- Table Definitions: Complete schema definitions for all database tables
- Database Initialization: Creates tables and sets up initial configuration
- Data Integrity: Foreign key relationships and constraints
- Default Settings: Initializes system configuration values

Database Tables:
- students: Student information and attendance status
- student_attendance_history: Historical attendance records per session
- attendance_sessions: Session management and timing
- session_profiles: Reusable session templates
- active_tokens: QR code tokens and validation
- attendances: Successful attendance check-ins
- denied_attempts: Failed check-in attempts with reasons
- device_fingerprints: Device tracking and usage limits
- settings: System configuration and security settings

Key Functions:
- create_all_tables(): Initialize complete database schema

Used by: Database connection module, initialization scripts
Dependencies: SQLite3, config settings
"""

import sqlite3
from config import Config, DEFAULT_SETTINGS

TABLES = {
    'students': '''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            year INTEGER NOT NULL,
            last_check_in TEXT,
            status TEXT DEFAULT NULL,
            absent_count INTEGER DEFAULT 0,
            present_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            session_id INTEGER,
            last_session_id INTEGER,
            total_sessions INTEGER DEFAULT 0,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES attendance_sessions (id) ON DELETE SET NULL
        )
    ''',
    
    'attendance_sessions': '''
        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            profile_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES session_profiles (id)
        )
    ''',
    
    'session_profiles': '''
        CREATE TABLE IF NOT EXISTS session_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_name TEXT NOT NULL,
            room_type TEXT NOT NULL,
            building TEXT,
            capacity INTEGER,
            organizer TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'active_tokens': '''
        CREATE TABLE IF NOT EXISTS active_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            timestamp REAL NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            opened BOOLEAN DEFAULT FALSE,
            device_signature TEXT,
            fingerprint_hash TEXT,
            created_at TEXT NOT NULL
        )
    ''',
    
    'attendances': '''
        CREATE TABLE IF NOT EXISTS attendances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            token TEXT NOT NULL,
            fingerprint_hash TEXT,
            timestamp REAL NOT NULL,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            year TEXT NOT NULL,
            device_info TEXT,
            device_signature TEXT
        )
    ''',
    
    'denied_attempts': '''
        CREATE TABLE IF NOT EXISTS denied_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL,
            fingerprint_hash TEXT,
            timestamp REAL NOT NULL,
            created_at TEXT NOT NULL,
            reason TEXT NOT NULL,
            name TEXT NOT NULL,
            device_info TEXT,
            device_signature TEXT
        )
    ''',
    
    'device_fingerprints': '''
        CREATE TABLE IF NOT EXISTS device_fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint_hash TEXT UNIQUE NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            usage_count INTEGER DEFAULT 1,
            device_info TEXT
        )
    ''',
    
    'settings': '''
        CREATE TABLE IF NOT EXISTS settings (
            id TEXT PRIMARY KEY,
            max_uses_per_device INTEGER DEFAULT 1,
            time_window_minutes INTEGER DEFAULT 1440,
            enable_fingerprint_blocking BOOLEAN DEFAULT TRUE
        )
    '''
}

def create_all_tables():
    """
    Create all database tables with complete schema.
    
    This function initializes the entire database structure including:
    - All table definitions with proper constraints
    - Foreign key relationships
    - Default system settings
    
    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # Create all tables
        for table_name, query in TABLES.items():
            print(f"Creating table: {table_name}")
            cursor.execute(query)
        
        # Insert default settings if not exists
        cursor.execute('SELECT * FROM settings WHERE id = ?', ('config',))
        if not cursor.fetchone():
            print("Inserting default settings...")
            cursor.execute('''
                INSERT INTO settings (id, max_uses_per_device, time_window_minutes, enable_fingerprint_blocking)
                VALUES (?, ?, ?, ?)
            ''', (
                'config', 
                DEFAULT_SETTINGS['max_uses_per_device'], 
                DEFAULT_SETTINGS['time_window_minutes'], 
                DEFAULT_SETTINGS['enable_fingerprint_blocking']
            ))
        
        conn.commit()
        conn.close()
        
        print("Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def get_table_info(table_name):
    """
    Get information about a specific table structure.
    
    Args:
        table_name (str): Name of the table to inspect
        
    Returns:
        list: List of column information tuples
    """
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        conn.close()
        return columns
        
    except Exception as e:
        print(f"Error getting table info for {table_name}: {e}")
        return []

def verify_database_integrity():
    """
    Verify database integrity and check for any issues.
    
    Returns:
        dict: Dictionary containing integrity check results
    """
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check PRAGMA integrity
        cursor.execute('PRAGMA integrity_check')
        integrity_result = cursor.fetchone()[0]
        
        # Check foreign key integrity
        cursor.execute('PRAGMA foreign_key_check')
        foreign_key_issues = cursor.fetchall()
        
        # Get table counts
        table_counts = {}
        for table_name in TABLES.keys():
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            table_counts[table_name] = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'integrity_ok': integrity_result == 'ok',
            'integrity_result': integrity_result,
            'foreign_key_issues': foreign_key_issues,
            'table_counts': table_counts
        }
        
    except Exception as e:
        print(f"Error verifying database integrity: {e}")
        return {
            'integrity_ok': False,
            'error': str(e)
        }

# Export table names for external use
TABLE_NAMES = list(TABLES.keys())