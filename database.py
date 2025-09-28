import sqlite3
import hashlib
import os
from datetime import datetime

# -------------------- DATABASE SETUP --------------------
DB_FILE = "users.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def create_tables():
    """Create users, quiz_results, badges tables."""
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
            total INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Badges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge TEXT NOT NULL,
            awarded_on TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

create_tables()

# -------------------- HASHING --------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------- USER FUNCTIONS --------------------
def create_user(name: str, email: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)", (name,email,hashed_pw))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"id": user_id, "name": name, "email": email}
    except sqlite3.IntegrityError:
        conn.close()
        return None

def authenticate(name: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)
    cursor.execute("SELECT id,name,email FROM users WHERE name=? AND password=?", (name,hashed_pw))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "name": user[1], "email": user[2]}
    return None

# -------------------- QUIZ RESULTS --------------------
def save_quiz_result(user_id: int, score: int, total: int):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO quiz_results (user_id,score,total,timestamp) VALUES (?,?,?,?)", (user_id,score,total,timestamp))
    conn.commit()
    conn.close()

def get_quiz_results(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT score,total,timestamp FROM quiz_results WHERE user_id=? ORDER BY timestamp", (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

# -------------------- BADGES --------------------
def award_badge(user_id: int, badge: str):
    conn = get_connection()
    cursor = conn.cursor()
    awarded_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO badges (user_id,badge,awarded_on) VALUES (?,?,?)", (user_id,badge,awarded_on))
    conn.commit()
    conn.close()

def get_badges(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT badge,awarded_on FROM badges WHERE user_id=? ORDER BY awarded_on", (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results
