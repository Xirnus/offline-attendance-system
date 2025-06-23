"""
Database Models Module for Offline Attendance System

This module defines all database table schemas and handles database initialization, migrations, and structural changes for the SQLite-based attendance tracking system.

Main Features:
- Table Definitions: Complete schema definitions for all database tables
- Database Initialization: Creates tables and sets up initial configuration
- Migration System: Handles schema changes and column additions
- Data Integrity: Foreign key relationships and constraints
- Default Settings: Initializes system configuration values

Database Tables:
- students: Student information and attendance status
- student_attendance_history: Historical attendance records per session
- attendance_sessions: Session management and timing
- active_tokens: QR code tokens and validation
- attendances: Successful attendance check-ins
- denied_attempts: Failed check-in attempts with reasons
- device_fingerprints: Device tracking and usage limits
- settings: System configuration and security settings

Key Functions:
- create_all_tables(): Initialize complete database schema
- migrate_tables(): Apply structural changes and updates

Migration System:
- Automatic column additions for schema evolution
- Backward compatibility maintenance
- Safe migration execution with error handling

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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    'student_attendance_history': '''
        CREATE TABLE IF NOT EXISTS student_attendance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            status TEXT NOT NULL,
            session_id INTEGER,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
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
            course TEXT NOT NULL,
            year TEXT NOT NULL,
            device_info TEXT
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
    """Create all database tables"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        for table_name, query in TABLES.items():
            cursor.execute(query)
        
        # Insert default settings
        cursor.execute('SELECT * FROM settings WHERE id = ?', ('config',))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO settings (id, max_uses_per_device, time_window_minutes, enable_fingerprint_blocking)
                VALUES (?, ?, ?, ?)
            ''', ('config', DEFAULT_SETTINGS['max_uses_per_device'], 
                  DEFAULT_SETTINGS['time_window_minutes'], 
                  DEFAULT_SETTINGS['enable_fingerprint_blocking']))
        
        conn.commit()
        conn.close()
        
        # Run migrations after table creation
        migrate_tables()
        
    except Exception as e:
        print(f"Database initialization error: {e}")

def migrate_tables():
    """Apply database migrations"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    migrations = [
        ('attendances', 'fingerprint_hash', 'ALTER TABLE attendances ADD COLUMN fingerprint_hash TEXT'),
        ('denied_attempts', 'fingerprint_hash', 'ALTER TABLE denied_attempts ADD COLUMN fingerprint_hash TEXT'),
        ('active_tokens', 'fingerprint_hash', 'ALTER TABLE active_tokens ADD COLUMN fingerprint_hash TEXT'),
        ('active_tokens', 'device_signature', 'ALTER TABLE active_tokens ADD COLUMN device_signature TEXT'),
        ('attendances', 'device_signature', 'ALTER TABLE attendances ADD COLUMN device_signature TEXT'),
        ('denied_attempts', 'device_signature', 'ALTER TABLE denied_attempts ADD COLUMN device_signature TEXT'),
        ('students', 'year', 'ALTER TABLE students ADD COLUMN year TEXT'),
        ('students', 'last_check_in', 'ALTER TABLE students ADD COLUMN last_check_in TEXT'),
        ('students', 'status', 'ALTER TABLE students ADD COLUMN status TEXT DEFAULT NULL'),
        ('students', 'absent_count', 'ALTER TABLE students ADD COLUMN absent_count INTEGER DEFAULT 0'),
        ('students', 'present_count', 'ALTER TABLE students ADD COLUMN present_count INTEGER DEFAULT 0'),
        ('attendances', 'student_id', 'ALTER TABLE attendances ADD COLUMN student_id TEXT'),
    ]
    
    for table, column, query in migrations:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if column not in columns:
                cursor.execute(query)
        except Exception as e:
            continue  # Skip failed migrations silently
    
    conn.commit()
    conn.close()