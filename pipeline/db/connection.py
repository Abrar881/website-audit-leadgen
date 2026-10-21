import sqlite3
from pathlib import Path

_SCHEMA = Path(__file__).parent / "schema.sql"


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Return a WAL-mode SQLite connection with row factory."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Create tables if they don't exist and return connection."""
    conn = get_connection(db_path)
    schema = _SCHEMA.read_text()
    conn.executescript(schema)
    conn.commit()
    return conn
