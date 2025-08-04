"""
Database Schema Manager for Offline Attendance System

This module provides comprehensive database schema management, cleanup, and migration
functionality to resolve inconsistencies between old and new schemas.

Features:
- Schema validation and consistency checks
- Automated cleanup of redundant tables
- Complete migration from old to new schema
- Foreign key constraint validation
- Database optimization and maintenance

Used for resolving schema inconsistencies and ensuring data integrity.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from config.config import Config

class SchemaManager:
    """Manages database schema migrations and cleanup"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.classes_db_path = Config.CLASSES_DATABASE_PATH
        
    def validate_schema(self) -> Dict[str, any]:
        """Validate current database schema and identify issues"""
        issues = {
            'missing_tables': [],
            'orphaned_tables': [],
            'missing_foreign_keys': [],
            'redundant_data': [],
            'schema_version': None
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for required tables
            required_tables = [
                'students', 'class_attendees', 'attendance_sessions',
                'session_profiles', 'tokens', 'denied_attempts',
                'device_fingerprints', 'student_attendance_summary', 'settings'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table not in existing_tables:
                    issues['missing_tables'].append(table)
            
            # Check for old tables that should be removed
            old_patterns = ['attendances', 'active_tokens', 'attendances_backup', 'tokens_backup']
            for table in existing_tables:
                if any(pattern in table for pattern in old_patterns):
                    issues['orphaned_tables'].append(table)
            
            # Check foreign key constraints
            foreign_key_issues = self._check_foreign_keys(cursor)
            issues['missing_foreign_keys'] = foreign_key_issues
            
            # Check for redundant class tables
            class_tables = [t for t in existing_tables if '___' in t or 
                          (t not in required_tables and t != 'sqlite_sequence')]
            issues['redundant_data'] = class_tables
            
            conn.close()
            
        except Exception as e:
            issues['validation_error'] = str(e)
            
        return issues
    
    def _check_foreign_keys(self, cursor) -> List[str]:
        """Check for missing foreign key constraints"""
        issues = []
        
        # Expected foreign keys
        expected_fks = {
            'class_attendees': ['student_id', 'session_id', 'device_fingerprint_id'],
            'tokens': ['device_fingerprint_id'],
            'denied_attempts': ['device_fingerprint_id', 'session_id'],
            'attendance_sessions': ['profile_id'],
            'session_enrollments': ['profile_id', 'student_id']
        }
        
        for table, fk_columns in expected_fks.items():
            try:
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                existing_fks = [row[3] for row in cursor.fetchall()]  # from column
                
                for fk_col in fk_columns:
                    if fk_col not in existing_fks:
                        issues.append(f"{table}.{fk_col}")
            except sqlite3.Error:
                # Table might not exist
                pass
                
        return issues
    
    def cleanup_old_schema(self, backup: bool = True) -> bool:
        """Remove old/redundant tables and data"""
        try:
            if backup:
                self._create_backup()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get validation results
            issues = self.validate_schema()
            
            print("🧹 Cleaning up old schema...")
            
            # Remove orphaned tables
            for table in issues['orphaned_tables']:
                print(f"  - Removing orphaned table: {table}")
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            # Clean up redundant class tables
            if issues['redundant_data']:
                print(f"  - Found {len(issues['redundant_data'])} redundant class tables")
                response = input("Remove redundant class tables? (y/N): ").lower()
                if response == 'y':
                    for table in issues['redundant_data']:
                        print(f"    - Removing: {table}")
                        cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            conn.commit()
            conn.close()
            
            print("✅ Schema cleanup completed")
            return True
            
        except Exception as e:
            print(f"❌ Schema cleanup error: {e}")
            return False
    
    def migrate_to_normalized_schema(self) -> bool:
        """Complete migration to normalized schema"""
        try:
            print("🔄 Starting complete schema migration...")
            
            # Create backup
            self._create_backup()
            
            # Import and run the complete migration
            from database.models import migrate_tables, create_optimized_classes_schema
            
            # Run main database migration
            print("📊 Migrating main database...")
            if not migrate_tables():
                print("❌ Main database migration failed")
                return False
            
            # Create optimized classes schema
            print("📚 Creating optimized classes schema...")
            if not create_optimized_classes_schema():
                print("❌ Classes schema creation failed")
                return False
            
            # Migrate existing class data
            print("📋 Migrating class data...")
            from database.models import migrate_existing_classes_data
            if not migrate_existing_classes_data():
                print("❌ Class data migration failed")
                return False
            
            # Validate final schema
            print("✅ Validating migrated schema...")
            issues = self.validate_schema()
            if issues['missing_tables'] or issues['missing_foreign_keys']:
                print(f"⚠️  Migration completed with issues: {issues}")
            else:
                print("✅ Schema migration completed successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """Optimize database performance"""
        try:
            print("⚡ Optimizing database performance...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Update statistics
            print("  - Updating table statistics...")
            cursor.execute("ANALYZE")
            
            # Rebuild database
            print("  - Rebuilding database (VACUUM)...")
            cursor.execute("VACUUM")
            
            # Optimize page cache
            cursor.execute("PRAGMA cache_size = 10000")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            
            conn.commit()
            conn.close()
            
            print("✅ Database optimization completed")
            return True
            
        except Exception as e:
            print(f"❌ Database optimization error: {e}")
            return False
    
    def _create_backup(self) -> str:
        """Create database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            shutil.copy2(self.db_path, backup_path)
            print(f"📦 Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"⚠️  Backup creation failed: {e}")
            return None
    
    def get_schema_status(self) -> Dict[str, any]:
        """Get current schema status and health"""
        status = {
            'schema_version': 'normalized_v2',
            'tables_count': 0,
            'data_integrity': True,
            'optimization_needed': False,
            'issues': []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count tables
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            status['tables_count'] = cursor.fetchone()[0]
            
            # Check for issues
            issues = self.validate_schema()
            status['issues'] = issues
            
            # Check if optimization needed
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA freelist_count")
            free_pages = cursor.fetchone()[0]
            
            if free_pages > page_count * 0.1:  # More than 10% free pages
                status['optimization_needed'] = True
            
            conn.close()
            
        except Exception as e:
            status['error'] = str(e)
            status['data_integrity'] = False
            
        return status

def main():
    """Interactive schema management CLI"""
    manager = SchemaManager()
    
    print("🗄️  Database Schema Manager")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Validate current schema")
        print("2. Clean up old schema")
        print("3. Migrate to normalized schema")
        print("4. Optimize database")
        print("5. Show schema status")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            issues = manager.validate_schema()
            print("\n📋 Schema Validation Results:")
            for key, value in issues.items():
                if value:
                    print(f"  {key}: {value}")
                    
        elif choice == '2':
            manager.cleanup_old_schema()
            
        elif choice == '3':
            manager.migrate_to_normalized_schema()
            
        elif choice == '4':
            manager.optimize_database()
            
        elif choice == '5':
            status = manager.get_schema_status()
            print("\n📊 Schema Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
                
        elif choice == '6':
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()
