import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "tasks.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            assignee TEXT,
            created TEXT,
            completed TEXT,
            deadline TEXT,
            days INTEGER,
            is_bug INTEGER DEFAULT 0,
            description TEXT,
            complexity TEXT DEFAULT '',
            reason TEXT DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()

def save_tasks(tasks: list):
    conn = get_conn()
    for t in tasks:
        conn.execute("""
            INSERT INTO tasks (id, title, author, assignee, created, completed,
                             deadline, days, is_bug, description, complexity, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                author=excluded.author,
                assignee=excluded.assignee,
                created=excluded.created,
                completed=excluded.completed,
                deadline=excluded.deadline,
                days=excluded.days,
                is_bug=excluded.is_bug,
                description=excluded.description
        """, (
            t.id, t.title, t.author, t.assignee,
            t.created, t.completed, t.deadline, t.days,
            1 if t.is_bug else 0, t.description,
            t.complexity or '', t.reason or ''
        ))
    conn.commit()
    conn.close()

def get_all_tasks() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM tasks ORDER BY completed DESC NULLS LAST").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_complexity(task_id: str, complexity: str, reason: str):
    conn = get_conn()
    conn.execute(
        "UPDATE tasks SET complexity=?, reason=? WHERE id=?",
        (complexity, reason, task_id)
    )
    conn.commit()
    conn.close()

def get_stats() -> dict:
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    conn.close()
    return {"total": total}
