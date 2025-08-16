"""
Manual Backup Utility for Offline Attendance System

This script allows users to manually create backups of their attendance data
and restore from backups if needed. Useful for regular maintenance and before
major updates.

Usage:
    python backup_utility.py backup    # Create a backup
    python backup_utility.py restore   # List and restore from backups
    python backup_utility.py list      # List available backups
"""

import os
import sys
import shutil
import json
from datetime import datetime
import argparse

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from database.user_data_migration import UserDataMigration


def create_manual_backup():
    """Create a manual backup of all databases"""
    migration = UserDataMigration()
    
    print("🔄 Creating manual backup...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"manual_backup_{timestamp}"
    backup_path = os.path.join(migration.backup_dir, backup_name)
    
    try:
        os.makedirs(backup_path, exist_ok=True)
        
        backed_up_files = []
        total_size = 0
        
        # Backup attendance database
        attendance_db = Config.DATABASE_PATH
        if os.path.exists(attendance_db):
            filename = os.path.basename(attendance_db)
            backup_file = os.path.join(backup_path, filename)
            shutil.copy2(attendance_db, backup_file)
            backed_up_files.append(filename)
            total_size += os.path.getsize(backup_file)
            print(f"✓ Backed up: {filename}")
        
        # Backup classes database
        classes_db = Config.CLASSES_DATABASE_PATH
        if os.path.exists(classes_db):
            filename = os.path.basename(classes_db)
            backup_file = os.path.join(backup_path, filename)
            shutil.copy2(classes_db, backup_file)
            backed_up_files.append(filename)
            total_size += os.path.getsize(backup_file)
            print(f"✓ Backed up: {filename}")
        
        if not backed_up_files:
            print("⚠️  No databases found to backup")
            os.rmdir(backup_path)
            return False
        
        # Create backup info
        backup_info = {
            "timestamp": timestamp,
            "reason": "manual_backup",
            "source_dir": Config.DATABASE_DIR,
            "backed_up_files": backed_up_files,
            "total_size": total_size,
            "backup_size_mb": round(total_size / (1024 * 1024), 2)
        }
        
        info_file = os.path.join(backup_path, "backup_info.json")
        with open(info_file, 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        print(f"✅ Backup created successfully!")
        print(f"📁 Location: {backup_path}")
        print(f"📊 Size: {backup_info['backup_size_mb']} MB")
        print(f"📋 Files: {', '.join(backed_up_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def list_backups():
    """List all available backups"""
    migration = UserDataMigration()
    
    if not os.path.exists(migration.backup_dir):
        print("📁 No backups directory found")
        return []
    
    backup_dirs = []
    for item in os.listdir(migration.backup_dir):
        backup_path = os.path.join(migration.backup_dir, item)
        if os.path.isdir(backup_path):
            info_file = os.path.join(backup_path, "backup_info.json")
            if os.path.exists(info_file):
                try:
                    with open(info_file, 'r') as f:
                        backup_info = json.load(f)
                    backup_info['path'] = backup_path
                    backup_info['name'] = item
                    backup_dirs.append(backup_info)
                except:
                    pass
    
    # Sort by timestamp (newest first)
    backup_dirs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    if not backup_dirs:
        print("📁 No backups found")
        return []
    
    print(f"📋 Found {len(backup_dirs)} backup(s):")
    print("-" * 80)
    
    for i, backup in enumerate(backup_dirs, 1):
        timestamp = backup['timestamp']
        reason = backup.get('reason', 'unknown')
        size_mb = backup.get('backup_size_mb', 0)
        files = backup.get('backed_up_files', [])
        
        # Format timestamp for display
        try:
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_str = timestamp
        
        print(f"{i:2d}. {backup['name']}")
        print(f"    Date: {date_str}")
        print(f"    Type: {reason}")
        print(f"    Size: {size_mb} MB")
        print(f"    Files: {', '.join(files)}")
        print()
    
    return backup_dirs


def restore_from_backup():
    """Interactive restore from backup"""
    backups = list_backups()
    
    if not backups:
        return False
    
    try:
        print("Select a backup to restore from:")
        choice = input("Enter backup number (or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            return False
        
        backup_num = int(choice)
        if backup_num < 1 or backup_num > len(backups):
            print("❌ Invalid backup number")
            return False
        
        selected_backup = backups[backup_num - 1]
        backup_path = selected_backup['path']
        
        print(f"\n⚠️  This will overwrite current databases with backup from:")
        print(f"   {selected_backup['timestamp']}")
        print(f"   Type: {selected_backup.get('reason', 'unknown')}")
        print(f"   Files: {', '.join(selected_backup.get('backed_up_files', []))}")
        
        confirm = input("\nAre you sure? (type 'yes' to confirm): ").strip().lower()
        if confirm != 'yes':
            print("❌ Restore cancelled")
            return False
        
        # Create a backup of current state before restoring
        print("\n🔄 Creating backup of current state...")
        create_manual_backup()
        
        # Restore files
        print("🔄 Restoring from backup...")
        restored_files = []
        
        for filename in selected_backup.get('backed_up_files', []):
            source_file = os.path.join(backup_path, filename)
            
            if filename == 'attendance.db':
                dest_file = Config.DATABASE_PATH
            elif filename == 'classes.db':
                dest_file = Config.CLASSES_DATABASE_PATH
            else:
                continue
            
            if os.path.exists(source_file):
                shutil.copy2(source_file, dest_file)
                restored_files.append(filename)
                print(f"✓ Restored: {filename}")
        
        if restored_files:
            print(f"\n✅ Restore completed!")
            print(f"📋 Restored files: {', '.join(restored_files)}")
            print("🔄 Please restart the attendance system")
        else:
            print("❌ No files were restored")
        
        return True
        
    except ValueError:
        print("❌ Please enter a valid number")
        return False
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Backup utility for Offline Attendance System')
    parser.add_argument('action', choices=['backup', 'restore', 'list'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    print("🏫 Offline Attendance System - Backup Utility")
    print("=" * 50)
    
    if args.action == 'backup':
        create_manual_backup()
    elif args.action == 'list':
        list_backups()
    elif args.action == 'restore':
        restore_from_backup()


if __name__ == "__main__":
    main()
