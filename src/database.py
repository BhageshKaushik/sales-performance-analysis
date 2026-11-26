"""
database.py — SQLite Database Connection and Schema Management
Sales Performance Analysis System
"""

import sqlite3
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "sales.db"
SCHEMA_SQL = PROJECT_ROOT / "sql" / "schema.sql"
ANALYSIS_SQL = PROJECT_ROOT / "sql" / "analysis.sql"


def connect_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """
    Create and return a connection to the SQLite database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        sqlite3.Connection object with row_factory set to Row.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    logger.info("Connected to database: %s", db_path)
    return conn


def execute_schema(conn: sqlite3.Connection) -> None:
    """
    Execute the SQL schema file to create (or recreate) tables.

    Args:
        conn: Active SQLite connection.
    """
    if not SCHEMA_SQL.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_SQL}")

    sql_text = SCHEMA_SQL.read_text(encoding="utf-8")
    # Execute each statement separately (SQLite doesn't support executescript in WAL mode cleanly)
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    for stmt in statements:
        conn.execute(stmt)
    conn.commit()
    logger.info("Schema executed successfully.")


def get_table_row_count(conn: sqlite3.Connection, table: str) -> int:
    """Return the number of rows in the given table."""
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]


def get_analytical_dataset(conn: sqlite3.Connection):
    """
    Execute the master analytical JOIN query and return a pandas DataFrame.

    Args:
        conn: Active SQLite connection.

    Returns:
        pandas.DataFrame with the full analytical dataset.
    """
    import pandas as pd

    if not ANALYSIS_SQL.exists():
        raise FileNotFoundError(f"Analysis SQL not found: {ANALYSIS_SQL}")

    sql_text = ANALYSIS_SQL.read_text(encoding="utf-8")
    df = pd.read_sql_query(sql_text, conn)
    logger.info("Analytical dataset loaded: %d rows, %d columns", len(df), len(df.columns))
    return df


def close_db(conn: sqlite3.Connection) -> None:
    """Safely close the database connection."""
    try:
        conn.close()
        logger.info("Database connection closed.")
    except Exception as exc:
        logger.warning("Error closing database: %s", exc)
