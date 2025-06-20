import sqlite3
from config import Config, DEFAULT_SETTINGS

TABLES = {
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
            token TEXT NOT NULL,
            fingerprint_hash TEXT,
            timestamp REAL NOT NULL,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            year TEXT NOT NULL,
            device_info TEXT
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
            print(f"✓ {table_name} table ready")
        
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
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")


def migrate_tables():
    """Apply database migrations"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Migration: Add missing columns
    migrations = [
        ('attendances', 'fingerprint_hash', 'ALTER TABLE attendances ADD COLUMN fingerprint_hash TEXT'),
        ('denied_attempts', 'fingerprint_hash', 'ALTER TABLE denied_attempts ADD COLUMN fingerprint_hash TEXT'),
        ('active_tokens', 'fingerprint_hash', 'ALTER TABLE active_tokens ADD COLUMN fingerprint_hash TEXT'),
        ('active_tokens', 'device_signature', 'ALTER TABLE active_tokens ADD COLUMN device_signature TEXT'),
        ('attendances', 'device_signature', 'ALTER TABLE attendances ADD COLUMN device_signature TEXT'),
        ('denied_attempts', 'device_signature', 'ALTER TABLE denied_attempts ADD COLUMN device_signature TEXT'),
    ]
    
    for table, column, query in migrations:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if column not in columns:
                cursor.execute(query)
                print(f"✓ Added {column} to {table}")
        except Exception as e:
            print(f"Migration error for {table}.{column}: {e}")
    
    conn.commit()
    conn.close()