import sqlite3

def create_class_table(table_name, columns, db_path='classes.db'):
    """
    Create a new table for the class if it doesn't exist.
    :param table_name: Name of the table (string, sanitized, no .xlsx)
    :param columns: List of tuples: (column_name, column_type)
    :param db_path: Path to the database file (default: 'classes.db')
    """
    # Sanitize table name: replace spaces with underscores, remove dangerous characters
    table_name = table_name.replace(' ', '_')
    table_name = ''.join(c for c in table_name if c.isalnum() or c == '_')

    # Make student_id the PRIMARY KEY
    columns_sql = ', '.join([
        f"{col} {dtype}" + (" PRIMARY KEY" if col == "student_id" else "")
        for col, dtype in columns
    ])
    sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {columns_sql}
        )
    '''
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    conn.close()

def insert_students(table_name, students, db_path='classes.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for student in students:
        cursor.execute(f'''
            INSERT OR IGNORE INTO "{table_name}" (student_id, student_name, year_level, course)
            VALUES (?, ?, ?, ?)
        ''', (
            student.get('studentId', ''),
            student.get('studentName', ''),
            student.get('yearLevel', ''),
            student.get('course', '')
        ))
    conn.commit()
    conn.close()