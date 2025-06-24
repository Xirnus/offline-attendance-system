import sqlite3

# Path to your attendance database
db_path = 'attendance.db'

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add the session_id column if it doesn't exist
try:
    cursor.execute("ALTER TABLE attendances ADD COLUMN session_id INTEGER;")
    print("Added 'session_id' column to 'attendances' table.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("'session_id' column already exists.")
    else:
        print("Error:", e)

# Add the class_table column to attendance_sessions if it doesn't exist
try:
    cursor.execute("ALTER TABLE attendance_sessions ADD COLUMN class_table TEXT;")
    print("Added 'class_table' column to 'attendance_sessions' table.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("'class_table' column already exists.")
    else:
        print("Error:", e)

conn.commit()
conn.close()