"""Data layer: the only place that contains SQL.

Every query uses `?` placeholders (parameterized queries), which protects
against SQL injection.
"""
from .db import get_db


def list_tasks(newest_first=False):
    query = "SELECT * FROM tasks ORDER BY id DESC" if newest_first else "SELECT * FROM tasks ORDER BY id ASC"
    return [dict(row) for row in get_db().execute(query).fetchall()]


def create_task(title):
    db = get_db()
    cur = db.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
    db.commit()
    return {"id": cur.lastrowid, "title": title, "done": 0}


def update_task(task_id, title):
    """Rename a task. Returns True if the task existed."""
    db = get_db()
    cur = db.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
    db.commit()
    return cur.rowcount > 0


def toggle_task(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,))
    db.commit()


def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
