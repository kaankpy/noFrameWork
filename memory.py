import sqlite3
import json
from config import DB_PATH

def init_db():
    # Input: None
    # Purpose:
    #   SQLite veya benzeri bir veritabanı başlatır.
    # Output:
    #   None
    #pass
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        content TEXT,
        meta TEXT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS tool_outputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tool_name TEXT,
        output TEXT,
        meta TEXT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def save_message(role: str, content: str, meta: dict = None):
    # Input:
    #   role (str) - "user" veya "assistant"
    #   content (str) - Mesaj içeriği
    #   meta (dict) - Ek meta veri
    # Purpose:
    #   Mesajı veritabanına kaydeder.
    # Output:
    #   None
    #pass
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (role, content, meta) VALUES (?, ?, ?)",
                (role, content, json.dumps(meta or {})))
    conn.commit(); conn.close()

def save_tool_output(tool_name: str, output, meta: dict = None):
    # Input:
    #   tool_name (str) - Tool adı
    #   output (any) - Tool çıktısı
    #   meta (dict) - Ek meta veri
    # Purpose:
    #   Tool çıktısını veritabanına kaydeder.
    # Output:
    #   None
    pass