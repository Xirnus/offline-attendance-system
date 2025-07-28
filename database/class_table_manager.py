import sqlite3
from config.config import Config

def convert_year_to_integer(year_level):
    """Convert year level to integer for database storage"""
    if isinstance(year_level, int):
        return year_level
    
    year_str = str(year_level).lower().strip()
    
    # Extract numeric value from common year level formats
    if '1st' in year_str or 'first' in year_str or year_str == '1':
        return 1
    elif '2nd' in year_str or 'second' in year_str or year_str == '2':
        return 2
    elif '3rd' in year_str or 'third' in year_str or year_str == '3':
        return 3
    elif '4th' in year_str or 'fourth' in year_str or year_str == '4':
        return 4
    elif '5th' in year_str or 'fifth' in year_str or year_str == '5':
        return 5
    
    # Try to extract any number from the string
    import re
    match = re.search(r'(\d+)', year_str)
    if match:
        return int(match.group(1))
    
    # Default to 1 if no valid year found
    print(f"Warning: Unable to parse year level: {year_level}, defaulting to 1")
    return 1

def add_students_to_class(class_name, students, db_path=None):
    """
    Add students to the main students table with class_table identifier.
    :param class_name: Name of the class (will be sanitized and used as class_table value)
    :param students: List of student dictionaries
    :param db_path: Path to the attendance database file (default: Config.DATABASE_PATH)
    """
    if db_path is None:
        db_path = Config.DATABASE_PATH
    # Sanitize class name
    class_table = class_name.replace(' ', '_').replace('-', '_')
    class_table = ''.join(c for c in class_table if c.isalnum() or c == '_')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        for student in students:
            # Convert year level safely
            year_level_raw = student.get('yearLevel', '')
            year_level_int = convert_year_to_integer(year_level_raw) if year_level_raw else 1
            
            cursor.execute('''
                INSERT OR REPLACE INTO students (student_id, name, course, year, created_at, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            ''', (
                student.get('studentId', ''),
                student.get('studentName', ''),
                student.get('course', ''),
                year_level_int
            ))
            
            # Initialize student attendance summary
            cursor.execute('''
                INSERT OR IGNORE INTO student_attendance_summary 
                (student_id, total_sessions, present_count, absent_count, status, updated_at)
                VALUES (?, 0, 0, 0, 'active', datetime('now'))
            ''', (student.get('studentId', ''),))
        
        conn.commit()
        print(f"Successfully added {len(students)} students to class '{class_name}' (table: {class_table})")
        
    except Exception as e:
        print(f"Error adding students to class: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_students_by_class(class_table, db_path='attendance.db'):
    """
    Get all students belonging to a specific class with their attendance data.
    :param class_table: The class table identifier
    :param db_path: Path to the attendance database file
    :return: List of student dictionaries
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                s.student_id, 
                s.name, 
                s.course, 
                s.year, 
                s.created_at,
                sas.status,
                COALESCE(sas.present_count, 0) as present_count,
                COALESCE(sas.absent_count, 0) as absent_count,
                COALESCE(sas.total_sessions, 0) as total_sessions,
                sas.last_check_in
            FROM students s
            LEFT JOIN student_attendance_summary sas ON s.student_id = sas.student_id
            ORDER BY s.name
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        students = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return students
        
    except Exception as e:
        print(f"Error getting students for class {class_table}: {e}")
        return []
    finally:
        conn.close()

def get_all_classes(db_path='attendance.db'):
    """
    Get all unique classes from the students table.
    Since we removed class_table column, we'll group by course instead.
    :param db_path: Path to the attendance database file
    :return: List of class dictionaries with course name and student count
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT course, COUNT(*) as student_count
            FROM students 
            WHERE course IS NOT NULL AND course != ''
            GROUP BY course
            ORDER BY course
        ''')
        
        classes = []
        for row in cursor.fetchall():
            course, student_count = row
            # Use course as both display name and identifier
            classes.append({
                'table_name': course.replace(' ', '_').replace('-', '_'),
                'display_name': course,
                'student_count': student_count
            })
        
        return classes
        
    except Exception as e:
        print(f"Error getting class list: {e}")
        return []
    finally:
        conn.close()

def delete_class(course_name, db_path='attendance.db'):
    """
    Delete all students belonging to a specific course.
    :param course_name: The course name identifier
    :param db_path: Path to the attendance database file
    :return: Number of students deleted
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First get student IDs to clean up their attendance summaries
        cursor.execute('SELECT student_id FROM students WHERE course = ?', (course_name,))
        student_ids = [row[0] for row in cursor.fetchall()]
        
        # Delete attendance summaries for these students
        for student_id in student_ids:
            cursor.execute('DELETE FROM student_attendance_summary WHERE student_id = ?', (student_id,))
        
        # Delete the students
        cursor.execute('DELETE FROM students WHERE course = ?', (course_name,))
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"Deleted {deleted_count} students from course '{course_name}'")
        return deleted_count
        
    except Exception as e:
        print(f"Error deleting course {course_name}: {e}")
        return 0
    finally:
        conn.close()

def check_normalized_schema(db_path='attendance.db'):
    """
    Check if the database has been migrated to the new normalized schema.
    :param db_path: Path to the attendance database file
    :return: True if normalized schema exists, False otherwise
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if new tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('class_attendees', 'student_attendance_summary', 'device_fingerprints')
        """)
        new_tables = cursor.fetchall()
        
        return len(new_tables) >= 3  # All three new tables should exist
        
    except sqlite3.Error as e:
        print(f"Error checking schema: {e}")
        return False
    finally:
        conn.close()

def migrate_to_normalized_schema(db_path='attendance.db'):
    """
    Migrate the database to use the new normalized schema.
    This function is now obsolete as migration is handled by models.py
    """
    if check_normalized_schema(db_path):
        print("Database already uses normalized schema")
        return True
    else:
        print("Database migration needed. Please run the migration from models.py")
        print("Use: python -c 'from database.models import create_all_tables; create_all_tables()'")
        return False

def fix_database_columns(db_path='attendance.db'):
    """
    Check if database needs migration to normalized schema.
    """
    print("Checking database schema...")
    if check_normalized_schema(db_path):
        print("✅ Database uses normalized schema")
    else:
        print("❌ Database needs migration to normalized schema")
        print("Please run: python -c 'from database.models import create_all_tables; create_all_tables()'")
    print("Database check completed!")

def get_students_by_course(course_name, db_path='attendance.db'):
    """
    Get all students belonging to a specific course with their attendance data.
    :param course_name: The course name
    :param db_path: Path to the attendance database file
    :return: List of student dictionaries
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                s.student_id, 
                s.name, 
                s.course, 
                s.year, 
                s.created_at,
                sas.status,
                COALESCE(sas.present_count, 0) as present_count,
                COALESCE(sas.absent_count, 0) as absent_count,
                COALESCE(sas.total_sessions, 0) as total_sessions,
                sas.last_check_in
            FROM students s
            LEFT JOIN student_attendance_summary sas ON s.student_id = sas.student_id
            WHERE s.course = ?
            ORDER BY s.name
        ''', (course_name,))
        
        columns = [desc[0] for desc in cursor.description]
        students = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return students
        
    except Exception as e:
        print(f"Error getting students for course {course_name}: {e}")
        return []
    finally:
        conn.close()

def get_session_attendance_for_course(course_name, session_id, db_path='attendance.db'):
    """
    Get attendance data for a specific course and session.
    :param course_name: The course name
    :param session_id: The session ID
    :param db_path: Path to the attendance database file
    :return: Dictionary with attendance statistics
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get total students in course
        cursor.execute('SELECT COUNT(*) FROM students WHERE course = ?', (course_name,))
        total_students = cursor.fetchone()[0]
        
        # Get students who attended
        cursor.execute('''
            SELECT COUNT(*) FROM class_attendees ca
            JOIN students s ON ca.student_id = s.student_id
            WHERE s.course = ? AND ca.session_id = ?
        ''', (course_name, session_id))
        present_count = cursor.fetchone()[0]
        
        absent_count = total_students - present_count
        
        return {
            'course': course_name,
            'session_id': session_id,
            'total_students': total_students,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_percentage': (present_count / total_students * 100) if total_students > 0 else 0
        }
        
    except Exception as e:
        print(f"Error getting session attendance for course {course_name}: {e}")
        return {}
    finally:
        conn.close()

# Legacy functions for backward compatibility (now redirect to new functions)
def create_class_table(table_name, columns, db_path=None):
    """Create a table for a specific class in classes.db"""
    if db_path is None:
        db_path = Config.CLASSES_DATABASE_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create table with specified columns
        column_definitions = ', '.join([f'{name} {type_}' for name, type_ in columns])
        create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({column_definitions})'
        
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"Created/verified table '{table_name}' in {db_path}")
        
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
    finally:
        conn.close()

def insert_students(table_name, students, db_path=None):
    """Insert students into a specific class table in classes.db"""
    if db_path is None:
        db_path = Config.CLASSES_DATABASE_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Insert students into the class table
        for student in students:
            cursor.execute(f'''
                INSERT OR REPLACE INTO "{table_name}" (student_id, student_name, year_level, course)
                VALUES (?, ?, ?, ?)
            ''', (
                student.get('studentId', ''),
                student.get('studentName', ''),
                student.get('yearLevel', ''),
                student.get('course', '')
            ))
        
        conn.commit()
        print(f"Successfully added {len(students)} students to class table '{table_name}' in {db_path}")
        
    except Exception as e:
        print(f"Error inserting students into table {table_name}: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Check database schema compatibility
    fix_database_columns()

# ===================================================================
# OPTIMIZED CLASS MANAGEMENT FUNCTIONS
# THESE FUNCTIONS WORK WITH THE NEW OPTIMIZED CLASSES.DB SCHEMA
# TO ELIMINATE DATA REDUNDANCY AND IMPROVE PERFORMANCE
# ===================================================================

class OptimizedClassManager:
    """Manages classes using the optimized normalized schema instead of table-per-class approach"""
    
    def __init__(self, classes_db_path=None, attendance_db_path=None):
        self.classes_db_path = classes_db_path or Config.CLASSES_DATABASE_PATH
        self.attendance_db_path = attendance_db_path or Config.DATABASE_PATH
    
    def create_class(self, class_name, professor_name, course_code=None, 
                    semester=None, academic_year=None):
        """
        Create a new class with professor information
        Returns the class ID
        """
        import sqlite3
        conn = sqlite3.connect(self.classes_db_path)
        cursor = conn.cursor()
        
        try:
            # Set defaults
            if not semester:
                semester = "2025-1"
            if not academic_year:
                academic_year = "2024-2025"
            
            # Insert professor if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO professors (professor_name, status)
                VALUES (?, 'active')
            """, (professor_name,))
            
            # Insert class
            cursor.execute("""
                INSERT INTO classes 
                (class_name, professor_name, course_code, semester, academic_year, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (class_name, professor_name, course_code, semester, academic_year))
            
            class_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ Created class: {class_name} - {professor_name} (ID: {class_id})")
            return class_id
            
        except sqlite3.IntegrityError:
            # Class already exists, get existing ID
            cursor.execute("""
                SELECT id FROM classes 
                WHERE class_name = ? AND professor_name = ? AND semester = ? AND academic_year = ?
            """, (class_name, professor_name, semester, academic_year))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Error creating class: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def enroll_students(self, class_id, student_ids):
        """
        Enroll multiple students in a class
        Returns number of students successfully enrolled
        """
        import sqlite3
        conn = sqlite3.connect(self.classes_db_path)
        cursor = conn.cursor()
        
        enrolled_count = 0
        try:
            for student_id in student_ids:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO class_enrollments 
                        (class_id, student_id, enrollment_status)
                        VALUES (?, ?, 'enrolled')
                    """, (class_id, student_id))
                    
                    if cursor.rowcount > 0:
                        enrolled_count += 1
                        
                except Exception as e:
                    print(f"❌ Error enrolling student {student_id}: {e}")
            
            conn.commit()
            print(f"✅ Enrolled {enrolled_count}/{len(student_ids)} students in class ID {class_id}")
            return enrolled_count
            
        except Exception as e:
            print(f"❌ Error during enrollment: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def get_all_classes(self):
        """Get all classes with summary information"""
        import sqlite3
        conn = sqlite3.connect(self.classes_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM class_summary ORDER BY class_name, professor_name")
            
            columns = [desc[0] for desc in cursor.description]
            classes = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return classes
            
        except Exception as e:
            print(f"❌ Error getting classes: {e}")
            return []
        finally:
            conn.close()
    
    def get_class_students(self, class_id):
        """Get all students enrolled in a specific class with their details from attendance.db"""
        import sqlite3
        
        # Get enrolled student IDs from classes.db
        conn_classes = sqlite3.connect(self.classes_db_path)
        cursor_classes = conn_classes.cursor()
        
        try:
            cursor_classes.execute("""
                SELECT student_id, enrollment_status, enrolled_at
                FROM class_enrollments 
                WHERE class_id = ? AND enrollment_status = 'enrolled'
            """, (class_id,))
            
            enrollments = cursor_classes.fetchall()
            if not enrollments:
                return []
            
        except Exception as e:
            print(f"❌ Error getting class enrollments: {e}")
            return []
        finally:
            conn_classes.close()
        
        # Get student details from attendance.db
        conn_attendance = sqlite3.connect(self.attendance_db_path)
        cursor_attendance = conn_attendance.cursor()
        
        students = []
        try:
            for student_id, enrollment_status, enrolled_at in enrollments:
                cursor_attendance.execute("""
                    SELECT s.student_id, s.name, s.course, s.year,
                           COALESCE(sas.present_count, 0) as present_count,
                           COALESCE(sas.absent_count, 0) as absent_count,
                           COALESCE(sas.total_sessions, 0) as total_sessions,
                           sas.last_check_in, sas.status
                    FROM students s
                    LEFT JOIN student_attendance_summary sas ON s.student_id = sas.student_id
                    WHERE s.student_id = ?
                """, (student_id,))
                
                result = cursor_attendance.fetchone()
                if result:
                    student_data = {
                        'student_id': result[0],
                        'name': result[1],
                        'course': result[2],
                        'year': result[3],
                        'present_count': result[4],
                        'absent_count': result[5],
                        'total_sessions': result[6],
                        'last_check_in': result[7],
                        'attendance_status': result[8],
                        'enrollment_status': enrollment_status,
                        'enrolled_at': enrolled_at
                    }
                    students.append(student_data)
            
            return students
            
        except Exception as e:
            print(f"❌ Error getting student details: {e}")
            return []
        finally:
            conn_attendance.close()
    
    def import_from_excel_data(self, class_name, professor_name, student_data, metadata=None):
        """
        Import class data from Excel upload (replacement for old table-per-class method)
        """
        try:
            # Create class (metadata no longer needed for room/venue info)
            class_id = self.create_class(
                class_name=class_name,
                professor_name=professor_name
            )
            
            if not class_id:
                return None
            
            # Extract student IDs
            student_ids = [student.get('studentId') for student in student_data if student.get('studentId')]
            
            # Ensure students exist in attendance.db first
            self._ensure_students_exist(student_data)
            
            # Enroll students
            enrolled_count = self.enroll_students(class_id, student_ids)
            
            print(f"✅ Successfully imported class: {class_name} - {professor_name}")
            print(f"   Students enrolled: {enrolled_count}/{len(student_ids)}")
            
            return class_id
            
        except Exception as e:
            print(f"❌ Error importing class data: {e}")
            return None
    
    def _ensure_students_exist(self, student_data):
        """Ensure all students exist in the attendance.db students table"""
        import sqlite3
        conn = sqlite3.connect(self.attendance_db_path)
        cursor = conn.cursor()
        
        try:
            for student in student_data:
                student_id = student.get('studentId')
                if not student_id:
                    continue
                
                # Convert year level
                year_level = convert_year_to_integer(student.get('yearLevel', ''))
                
                cursor.execute("""
                    INSERT OR REPLACE INTO students (student_id, name, course, year, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (
                    student_id,
                    student.get('studentName', ''),
                    student.get('course', ''),
                    year_level
                ))
                
                # Initialize attendance summary if not exists
                cursor.execute("""
                    INSERT OR IGNORE INTO student_attendance_summary 
                    (student_id, total_sessions, present_count, absent_count, status, updated_at)
                    VALUES (?, 0, 0, 0, 'active', datetime('now'))
                """, (student_id,))
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ Error ensuring students exist: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def delete_class(self, class_id):
        """Delete a class and all its enrollments"""
        import sqlite3
        conn = sqlite3.connect(self.classes_db_path)
        cursor = conn.cursor()
        
        try:
            # Check if class exists
            cursor.execute("SELECT class_name, professor_name FROM classes WHERE id = ?", (class_id,))
            result = cursor.fetchone()
            if not result:
                print(f"❌ Class {class_id} not found")
                return False
            
            class_name, professor_name = result
            print(f"🗑️  Deleting class: {class_name} - {professor_name}")
            
            # Delete enrollments first (will be handled by foreign key cascade)
            cursor.execute("DELETE FROM class_enrollments WHERE class_id = ?", (class_id,))
            enrollments_deleted = cursor.rowcount
            
            # Delete schedules
            cursor.execute("DELETE FROM class_schedules WHERE class_id = ?", (class_id,))
            schedules_deleted = cursor.rowcount
            
            # Delete the class
            cursor.execute("DELETE FROM classes WHERE id = ?", (class_id,))
            class_deleted = cursor.rowcount
            
            conn.commit()
            
            if class_deleted > 0:
                print(f"✅ Successfully deleted class {class_id} ({enrollments_deleted} enrollments, {schedules_deleted} schedules)")
                return True
            else:
                print(f"❌ Failed to delete class {class_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting class {class_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def unenroll_student(self, class_id, student_id):
        """Remove a student from a class"""
        import sqlite3
        conn = sqlite3.connect(self.classes_db_path)
        cursor = conn.cursor()
        
        try:
            # Check if enrollment exists
            cursor.execute("""
                SELECT id FROM class_enrollments 
                WHERE class_id = ? AND student_id = ? AND enrollment_status = 'enrolled'
            """, (class_id, student_id))
            
            result = cursor.fetchone()
            if not result:
                print(f"❌ Student {student_id} not enrolled in class {class_id}")
                return False
            
            # Update enrollment status instead of deleting (for audit trail)
            cursor.execute("""
                UPDATE class_enrollments 
                SET enrollment_status = 'dropped', dropped_at = CURRENT_TIMESTAMP
                WHERE class_id = ? AND student_id = ?
            """, (class_id, student_id))
            
            updated = cursor.rowcount
            conn.commit()
            
            if updated > 0:
                print(f"✅ Successfully unenrolled student {student_id} from class {class_id}")
                return True
            else:
                print(f"❌ Failed to unenroll student {student_id} from class {class_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error unenrolling student {student_id} from class {class_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
# Backward compatibility functions - use these to gradually migrate your existing code
def create_class_optimized(class_name, professor_name, students, metadata=None):
    """Legacy wrapper for creating classes with the optimized schema"""
    manager = OptimizedClassManager()
    class_id = manager.import_from_excel_data(class_name, professor_name, students, metadata)
    return class_id is not None

def get_all_classes_optimized():
    """Legacy wrapper for getting all classes"""
    manager = OptimizedClassManager()
    return manager.get_all_classes()

def get_class_students_optimized(class_name, professor_name):
    """Legacy wrapper for getting class students by name"""
    manager = OptimizedClassManager()
    
    # Find class by name and professor
    classes = manager.get_all_classes()
    for class_data in classes:
        if (class_data['class_name'] == class_name and 
            class_data['professor_name'] == professor_name):
            return manager.get_class_students(class_data['class_id'])
    
    return []

# Function to setup optimized schema
def setup_optimized_classes_db():
    """Initialize the optimized classes database schema"""
    from .models import create_optimized_classes_schema
    return create_optimized_classes_schema()

def migrate_to_optimized_schema():
    """Migrate existing class tables to optimized schema"""
    from .models import migrate_existing_classes_data
    return migrate_existing_classes_data()