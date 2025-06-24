import sqlite3

db_path = 'classes.db'  # or your database file
table_name = 'Operating_Systems__Dr_Maria_Santos'  # replace with your table name

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
conn.commit()
conn.close()

print(f'Table "{table_name}" deleted from {db_path}.')