import json
from datetime import datetime, timezone

from backend.db.database import get_connection


def ensure_memory_table():
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                question TEXT,
                sql TEXT,
                insight TEXT,
                row_count INTEGER,
                created_at TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def remember_interaction(table_name, question, sql, insight, row_count):
    ensure_memory_table()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO _agent_memory (table_name, question, sql, insight, row_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                table_name,
                question,
                sql,
                insight,
                int(row_count),
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def recall_memory(table_name=None, limit=5):
    ensure_memory_table()
    conn = get_connection()
    try:
        if table_name:
            rows = conn.execute(
                """
                SELECT question, sql, insight, row_count, created_at
                FROM _agent_memory
                WHERE table_name = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (table_name, int(limit)),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT question, sql, insight, row_count, created_at
                FROM _agent_memory
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
    finally:
        conn.close()

    return [
        {
            "question": row[0],
            "sql": row[1],
            "insight": row[2],
            "row_count": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


def memory_to_text(memories):
    if not memories:
        return "No prior memory for this table."
    return json.dumps(memories, default=str, indent=2)
