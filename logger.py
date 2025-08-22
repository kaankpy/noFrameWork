import sqlite3
import json
import datetime
import os

DB_FILE = "data/application.db"
LOG_TABLE_NAME = "event_logs"

def _get_db_connection():
    """
    Establishes a connection to the SQLite database.
    Ensures the data directory exists.
    """
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_log_db():
    """Initializes the event_logs table in the database if it doesn't exist."""
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {LOG_TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            kind TEXT NOT NULL,
            payload TEXT NOT NULL
        )
        """)
        conn.commit()

def log_event(kind: str, payload: dict):
    """Logs an event to the database."""
    log_entry = (
        datetime.datetime.utcnow().isoformat(),
        kind,
        json.dumps(payload)
    )
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {LOG_TABLE_NAME} (timestamp, kind, payload) VALUES (?, ?, ?)",
            log_entry
        )
        conn.commit()