import sqlite3
import os
from config.config import Config

# Database path
DB_PATH = Config.DATABASE_PATH

def get_db_connection():
    """Get database connection to existing database"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_database():
    """Add missing columns to existing tables if needed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    migrations = [
        ('attendances', 'fingerprint_hash', 'TEXT'),
        ('denied_attempts', 'fingerprint_hash', 'TEXT'),
        ('active_tokens', 'fingerprint_hash', 'TEXT'),
        ('active_tokens', 'device_signature', 'TEXT')
    ]
    
    for table, column, datatype in migrations:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if column not in columns:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {datatype}')
        except Exception as e:
            print(f"Migration error: {e}")
    
    conn.commit()
    conn.close()