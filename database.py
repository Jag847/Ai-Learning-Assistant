import sqlite3
import hashlib
import os

# -------------------- DATABASE SETUP --------------------
DB_FILE = "users.db"

def get_connection():
    """Connect to the SQLite database."""
    return sqlite3.connect(DB_FILE)

def create_table():
    """Create users table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Run on import to ensure table exists
create_table()

# -------------------- HASHING FUNCTION --------------------
def hash_password(password: str) -> str:
    """Return a SHA-256 hashed password."""
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------- USER CREATION --------------------
def create_user(name: str, email: str, password: str):
    """Create a new user if not already existing."""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)

    try:
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_pw))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"id": user_id, "name": name, "email": email}
    except sqlite3.IntegrityError:
        conn.close()
        return None

# -------------------- USER AUTHENTICATION --------------------
def authenticate(name: str, password: str):
    """Check if user credentials are correct."""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)

    cursor.execute("SELECT id, name, email FROM users WHERE name=? AND password=?", (name, hashed_pw))
    user = cursor.fetchone()
    conn.close()

    if user:
        return {"id": user[0], "name": user[1], "email": user[2]}
    else:
        return None

# -------------------- DEBUG UTILITY --------------------
if __name__ == "__main__":
    print("✅ Database initialized successfully!")
    # Optional: create a test user
    # print(create_user("testuser", "test@gmail.com", "12345"))
