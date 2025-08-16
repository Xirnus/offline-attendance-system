"""
User Data Migration Module for Offline Attendance System

This module handles migration of database files from the old application directory
to the new user data directory structure. It ensures data persistence across
application updates and provides backup functionality.

Features:
- Automatic migration of existing databases
- Backup creation before migration
- Version-safe database handling
- User data directory management
- Legacy compatibility support

Used during application startup to ensure databases are in the correct location.
"""

import os
import shutil
import sqlite3
from datetime import datetime
import json
import sys
from config.config import Config


class UserDataMigration:
    """Handles migration of user data to persistent locations beside exe"""
    
    def __init__(self):
        self.new_database_dir = Config.DATABASE_DIR
        self.backup_dir = os.path.join(os.path.dirname(Config.DATABASE_DIR), 'backups')
        
        # Determine old database location (if any)
        if getattr(sys, 'frozen', False):
            # For exe, check if there are databases in old locations
            exe_dir = os.path.dirname(sys.executable)
            self.old_database_dirs = [
                os.path.join(exe_dir, 'database', 'db'),  # Old bundled location
                os.path.join(os.path.expanduser('~'), 'OfflineAttendanceSystem', 'database')  # Previous fix attempt
            ]
        else:
            self.old_database_dirs = []
    
    def needs_migration(self):
        """Check if migration is needed"""
        # Check if any old locations have databases
        for old_dir in self.old_database_dirs:
            if not os.path.exists(old_dir):
                continue
            
            old_attendance_db = os.path.join(old_dir, 'attendance.db')
            old_classes_db = os.path.join(old_dir, 'classes.db')
            
            if os.path.exists(old_attendance_db) or os.path.exists(old_classes_db):
                # Check if new location already has databases
                new_attendance_db = os.path.join(self.new_database_dir, 'attendance.db')
                new_classes_db = os.path.join(self.new_database_dir, 'classes.db')
                
                # Need migration if old databases exist and new ones don't
                new_exists = os.path.exists(new_attendance_db) or os.path.exists(new_classes_db)
                if not new_exists:
                    return True
        
        return False
    
    def create_backup(self, source_path, reason="migration"):
        """Create a backup of the database"""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy database files
            if os.path.exists(source_path):
                filename = os.path.basename(source_path)
                backup_file = os.path.join(backup_path, filename)
                shutil.copy2(source_path, backup_file)
                
                # Create backup info
                backup_info = {
                    "timestamp": timestamp,
                    "reason": reason,
                    "source_path": source_path,
                    "backed_up_files": [filename],
                    "backup_size": os.path.getsize(backup_file)
                }
                
                info_file = os.path.join(backup_path, "backup_info.json")
                with open(info_file, 'w') as f:
                    json.dump(backup_info, f, indent=2)
                
                return backup_path
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
            return None
    
    def validate_database(self, db_path):
        """Validate that a database file is not corrupted"""
        try:
            if not os.path.exists(db_path):
                return False
            
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA integrity_check")
            conn.close()
            return True
        except:
            return False
    
    def migrate_database_file(self, old_path, new_path):
        """Migrate a single database file"""
        try:
            if not os.path.exists(old_path):
                return True
            
            # Validate source database
            if not self.validate_database(old_path):
                print(f"Warning: Source database {old_path} appears corrupted, skipping migration")
                return False
            
            # Create backup
            backup_path = self.create_backup(old_path, "pre_migration")
            if backup_path:
                print(f"✓ Created backup at: {backup_path}")
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            # Copy the file
            shutil.copy2(old_path, new_path)
            
            # Validate copied database
            if self.validate_database(new_path):
                print(f"✓ Successfully migrated: {os.path.basename(old_path)}")
                return True
            else:
                # Restore from backup if validation fails
                if backup_path:
                    backup_file = os.path.join(backup_path, os.path.basename(old_path))
                    if os.path.exists(backup_file):
                        shutil.copy2(backup_file, new_path)
                print(f"✗ Migration validation failed for: {os.path.basename(old_path)}")
                return False
                
        except Exception as e:
            print(f"✗ Error migrating {old_path}: {e}")
            return False
    
    def perform_migration(self):
        """Perform the complete migration process"""
        if not self.needs_migration():
            return True
        
        print("🔄 Migrating databases to data folder beside exe...")
        print(f"   To: {self.new_database_dir}")
        
        success = True
        
        # Find and migrate from the first old location that has databases
        for old_dir in self.old_database_dirs:
            if not os.path.exists(old_dir):
                continue
            
            old_attendance = os.path.join(old_dir, 'attendance.db')
            old_classes = os.path.join(old_dir, 'classes.db')
            
            if os.path.exists(old_attendance) or os.path.exists(old_classes):
                print(f"   From: {old_dir}")
                
                # Migrate attendance database
                new_attendance = os.path.join(self.new_database_dir, 'attendance.db')
                if os.path.exists(old_attendance) and not os.path.exists(new_attendance):
                    if not self.migrate_database_file(old_attendance, new_attendance):
                        success = False
                
                # Migrate classes database
                new_classes = os.path.join(self.new_database_dir, 'classes.db')
                if os.path.exists(old_classes) and not os.path.exists(new_classes):
                    if not self.migrate_database_file(old_classes, new_classes):
                        success = False
                
                break  # Only migrate from the first location found
        
        if success:
            print("✅ Database migration completed successfully!")
            print(f"📁 Data location: {self.new_database_dir}")
            print(f"💾 Backups saved to: {self.backup_dir}")
        else:
            print("⚠️  Database migration completed with warnings")
        
        return success
    
    def get_user_data_info(self):
        """Get information about user data location"""
        info = {
            "user_data_dir": self.new_database_dir,
            "backup_dir": self.backup_dir,
            "databases": {
                "attendance": os.path.join(self.new_database_dir, 'attendance.db'),
                "classes": os.path.join(self.new_database_dir, 'classes.db')
            },
            "exists": {
                "attendance": os.path.exists(os.path.join(self.new_database_dir, 'attendance.db')),
                "classes": os.path.exists(os.path.join(self.new_database_dir, 'classes.db'))
            }
        }
        return info


def migrate_user_data():
    """Convenience function to perform migration"""
    migration = UserDataMigration()
    return migration.perform_migration()


def get_migration_info():
    """Get migration status information"""
    migration = UserDataMigration()
    return migration.get_user_data_info()


if __name__ == "__main__":
    # Test migration
    migrate_user_data()
    info = get_migration_info()
    print("\nUser Data Information:")
    print(json.dumps(info, indent=2))
