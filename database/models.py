"""
Database Models Module for Offline Attendance System

This module defines all database table schemas and handles database initialization
for the SQLite-based attendance tracking system.

Main Features:
- Table Definitions: Complete schema definitions for all database tables
- Database Initialization: Creates tables and sets up initial configuration
- Data Integrity: Foreign key relationships and constraints
- Default Settings: Initializes system configuration values
- Normalized Schema: Eliminates data duplication through proper foreign keys

Database Tables:
- students: Student information and attendance status
- class_attendees: Attendance records per session with device fingerprint references
- attendance_sessions: Session management and timing
- session_profiles: Reusable session templates
- tokens: QR code tokens with device fingerprint references
- denied_attempts: Failed check-in attempts with device fingerprint references
- device_fingerprints: Centralized device tracking and usage limits
- student_attendance_summary: Aggregated attendance statistics per student
- settings: System configuration and security settings

Key Improvements:
- Normalized device fingerprint data to eliminate duplication
- All device-related tables now reference device_fingerprints via foreign keys
- Consistent device tracking across attendance, tokens, and denied attempts
- Eliminated timestamp redundancy (consolidated to single meaningful column names)
- Added comprehensive database indexes for improved query performance
- Streamlined session management to reduce redundant session information
- Made session profiles mandatory for attendance sessions (better data integrity)

Key Functions:
- create_all_tables(): Initialize complete database schema
- migrate_tables(): Handle schema upgrades and data migration

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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'class_attendees': '''
        CREATE TABLE IF NOT EXISTS class_attendees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            token_id INTEGER,
            device_fingerprint_id INTEGER,
            checked_in_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES attendance_sessions (id) ON DELETE CASCADE,
            FOREIGN KEY (token_id) REFERENCES tokens (id) ON DELETE SET NULL,
            FOREIGN KEY (device_fingerprint_id) REFERENCES device_fingerprints (id) ON DELETE SET NULL,
            UNIQUE(student_id, session_id)
        )
    ''',
    
    'attendance_sessions': '''
        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            session_name TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            late_minutes INTEGER DEFAULT 15,
            is_active BOOLEAN DEFAULT FALSE,
            class_table TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES session_profiles (id) ON DELETE CASCADE
        )
    ''',
    
    'session_profiles': '''
        CREATE TABLE IF NOT EXISTS session_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_name TEXT NOT NULL UNIQUE,
            room_type TEXT NOT NULL,
            building TEXT,
            capacity INTEGER,
            organizer TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'tokens': '''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            device_fingerprint_id INTEGER,
            generated_at REAL NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            opened BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (device_fingerprint_id) REFERENCES device_fingerprints (id) ON DELETE SET NULL
        )
    ''',
    
    'denied_attempts': '''
        CREATE TABLE IF NOT EXISTS denied_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            token_id INTEGER,
            device_fingerprint_id INTEGER,
            session_id INTEGER,
            reason TEXT NOT NULL,
            attempted_at REAL NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE SET NULL,
            FOREIGN KEY (token_id) REFERENCES tokens (id) ON DELETE SET NULL,
            FOREIGN KEY (device_fingerprint_id) REFERENCES device_fingerprints (id) ON DELETE SET NULL,
            FOREIGN KEY (session_id) REFERENCES attendance_sessions (id) ON DELETE SET NULL
        )
    ''',
    
    'device_fingerprints': '''
        CREATE TABLE IF NOT EXISTS device_fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint_hash TEXT UNIQUE NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            usage_count INTEGER DEFAULT 1,
            device_info TEXT,
            is_blocked BOOLEAN DEFAULT FALSE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'student_attendance_summary': '''
        CREATE TABLE IF NOT EXISTS student_attendance_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            total_sessions INTEGER DEFAULT 0,
            present_count INTEGER DEFAULT 0,
            late_count INTEGER DEFAULT 0,
            absent_count INTEGER DEFAULT 0,
            last_session_id INTEGER,
            last_check_in TEXT,
            status TEXT DEFAULT 'active',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (last_session_id) REFERENCES attendance_sessions (id) ON DELETE SET NULL,
            UNIQUE(student_id)
        )
    ''',
    
    'settings': '''
        CREATE TABLE IF NOT EXISTS settings (
            id TEXT PRIMARY KEY,
            max_uses_per_device INTEGER DEFAULT 1,
            time_window_minutes INTEGER DEFAULT 1440,
            enable_fingerprint_blocking BOOLEAN DEFAULT TRUE,
            session_timeout_minutes INTEGER DEFAULT 30,
            max_devices_per_student INTEGER DEFAULT 3,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'session_enrollments': '''
        CREATE TABLE IF NOT EXISTS session_enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            student_id TEXT NOT NULL,
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES session_profiles (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
            UNIQUE(profile_id, student_id)
        )
    '''
}

# Indexes for better query performance
INDEXES = {
    'idx_class_attendees_student': 'CREATE INDEX IF NOT EXISTS idx_class_attendees_student ON class_attendees(student_id)',
    'idx_class_attendees_session': 'CREATE INDEX IF NOT EXISTS idx_class_attendees_session ON class_attendees(session_id)',
    'idx_class_attendees_device': 'CREATE INDEX IF NOT EXISTS idx_class_attendees_device ON class_attendees(device_fingerprint_id)',
    'idx_tokens_device': 'CREATE INDEX IF NOT EXISTS idx_tokens_device ON tokens(device_fingerprint_id)',
    'idx_tokens_generated': 'CREATE INDEX IF NOT EXISTS idx_tokens_generated ON tokens(generated_at)',
    'idx_denied_attempts_device': 'CREATE INDEX IF NOT EXISTS idx_denied_attempts_device ON denied_attempts(device_fingerprint_id)',
    'idx_denied_attempts_session': 'CREATE INDEX IF NOT EXISTS idx_denied_attempts_session ON denied_attempts(session_id)',
    'idx_denied_attempts_time': 'CREATE INDEX IF NOT EXISTS idx_denied_attempts_time ON denied_attempts(attempted_at)',
    'idx_device_fingerprints_hash': 'CREATE INDEX IF NOT EXISTS idx_device_fingerprints_hash ON device_fingerprints(fingerprint_hash)',
    'idx_sessions_profile': 'CREATE INDEX IF NOT EXISTS idx_sessions_profile ON attendance_sessions(profile_id)',
    'idx_sessions_active': 'CREATE INDEX IF NOT EXISTS idx_sessions_active ON attendance_sessions(is_active)',
    'idx_enrollments_profile': 'CREATE INDEX IF NOT EXISTS idx_enrollments_profile ON session_enrollments(profile_id)',
    'idx_enrollments_student': 'CREATE INDEX IF NOT EXISTS idx_enrollments_student ON session_enrollments(student_id)',
}

def create_all_tables():
    """
    Create all database tables with complete schema.
    
    This function initializes the entire database structure including:
    - All table definitions with proper constraints
    - Foreign key relationships
    - Default system settings
    - Data migration from old schema if needed
    
    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        # Use the migration function which handles both new installations and upgrades
        return migrate_tables()
        
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

def migrate_tables():
    """Apply database migrations and updates"""
    try:
        print("Running database migrations...")
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # Check if this is a new database or needs migration
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendances'")
        has_old_attendances = cursor.fetchone() is not None
        
        if has_old_attendances:
            print("Migrating from old schema to new normalized schema...")
            
            # Create new tables
            for table_name, query in TABLES.items():
                print(f"Creating/updating table: {table_name}")
                cursor.execute(query)
            
            # Create indexes for better performance
            print("Creating database indexes...")
            for index_name, index_query in INDEXES.items():
                try:
                    cursor.execute(index_query)
                except Exception as e:
                    print(f"Note: Could not create index {index_name}: {e}")
            
            # First, migrate device fingerprints data
            print("Migrating device fingerprint data...")
            cursor.execute('''
                INSERT OR IGNORE INTO device_fingerprints 
                (fingerprint_hash, first_seen, last_seen, usage_count, device_info, is_blocked)
                SELECT DISTINCT
                    COALESCE(fingerprint_hash, device_signature, 'unknown') as fingerprint_hash,
                    MIN(created_at) as first_seen,
                    MAX(created_at) as last_seen,
                    COUNT(*) as usage_count,
                    device_info,
                    FALSE as is_blocked
                FROM attendances 
                WHERE fingerprint_hash IS NOT NULL OR device_signature IS NOT NULL
                GROUP BY COALESCE(fingerprint_hash, device_signature), device_info
            ''')
            
            # Migrate attendance data with device fingerprint foreign keys
            print("Migrating attendance data with device fingerprint references...")
            cursor.execute('''
                INSERT OR IGNORE INTO class_attendees 
                (student_id, session_id, device_fingerprint_id, checked_in_at)
                SELECT 
                    a.student_id, 
                    COALESCE(a.session_id, 1) as session_id,
                    df.id as device_fingerprint_id,
                    COALESCE(a.created_at, datetime(a.timestamp, 'unixepoch')) as checked_in_at
                FROM attendances a
                LEFT JOIN device_fingerprints df ON 
                    df.fingerprint_hash = COALESCE(a.fingerprint_hash, a.device_signature, 'unknown')
                    AND (df.device_info = a.device_info OR (df.device_info IS NULL AND a.device_info IS NULL))
                WHERE a.student_id IS NOT NULL
            ''')
            
            # Migrate denied attempts data with device fingerprint references
            print("Migrating denied attempts data...")
            cursor.execute('''
                INSERT OR IGNORE INTO denied_attempts 
                (student_id, device_fingerprint_id, reason, attempted_at)
                SELECT 
                    da.student_id,
                    df.id as device_fingerprint_id,
                    da.reason,
                    COALESCE(da.timestamp, strftime('%s', da.created_at)) as attempted_at
                FROM denied_attempts da
                LEFT JOIN device_fingerprints df ON 
                    df.device_info = da.device_info
                WHERE NOT EXISTS (
                    SELECT 1 FROM denied_attempts AS new_denied 
                    WHERE new_denied.attempted_at = COALESCE(da.timestamp, strftime('%s', da.created_at))
                    AND new_denied.reason = da.reason
                )
            ''')
            
            # Migrate tokens data with device fingerprint references
            print("Migrating tokens data...")
            cursor.execute('''
                UPDATE tokens SET device_fingerprint_id = (
                    SELECT df.id FROM device_fingerprints df 
                    WHERE df.fingerprint_hash = tokens.device_fingerprint
                    LIMIT 1
                ),
                generated_at = COALESCE(tokens.timestamp, strftime('%s', tokens.created_at))
                WHERE device_fingerprint IS NOT NULL OR tokens.timestamp IS NOT NULL
            ''')
            
            # Create summary data for existing students
            print("Creating student attendance summaries...")
            cursor.execute('''
                INSERT OR REPLACE INTO student_attendance_summary 
                (student_id, total_sessions, present_count, absent_count, last_check_in, status)
                SELECT 
                    s.student_id,
                    COUNT(DISTINCT ca.session_id) as total_sessions,
                    COUNT(ca.id) as present_count,
                    0 as absent_count,  -- Will be calculated separately
                    MAX(ca.checked_in_at) as last_check_in,
                    'active' as status
                FROM students s
                LEFT JOIN class_attendees ca ON s.student_id = ca.student_id
                GROUP BY s.student_id
            ''')
            
            # Create default session profile for migration
            print("Creating default session profile for migration...")
            cursor.execute('''
                INSERT OR IGNORE INTO session_profiles (
                    profile_name, room_type, building, capacity, organizer
                )
                VALUES (?, ?, ?, ?, ?)
            ''', (
                'Default Session',
                'Classroom',
                'Main Building',
                50,
                'System Administrator'
            ))
            
            # Update any existing sessions to use default profile
            cursor.execute('''
                UPDATE attendance_sessions 
                SET profile_id = (SELECT id FROM session_profiles WHERE profile_name = 'Default Session' LIMIT 1)
                WHERE profile_id IS NULL
            ''')
            
            # Backup old tables by renaming them
            print("Backing up old tables...")
            try:
                cursor.execute('ALTER TABLE attendances RENAME TO attendances_backup')
                cursor.execute('ALTER TABLE active_tokens RENAME TO tokens_backup')
                print("Old tables backed up successfully")
            except Exception as e:
                print(f"Note: Could not backup old tables (may not exist): {e}")
            
        else:
            # Fresh installation - just create all tables
            print("Fresh installation detected - creating all tables...")
            for table_name, query in TABLES.items():
                print(f"Creating table: {table_name}")
                cursor.execute(query)
            
            # Create indexes for better performance
            print("Creating database indexes...")
            for index_name, index_query in INDEXES.items():
                try:
                    cursor.execute(index_query)
                except Exception as e:
                    print(f"Note: Could not create index {index_name}: {e}")
        
        # Insert default settings if not exists
        cursor.execute('SELECT * FROM settings WHERE id = ?', ('config',))
        if not cursor.fetchone():
            print("Inserting default settings...")
            cursor.execute('''
                INSERT INTO settings (
                    id, max_uses_per_device, time_window_minutes, 
                    enable_fingerprint_blocking, session_timeout_minutes, max_devices_per_student
                )
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'config', 
                DEFAULT_SETTINGS['max_uses_per_device'], 
                DEFAULT_SETTINGS['time_window_minutes'], 
                DEFAULT_SETTINGS['enable_fingerprint_blocking'],
                30,  # session_timeout_minutes
                3    # max_devices_per_student
            ))
        
        # Create default session profile if none exists
        cursor.execute('SELECT COUNT(*) FROM session_profiles')
        profile_count = cursor.fetchone()[0]
        if profile_count == 0:
            print("Creating default session profile...")
            cursor.execute('''
                INSERT INTO session_profiles (
                    profile_name, room_type, building, capacity, organizer
                )
                VALUES (?, ?, ?, ?, ?)
            ''', (
                'Default Session',
                'Classroom',
                'Main Building',
                50,
                'System Administrator'
            ))
        
        conn.commit()
        conn.close()
        
        print("Database migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during database migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_student_attendance_stats(student_id):
    """
    Get comprehensive attendance statistics for a student.
    
    Args:
        student_id (str): The student's ID
        
    Returns:
        dict: Student attendance statistics
    """
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get student basic info
        cursor.execute('''
            SELECT s.student_id, s.name, s.course, s.year,
                   sas.total_sessions, sas.present_count, sas.absent_count,
                   sas.last_check_in, sas.status
            FROM students s
            LEFT JOIN student_attendance_summary sas ON s.student_id = sas.student_id
            WHERE s.student_id = ?
        ''', (student_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None
            
        stats = {
            'student_id': result[0],
            'name': result[1],
            'course': result[2],
            'year': result[3],
            'total_sessions': result[4] or 0,
            'present_count': result[5] or 0,
            'absent_count': result[6] or 0,
            'last_check_in': result[7],
            'status': result[8] or 'active'
        }
        
        # Calculate attendance percentage
        if stats['total_sessions'] > 0:
            stats['attendance_percentage'] = (stats['present_count'] / stats['total_sessions']) * 100
        else:
            stats['attendance_percentage'] = 0
            
        conn.close()
        return stats
        
    except Exception as e:
        print(f"Error getting student attendance stats: {e}")
        return None

def update_student_attendance_summary(student_id):
    """
    Update the attendance summary for a specific student.
    
    Args:
        student_id (str): The student's ID
    """
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Calculate current stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT ca.session_id) as total_sessions,
                COUNT(ca.id) as present_count,
                MAX(ca.checked_in_at) as last_check_in
            FROM class_attendees ca
            WHERE ca.student_id = ?
        ''', (student_id,))
        
        stats = cursor.fetchone()
        if stats:
            total_sessions, present_count, last_check_in = stats
            absent_count = max(0, (total_sessions or 0) - (present_count or 0))
            
            # Update or insert summary
            cursor.execute('''
                INSERT OR REPLACE INTO student_attendance_summary 
                (student_id, total_sessions, present_count, absent_count, last_check_in, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (student_id, total_sessions or 0, present_count or 0, absent_count, last_check_in))
            
            conn.commit()
        
        conn.close()
        
    except Exception as e:
        print(f"Error updating student attendance summary: {e}")

def cleanup_old_tokens():
    """
    Clean up old/expired tokens from the database.
    """
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get time window from settings
        cursor.execute('SELECT time_window_minutes FROM settings WHERE id = ?', ('config',))
        result = cursor.fetchone()
        time_window = result[0] if result else 1440  # Default 24 hours
        
        # Calculate cutoff time
        import time
        cutoff_time = time.time() - (time_window * 60)
        
        # Delete old tokens
        cursor.execute('DELETE FROM tokens WHERE generated_at < ? AND used = TRUE', (cutoff_time,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old tokens")
            
    except Exception as e:
        print(f"Error cleaning up old tokens: {e}")

# Export table names for external use
TABLE_NAMES = list(TABLES.keys())

# ===================================================================
# OPTIMIZED CLASSES DATABASE SCHEMA
# This section provides the optimized schema for classes.db
# to eliminate data redundancy and improve performance
# ===================================================================

OPTIMIZED_CLASSES_TABLES = {
    'classes': '''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            professor_name TEXT NOT NULL,
            course_code TEXT,
            start_time TEXT,
            end_time TEXT,
            schedule_days TEXT, -- JSON array of days: ["Monday", "Wednesday", "Friday"]
            semester TEXT,
            academic_year TEXT,
            status TEXT DEFAULT 'active', -- active, inactive, completed
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(class_name, professor_name, semester, academic_year)
        )
    ''',
    
    'class_enrollments': '''
        CREATE TABLE IF NOT EXISTS class_enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            student_id TEXT NOT NULL,
            enrollment_status TEXT DEFAULT 'enrolled', -- enrolled, dropped, completed
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
            dropped_at TEXT,
            FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE CASCADE,
            UNIQUE(class_id, student_id)
        )
    ''',
    
    'professors': '''
        CREATE TABLE IF NOT EXISTS professors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_name TEXT NOT NULL UNIQUE,
            department TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'class_schedules': '''
        CREATE TABLE IF NOT EXISTS class_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL, -- Monday, Tuesday, etc.
            start_time TEXT NOT NULL,  -- HH:MM format
            end_time TEXT NOT NULL,    -- HH:MM format
            room TEXT,
            effective_from TEXT,       -- Start date for this schedule
            effective_until TEXT,      -- End date for this schedule
            FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE CASCADE
        )
    '''
}

OPTIMIZED_CLASSES_INDEXES = {
    'idx_classes_professor': 'CREATE INDEX IF NOT EXISTS idx_classes_professor ON classes(professor_name)',
    'idx_classes_status': 'CREATE INDEX IF NOT EXISTS idx_classes_status ON classes(status)',
    'idx_enrollments_class': 'CREATE INDEX IF NOT EXISTS idx_enrollments_class ON class_enrollments(class_id)',
    'idx_enrollments_student': 'CREATE INDEX IF NOT EXISTS idx_enrollments_student ON class_enrollments(student_id)',
    'idx_schedules_class': 'CREATE INDEX IF NOT EXISTS idx_schedules_class ON class_schedules(class_id)',
    'idx_schedules_day': 'CREATE INDEX IF NOT EXISTS idx_schedules_day ON class_schedules(day_of_week)',
}

OPTIMIZED_CLASSES_VIEWS = {
    'class_summary': '''
        CREATE VIEW IF NOT EXISTS class_summary AS
        SELECT 
            c.id as class_id,
            c.class_name,
            c.professor_name,
            c.course_code,
            c.semester,
            c.academic_year,
            c.status,
            COUNT(ce.student_id) as enrolled_students,
            GROUP_CONCAT(
                cs.day_of_week || ' ' || cs.start_time || '-' || cs.end_time, 
                '; '
            ) as schedule
        FROM classes c
        LEFT JOIN class_enrollments ce ON c.id = ce.class_id AND ce.enrollment_status = 'enrolled'
        LEFT JOIN class_schedules cs ON c.id = cs.class_id
        GROUP BY c.id, c.class_name, c.professor_name, c.course_code
    ''',
    
    'student_class_details': '''
        CREATE VIEW IF NOT EXISTS student_class_details AS
        SELECT 
            ce.student_id,
            c.id as class_id,
            c.class_name,
            c.professor_name,
            c.course_code,
            ce.enrollment_status,
            ce.enrolled_at,
            ce.dropped_at
        FROM class_enrollments ce
        JOIN classes c ON ce.class_id = c.id
    '''
}

def create_optimized_classes_schema(db_path='classes.db'):
    """
    Create the optimized classes database schema to replace redundant table-per-class approach.
    This eliminates data duplication and improves performance.
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Creating optimized classes database schema...")
        
        # Create tables
        for table_name, table_sql in OPTIMIZED_CLASSES_TABLES.items():
            cursor.execute(table_sql)
            print(f"✅ Created table: {table_name}")
        
        # Create indexes
        for index_name, index_sql in OPTIMIZED_CLASSES_INDEXES.items():
            cursor.execute(index_sql)
            print(f"✅ Created index: {index_name}")
        
        # Create views
        for view_name, view_sql in OPTIMIZED_CLASSES_VIEWS.items():
            cursor.execute(view_sql)
            print(f"✅ Created view: {view_name}")
        
        conn.commit()
        print("✅ Optimized classes schema created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating optimized schema: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_existing_classes_data(old_db_path='classes.db', attendance_db_path='attendance.db'):
    """
    Migrate existing class tables to the new optimized schema.
    Extracts class and professor information from table names and preserves student enrollments.
    """
    import sqlite3
    import re
    from datetime import datetime
    
    # Create backup first
    import shutil
    backup_path = f"{old_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(old_db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    conn = sqlite3.connect(old_db_path)
    cursor = conn.cursor()
    
    try:
        # Get existing class tables (exclude new optimized tables and sqlite_sequence)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name != 'sqlite_sequence'
            AND name NOT IN ('classes', 'class_enrollments', 'professors', 'class_schedules')
        """)
        old_tables = [row[0] for row in cursor.fetchall()]
        
        if not old_tables:
            print("ℹ️  No old class tables found to migrate")
            return True
        
        print(f"📋 Found {len(old_tables)} class tables to migrate:")
        for table in old_tables:
            print(f"   - {table}")
        
        migrated_count = 0
        for table_name in old_tables:
            # Extract class name and professor from table name
            if '___' in table_name:
                parts = table_name.split('___')
                class_name = parts[0].replace('_', ' ')
                professor_name = parts[1].replace('_', ' ') if len(parts) > 1 else 'Unknown Professor'
            else:
                class_name = table_name.replace('_', ' ')
                professor_name = 'Unknown Professor'
            
            # Get students from this table
            cursor.execute(f"SELECT student_id FROM {table_name}")
            student_ids = [row[0] for row in cursor.fetchall()]
            
            if student_ids:
                # Insert professor if not exists
                cursor.execute("""
                    INSERT OR IGNORE INTO professors (professor_name, status)
                    VALUES (?, 'active')
                """, (professor_name,))
                
                # Insert class
                cursor.execute("""
                    INSERT OR IGNORE INTO classes 
                    (class_name, professor_name, status, semester, academic_year)
                    VALUES (?, ?, 'active', '2025-1', '2024-2025')
                """, (class_name, professor_name))
                
                # Get class ID
                cursor.execute("""
                    SELECT id FROM classes 
                    WHERE class_name = ? AND professor_name = ?
                """, (class_name, professor_name))
                result = cursor.fetchone()
                if result:
                    class_id = result[0]
                    
                    # Insert enrollments
                    for student_id in student_ids:
                        cursor.execute("""
                            INSERT OR IGNORE INTO class_enrollments 
                            (class_id, student_id, enrollment_status)
                            VALUES (?, ?, 'enrolled')
                        """, (class_id, student_id))
                    
                    print(f"✅ Migrated: {class_name} - {professor_name} ({len(student_ids)} students)")
                    migrated_count += 1
        
        conn.commit()
        print(f"✅ Successfully migrated {migrated_count} classes to optimized schema")
        
        # Ask if user wants to remove old tables
        response = input("\nRemove old redundant tables? (y/N): ").lower()
        if response == 'y':
            for table in old_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"🗑️  Removed old table: {table}")
            conn.commit()
            print("✅ Old tables cleaned up")
        else:
            print("ℹ️  Old tables preserved. You can remove them manually later.")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()