import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE session_profiles ADD COLUMN organizer TEXT;")
    print("Column 'organizer' added.")
except Exception as e:
    print("Error or column may already exist:", e)
conn.commit()
conn.close()