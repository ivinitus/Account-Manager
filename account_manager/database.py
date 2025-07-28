import os
import sys
import sqlite3
import queue
from contextlib import contextmanager

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "accounts.db")


class ConnectionPool:
    """A very small SQLite connection-pool for threaded applications."""

    def __init__(self, database_path: str, max_connections: int = 10):
        self.database_path = database_path
        self.pool: "queue.Queue[sqlite3.Connection]" = queue.Queue(
            maxsize=max_connections
        )
        self.max_connections = max_connections
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        for _ in range(self.max_connections):
            conn = sqlite3.connect(self.database_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            self.pool.put(conn)

    @contextmanager
    def get_connection(self):
        """Context manager that yields a DB connection from the pool."""
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)

db_pool = ConnectionPool(DB_PATH)


def init_db() -> None:
    """Initialize tables & indexes if they do not yet exist."""
    with db_pool.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                customer_id TEXT PRIMARY KEY,
                email TEXT,
                password TEXT,
                marketplace TEXT,
                type TEXT,
                date TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS last_used (
                id INTEGER PRIMARY KEY,
                customer_id TEXT,
                email TEXT,
                password TEXT,
                marketplace TEXT,
                type TEXT,
                date TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_accounts_marketplace_type
            ON accounts (marketplace, type)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_accounts_type_date
            ON accounts (type, date)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_last_used_id
            ON last_used (id DESC)
        """
        )

        conn.commit()