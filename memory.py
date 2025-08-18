import sqlite3
import json
from config import DB_PATH

def init_db():
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
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (role, content, meta) VALUES (?, ?, ?)",
                (role, content, json.dumps(meta or {})))
    conn.commit(); conn.close()

def save_tool_output(tool_name: str, output, meta: dict = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO tool_outputs (tool_name, output, meta) VALUES (?, ?, ?)",
                (tool_name, json.dumps(output), json.dumps(meta or {})))
    conn.commit()
    conn.close()