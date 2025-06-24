import os
import sqlite3

# Settings
CLASSES_FOLDER = 'CLASSES'
CLASS_NAME = 'class1'  # Change this to your desired class name
TABLE_NAME = 'students'

# Ensure the CLASSES folder exists
os.makedirs(CLASSES_FOLDER, exist_ok=True)

# Path for the class-specific database
class_db_path = os.path.join(CLASSES_FOLDER, f'{CLASS_NAME}.db')

# Connect to the class database (creates it if it doesn't exist)
conn = sqlite3.connect(class_db_path)
cursor = conn.cursor()

# Create the students table
cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        student_name TEXT,
        year_level TEXT,
        course TEXT
    )
''')
conn.commit()
conn.close()

print(f"Created {CLASS_NAME}.db with a '{TABLE_NAME}' table inside the {CLASSES_FOLDER} folder.")