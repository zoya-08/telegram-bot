import sqlite3

DB_FILE = "recipes.db"

def create_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            ingredients TEXT,
            instructions TEXT
    )
    """)
    conn.commit()
    conn.close()
    print("Файл базы данных успешно создан:", DB_FILE)

create_db()

