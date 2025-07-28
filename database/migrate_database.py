#!/usr/bin/env python3
"""
Database Migration Script for Offline Attendance System

This script migrates the database from the old schema to the new normalized schema.
It safely preserves existing data while improving the database structure.

Usage:
    python migrate_database.py

Features:
- Backs up existing data before migration
- Creates new normalized tables
- Migrates existing data to new structure
- Removes duplicate data
- Improves database performance
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import migrate_tables, verify_database_integrity
from config.config import Config

def backup_database():
    """Create a backup of the current database"""
    try:
        if os.path.exists(Config.DATABASE_PATH):
            backup_path = f"{Config.DATABASE_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(Config.DATABASE_PATH, backup_path)
            print(f"Database backed up to: {backup_path}")
            return backup_path
        else:
            print("No existing database found - proceeding with fresh installation")
            return None
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def show_database_info(title):
    """Show current database information"""
    print(f"\n{title}")
    print("=" * len(title))
    
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"Tables in database: {len(tables)}")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} records")
        
        conn.close()
        
    except Exception as e:
        print(f"Error getting database info: {e}")

def main():
    """Main migration function"""
    print("Offline Attendance System - Database Migration")
    print("=" * 50)
    
    # Show current database state
    if os.path.exists(Config.DATABASE_PATH):
        show_database_info("BEFORE MIGRATION")
    
    # Create backup
    backup_path = backup_database()
    
    # Run migration
    print("\nStarting database migration...")
    try:
        success = migrate_tables()
        
        if success:
            print("\n✅ Migration completed successfully!")
            
            # Show new database state
            show_database_info("AFTER MIGRATION")
            
            # Verify integrity
            print("\nVerifying database integrity...")
            integrity = verify_database_integrity()
            
            if integrity['integrity_ok']:
                print("✅ Database integrity check passed!")
                print(f"Table counts: {integrity['table_counts']}")
            else:
                print("❌ Database integrity check failed!")
                print(f"Issues: {integrity}")
                
                if backup_path:
                    print(f"You can restore from backup: {backup_path}")
                    
        else:
            print("\n❌ Migration failed!")
            if backup_path:
                print(f"You can restore from backup: {backup_path}")
                
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        
        if backup_path:
            print(f"You can restore from backup: {backup_path}")

if __name__ == "__main__":
    main()
