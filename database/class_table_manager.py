import sqlite3

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

def add_students_to_class(class_name, students, db_path='attendance.db'):
    """
    Add students to the main students table with class_table identifier.
    :param class_name: Name of the class (will be sanitized and used as class_table value)
    :param students: List of student dictionaries
    :param db_path: Path to the attendance database file (default: 'attendance.db')
    """
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
                INSERT OR REPLACE INTO students (student_id, name, course, year, class_table, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (
                student.get('studentId', ''),
                student.get('studentName', ''),
                student.get('course', ''),
                year_level_int,
                class_table
            ))
        
        conn.commit()
        print(f"Successfully added {len(students)} students to class '{class_name}' (table: {class_table})")
        
    except Exception as e:
        print(f"Error adding students to class: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_students_by_class(class_table, db_path='attendance.db'):
    """
    Get all students belonging to a specific class.
    :param class_table: The class table identifier
    :param db_path: Path to the attendance database file
    :return: List of student dictionaries
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT student_id, name, course, year, class_table, status, 
                   absent_count, present_count, created_at
            FROM students 
            WHERE class_table = ?
            ORDER BY name
        ''', (class_table,))
        
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
    Get all unique class tables from the students table.
    :param db_path: Path to the attendance database file
    :return: List of class dictionaries with table_name and student count
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT class_table, COUNT(*) as student_count
            FROM students 
            WHERE class_table IS NOT NULL AND class_table != ''
            GROUP BY class_table
            ORDER BY class_table
        ''')
        
        classes = []
        for row in cursor.fetchall():
            class_table, student_count = row
            # Convert class_table back to display name
            display_name = class_table.replace('_', ' ').replace('-', ' - ')
            
            classes.append({
                'table_name': class_table,
                'display_name': display_name,
                'student_count': student_count
            })
        
        return classes
        
    except Exception as e:
        print(f"Error getting class list: {e}")
        return []
    finally:
        conn.close()

def delete_class(class_table, db_path='attendance.db'):
    """
    Delete all students belonging to a specific class.
    :param class_table: The class table identifier
    :param db_path: Path to the attendance database file
    :return: Number of students deleted
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM students WHERE class_table = ?', (class_table,))
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"Deleted {deleted_count} students from class '{class_table}'")
        return deleted_count
        
    except Exception as e:
        print(f"Error deleting class {class_table}: {e}")
        return 0
    finally:
        conn.close()

def add_class_table_column_to_students(db_path='attendance.db'):
    """
    Add the class_table column to the students table if it doesn't exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(students)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'class_table' not in columns:
            # Add the class_table column
            cursor.execute("ALTER TABLE students ADD COLUMN class_table TEXT")
            conn.commit()
            print("Successfully added class_table column to students table")
        else:
            print("class_table column already exists in students table")
            
    except sqlite3.Error as e:
        print(f"Error adding class_table column: {e}")
    finally:
        conn.close()

def add_session_id_column_to_attendances(db_path='attendance.db'):
    """
    Add the session_id column to the attendances table if it doesn't exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(attendances)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'session_id' not in columns:
            # Add the session_id column
            cursor.execute("ALTER TABLE attendances ADD COLUMN session_id INTEGER")
            cursor.execute("ALTER TABLE attendances ADD FOREIGN KEY (session_id) REFERENCES attendance_sessions (id)")
            conn.commit()
            print("Successfully added session_id column to attendances table")
        else:
            print("session_id column already exists in attendances table")
            
    except sqlite3.Error as e:
        print(f"Error adding session_id column: {e}")
    finally:
        conn.close()

def add_class_table_column_to_sessions(db_path='attendance.db'):
    """
    Add the class_table column to the attendance_sessions table if it doesn't exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(attendance_sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'class_table' not in columns:
            # Add the class_table column
            cursor.execute("ALTER TABLE attendance_sessions ADD COLUMN class_table TEXT")
            conn.commit()
            print("Successfully added class_table column to attendance_sessions table")
        else:
            print("class_table column already exists in attendance_sessions table")
            
    except sqlite3.Error as e:
        print(f"Error adding class_table column: {e}")
    finally:
        conn.close()

def fix_database_columns(db_path='attendance.db'):
    """
    Fix all missing columns in the attendance database.
    """
    print("Checking and fixing database columns...")
    add_class_table_column_to_students(db_path)
    add_session_id_column_to_attendances(db_path)
    add_class_table_column_to_sessions(db_path)
    print("Database column fixes completed!")

# Legacy functions for backward compatibility (now redirect to new functions)
def create_class_table(table_name, columns, db_path='classes.db'):
    """Create a table for a specific class in classes.db"""
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

def insert_students(table_name, students, db_path='classes.db'):
    """Insert students into a specific class table in classes.db"""
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
    # Run this to add the missing columns
    fix_database_columns()