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
        CREATE TABLE IF NOT EXISTS assignees (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            func_group   TEXT DEFAULT '',
            support_line TEXT DEFAULT ''
        );
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
            reason TEXT DEFAULT '',
            project TEXT DEFAULT 'Евро'
        );
    """)
    conn.commit()

    # Миграция: добавить project если его нет (для старых БД)
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN project TEXT DEFAULT 'Евро'")
        conn.commit()
    except Exception:
        pass

    # Миграция: перенести func_group/support_line из tasks в assignees (если колонки ещё есть)
    try:
        rows = conn.execute(
            "SELECT assignee, func_group, support_line FROM tasks WHERE assignee != ''"
        ).fetchall()
        for row in rows:
            for name in [n.strip() for n in (row['assignee'] or '').split(',') if n.strip()]:
                conn.execute("""
                    INSERT INTO assignees (name, func_group, support_line) VALUES (?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        func_group   = CASE WHEN excluded.func_group   != '' THEN excluded.func_group   ELSE func_group   END,
                        support_line = CASE WHEN excluded.support_line != '' THEN excluded.support_line ELSE support_line END
                """, (name, row['func_group'] or '', row['support_line'] or ''))
        conn.commit()
    except Exception:
        pass

    # Удалить старые колонки из tasks (SQLite 3.35+)
    for col in ('func_group', 'support_line'):
        try:
            conn.execute(f"ALTER TABLE tasks DROP COLUMN {col}")
            conn.commit()
        except Exception:
            pass

    conn.close()

def save_tasks(tasks: list):
    conn = get_conn()

    # Шаг 1: upsert assignees
    for t in tasks:
        for name in [n.strip() for n in (t.assignee or '').split(',') if n.strip()]:
            conn.execute("""
                INSERT INTO assignees (name, func_group, support_line) VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    func_group   = CASE WHEN excluded.func_group   != '' THEN excluded.func_group   ELSE func_group   END,
                    support_line = CASE WHEN excluded.support_line != '' THEN excluded.support_line ELSE support_line END
            """, (name, t.func_group or '', t.support_line or ''))

    # Шаг 2: upsert tasks (без func_group/support_line)
    for t in tasks:
        conn.execute("""
            INSERT INTO tasks (id, title, author, assignee, created, completed,
                             deadline, days, is_bug, description, complexity, reason, project)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                author=excluded.author,
                assignee=excluded.assignee,
                created=excluded.created,
                completed=excluded.completed,
                deadline=excluded.deadline,
                days=excluded.days,
                is_bug=excluded.is_bug,
                description=excluded.description,
                project=excluded.project
        """, (
            t.id, t.title, t.author, t.assignee,
            t.created, t.completed, t.deadline, t.days,
            1 if t.is_bug else 0, t.description,
            t.complexity or '', t.reason or '', t.project or 'Евро',
        ))

    conn.commit()
    conn.close()

def clear_all_tasks():
    conn = get_conn()
    conn.execute("DELETE FROM tasks")
    conn.execute("DELETE FROM assignees")
    conn.commit()
    conn.close()

def get_all_tasks() -> list:
    conn = get_conn()
    tasks = [dict(r) for r in conn.execute(
        "SELECT * FROM tasks ORDER BY completed DESC NULLS LAST"
    ).fetchall()]
    assignees = {r['name']: dict(r) for r in conn.execute(
        "SELECT name, func_group, support_line FROM assignees"
    ).fetchall()}
    for t in tasks:
        first = (t.get('assignee') or '').split(',')[0].strip()
        a = assignees.get(first, {})
        t['func_group']   = a.get('func_group', '')
        t['support_line'] = a.get('support_line', '')
    conn.close()
    return tasks

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
    assignees = conn.execute("SELECT COUNT(*) FROM assignees").fetchone()[0]
    conn.close()
    return {"total": total, "assignees": assignees}
