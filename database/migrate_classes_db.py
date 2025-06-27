"""
Migration Script: Optimize Classes Database
This script migrates from the current redundant classes.db structure to an optimized normalized schema.

Before running:
1. Backup your current classes.db file
2. Ensure attendance.db has all student records

What this migration does:
1. Creates optimized tables in classes.db
2. Migrates existing class data from table names to normalized structure
3. Links students via enrollment table instead of duplicating data
4. Extracts professor information into separate management
5. Preserves all existing functionality while eliminating redundancy
"""

import sqlite3
import re
import json
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the current database"""
    import shutil
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def create_optimized_schema(db_path='classes.db'):
    """Create the new optimized schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read and execute the optimized schema
    with open('database/optimized_classes_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    try:
        # Execute each statement separately
        statements = schema_sql.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        print("✅ Optimized schema created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def extract_class_info_from_table_name(table_name):
    """Extract class name and professor from the current table naming convention"""
    # Pattern: Subject_Name___Professor_Name
    if '___' in table_name:
        parts = table_name.split('___')
        class_name = parts[0].replace('_', ' ')
        professor_name = parts[1].replace('_', ' ') if len(parts) > 1 else 'Unknown Professor'
    else:
        class_name = table_name.replace('_', ' ')
        professor_name = 'Unknown Professor'
    
    return class_name, professor_name

def migrate_existing_data(old_db_path='classes.db', attendance_db_path='attendance.db'):
    """Migrate data from old structure to new optimized structure"""
    
    # Get existing class tables
    conn_old = sqlite3.connect(old_db_path)
    cursor_old = conn_old.cursor()
    
    try:
        # Get all existing class tables (exclude sqlite_sequence)
        cursor_old.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name != 'sqlite_sequence'
            AND name NOT IN ('classes', 'class_enrollments', 'professors', 'class_schedules')
        """)
        old_tables = [row[0] for row in cursor_old.fetchall()]
        
        if not old_tables:
            print("ℹ️  No old class tables found to migrate")
            return True
        
        print(f"📋 Found {len(old_tables)} class tables to migrate:")
        for table in old_tables:
            print(f"   - {table}")
        
        # Process each old table
        migrated_classes = []
        for table_name in old_tables:
            class_name, professor_name = extract_class_info_from_table_name(table_name)
            
            # Get students from this table
            cursor_old.execute(f"SELECT student_id FROM {table_name}")
            student_ids = [row[0] for row in cursor_old.fetchall()]
            
            if student_ids:
                migrated_classes.append({
                    'table_name': table_name,
                    'class_name': class_name,
                    'professor_name': professor_name,
                    'student_ids': student_ids
                })
        
        # Insert into new schema
        conn_new = sqlite3.connect(old_db_path)  # Same file, new schema
        cursor_new = conn_new.cursor()
        
        for class_data in migrated_classes:
            try:
                # Insert professor if not exists
                cursor_new.execute("""
                    INSERT OR IGNORE INTO professors (professor_name, status)
                    VALUES (?, 'active')
                """, (class_data['professor_name'],))
                
                # Insert class
                cursor_new.execute("""
                    INSERT OR IGNORE INTO classes 
                    (class_name, professor_name, status, semester, academic_year)
                    VALUES (?, ?, 'active', '2025-1', '2024-2025')
                """, (class_data['class_name'], class_data['professor_name']))
                
                # Get class ID
                cursor_new.execute("""
                    SELECT id FROM classes 
                    WHERE class_name = ? AND professor_name = ?
                """, (class_data['class_name'], class_data['professor_name']))
                class_id = cursor_new.fetchone()[0]
                
                # Insert enrollments
                for student_id in class_data['student_ids']:
                    cursor_new.execute("""
                        INSERT OR IGNORE INTO class_enrollments 
                        (class_id, student_id, enrollment_status)
                        VALUES (?, ?, 'enrolled')
                    """, (class_id, student_id))
                
                print(f"✅ Migrated: {class_data['class_name']} - {class_data['professor_name']} ({len(class_data['student_ids'])} students)")
                
            except Exception as e:
                print(f"❌ Error migrating {class_data['table_name']}: {e}")
        
        conn_new.commit()
        conn_new.close()
        
        print(f"✅ Successfully migrated {len(migrated_classes)} classes")
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
    finally:
        conn_old.close()

def cleanup_old_tables(db_path='classes.db'):
    """Remove old redundant tables after successful migration"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get old tables to drop
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name != 'sqlite_sequence'
            AND name NOT IN ('classes', 'class_enrollments', 'professors', 'class_schedules')
        """)
        old_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"🗑️  Removing {len(old_tables)} old redundant tables...")
        for table in old_tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"   Dropped: {table}")
        
        conn.commit()
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
    finally:
        conn.close()

def verify_migration(db_path='classes.db'):
    """Verify the migration was successful"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check new tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('classes', 'class_enrollments', 'professors')
        """)
        new_tables = [row[0] for row in cursor.fetchall()]
        
        if len(new_tables) != 3:
            print("❌ Migration verification failed: Missing new tables")
            return False
        
        # Check data counts
        cursor.execute("SELECT COUNT(*) FROM classes")
        class_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM professors")
        professor_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM class_enrollments")
        enrollment_count = cursor.fetchone()[0]
        
        print("📊 Migration Results:")
        print(f"   Classes: {class_count}")
        print(f"   Professors: {professor_count}")
        print(f"   Enrollments: {enrollment_count}")
        
        # Test the summary view
        cursor.execute("SELECT * FROM class_summary LIMIT 3")
        summary_data = cursor.fetchall()
        
        if summary_data:
            print("✅ Class summary view working correctly")
            for row in summary_data:
                print(f"   {row[1]} - {row[2]} ({row[6]} students)")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False
    finally:
        conn.close()

def main():
    """Run the complete migration process"""
    print("🚀 Starting Classes Database Optimization Migration")
    print("=" * 60)
    
    # Step 1: Backup
    print("\n1️⃣  Creating backup...")
    backup_path = backup_database('classes.db')
    
    # Step 2: Create new schema
    print("\n2️⃣  Creating optimized schema...")
    if not create_optimized_schema():
        print("❌ Migration aborted due to schema creation failure")
        return False
    
    # Step 3: Migrate data
    print("\n3️⃣  Migrating existing data...")
    if not migrate_existing_data():
        print("❌ Migration aborted due to data migration failure")
        return False
    
    # Step 4: Verify migration
    print("\n4️⃣  Verifying migration...")
    if not verify_migration():
        print("❌ Migration verification failed")
        return False
    
    # Step 5: Cleanup (optional - ask user)
    print("\n5️⃣  Cleanup old tables...")
    response = input("Remove old redundant tables? (y/N): ").lower()
    if response == 'y':
        cleanup_old_tables()
    else:
        print("ℹ️  Old tables preserved. You can remove them manually later.")
    
    print("\n" + "=" * 60)
    print("🎉 Migration completed successfully!")
    print(f"📁 Backup saved as: {backup_path}")
    print("\nYour classes database is now optimized with:")
    print("✅ Eliminated data redundancy")
    print("✅ Proper normalization")
    print("✅ Professor management")
    print("✅ Flexible class scheduling")
    print("✅ Easy enrollment tracking")
    
    return True

if __name__ == "__main__":
    main()
