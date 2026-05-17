import sqlite3

def init_db():
    conn = sqlite3.connect("sentiment.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sentiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        sentiment TEXT,
        score REAL
    )
    """)

    conn.commit()
    conn.close()


def insert_data(text, sentiment, score):
    conn = sqlite3.connect("sentiment.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO sentiments (text, sentiment, score)
    VALUES (?, ?, ?)
    """, (text, sentiment, score))

    conn.commit()
    conn.close()


def fetch_all():
    conn = sqlite3.connect("sentiment.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sentiments")
    data = cursor.fetchall()

    conn.close()
    return data