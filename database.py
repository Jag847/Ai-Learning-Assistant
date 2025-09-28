import sqlite3
import hashlib
import os

# -------------------- DATABASE SETUP --------------------
DB_FILE = "users.db"

def get_connection():
    """Connect to the SQLite database."""
    return sqlite3.connect(DB_FILE)

def create_tables():
    """Create users and quiz tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    # Quiz results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Run on import to ensure tables exist
create_tables()

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
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_pw)
        )
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

    cursor.execute(
        "SELECT id, name, email FROM users WHERE name=? AND password=?",
        (name, hashed_pw)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return {"id": user[0], "name": user[1], "email": user[2]}
    else:
        return None

# -------------------- QUIZ RESULTS --------------------
def save_quiz_result(user_id: int, score: int, total_questions: int):
    """Store a user's quiz result in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO quiz_results (user_id, score, total_questions) VALUES (?, ?, ?)",
        (user_id, score, total_questions)
    )
    conn.commit()
    conn.close()

def get_quiz_results(user_id: int):
    """Retrieve all quiz results for a specific user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT score, total_questions, timestamp FROM quiz_results WHERE user_id=? ORDER BY timestamp",
        (user_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return results

# -------------------- DEBUG UTILITY --------------------
if __name__ == "__main__":
    print("✅ Database initialized successfully!")
    # Optional: create a test user
    # print(create_user("testuser", "test@gmail.com", "12345"))
