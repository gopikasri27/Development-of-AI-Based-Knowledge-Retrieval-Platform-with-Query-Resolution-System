import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "rag_metadata.db")


def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite metadata database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT,
        file_size INTEGER,
        chunks_count INTEGER DEFAULT 0,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Chat sessions and messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        query_type TEXT,
        sources_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()


def save_document_record(filename: str, file_path: str, file_type: str, file_size: int, chunks_count: int):
    """Inserts or updates a document metadata record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO documents (filename, file_path, file_type, file_size, chunks_count, uploaded_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(filename) DO UPDATE SET
        file_path = excluded.file_path,
        file_type = excluded.file_type,
        file_size = excluded.file_size,
        chunks_count = excluded.chunks_count,
        uploaded_at = CURRENT_TIMESTAMP
    """, (filename, file_path, file_type, file_size, chunks_count))
    conn.commit()
    conn.close()


def get_all_documents() -> List[Dict[str, Any]]:
    """Retrieves all indexed document records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    docs = [dict(row) for row in rows]
    conn.close()
    return docs


def save_chat_message(
    session_id: str,
    role: str,
    message: str,
    query_type: Optional[str] = None,
    sources: Optional[List[Dict[str, Any]]] = None
):
    """Saves a single turn of chat message to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sources_json = json.dumps(sources) if sources else None
    cursor.execute("""
    INSERT INTO chat_history (session_id, role, message, query_type, sources_json)
    VALUES (?, ?, ?, ?, ?)
    """, (session_id, role, message, query_type, sources_json))
    conn.commit()
    conn.close()


def get_recent_history(session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieves the most recent chat history for a session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT role, message, query_type, sources_json, created_at
    FROM chat_history
    WHERE session_id = ?
    ORDER BY id DESC
    LIMIT ?
    """, (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    # Reverse so they are in chronological order
    for row in reversed(rows):
        item = dict(row)
        if item["sources_json"]:
            try:
                item["sources"] = json.loads(item["sources_json"])
            except Exception:
                item["sources"] = []
        else:
            item["sources"] = []
        del item["sources_json"]
        history.append(item)
        
    return history


# Automatically ensure DB is initialized on module import
init_db()
