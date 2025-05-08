import sqlite3

def init_db():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')
    
    connection.commit()
    connection.close()

if __name__ == '__main__':
    init_db()