"""Database connection handling (no business queries here)."""
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT    NOT NULL,
    done  INTEGER NOT NULL DEFAULT 0
)
"""


def get_db():
    """Return the connection of the current request, opening it if needed."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row  # rows behave like dicts
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    """Create the table once at startup and close connections after each request."""
    conn = sqlite3.connect(app.config["DB_PATH"])
    conn.execute(SCHEMA)
    conn.commit()
    conn.close()
    app.teardown_appcontext(close_db)
