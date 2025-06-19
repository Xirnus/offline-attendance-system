import sqlite3
import os
from config import Config

def get_db_connection():
    """Get database connection with error handling"""
    try:
        if not os.path.exists(Config.DATABASE_PATH):
            from .models import create_all_tables
            create_all_tables()
        
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA journal_mode = WAL')
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise