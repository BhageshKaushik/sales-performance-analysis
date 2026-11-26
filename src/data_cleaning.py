"""
data_cleaning.py — SQL-based Data Cleaning Pipeline
Sales Performance Analysis System

Executes all cleaning queries against SQLite, reports audit results,
and returns cleaning documentation.
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANING_SQL = PROJECT_ROOT / "sql" / "cleaning.sql"


def audit_null_counts(conn: sqlite3.Connection, table: str) -> dict:
    """
    Count NULL values in every column of the given table.

    Args:
        conn: Active SQLite connection.
        table: Table name to audit.

    Returns:
        dict mapping column_name -> null_count.
    """
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if not columns:
        return {}

    null_cases = ", ".join(
        f"SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) AS null_{col}"
        for col in columns
    )
    sql = f"SELECT {null_cases} FROM {table}"
    row = conn.execute(sql).fetchone()
    return dict(zip([f"null_{c}" for c in columns], row))


def detect_duplicates(conn: sqlite3.Connection) -> dict:
    """
    Detect duplicate rows in each table.

    Returns:
        dict with duplicate counts per table.
    """
    results = {}

    # Orders: duplicates by order_id + product_id + quantity
    df = pd.read_sql_query(
        """
        SELECT order_id, product_id, quantity, COUNT(*) AS cnt
        FROM orders
        GROUP BY order_id, product_id, quantity
        HAVING COUNT(*) > 1
        """,
        conn,
    )
    results["orders_duplicates"] = len(df)
    if len(df) > 0:
        logger.warning("Orders duplicates found: %d", len(df))

    # Returns: duplicates by order_id
    df_r = pd.read_sql_query(
        """
        SELECT order_id, COUNT(*) AS cnt
        FROM returns
        GROUP BY order_id
        HAVING COUNT(*) > 1
        """,
        conn,
    )
    results["returns_duplicates"] = len(df_r)

    # People: duplicates by person + region
    df_p = pd.read_sql_query(
        """
        SELECT person, region, COUNT(*) AS cnt
        FROM people
        GROUP BY person, region
        HAVING COUNT(*) > 1
        """,
        conn,
    )
    results["people_duplicates"] = len(df_p)

    return results


def compare_ship_mode(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Compare raw ship_mode against TRIM(UPPER()) corrected version.

    Returns:
        DataFrame with original, corrected values and correction flag.
    """
    df = pd.read_sql_query(
        """
        SELECT
            ship_mode                   AS ship_mode_original,
            TRIM(UPPER(ship_mode))      AS ship_mode_corrected,
            CASE
                WHEN TRIM(UPPER(ship_mode)) != UPPER(ship_mode)
                THEN 'Corrected'
                ELSE 'No Change'
            END AS correction_status,
            COUNT(*) AS row_count
        FROM orders
        GROUP BY ship_mode
        ORDER BY ship_mode
        """,
        conn,
    )
    return df


def report_data_quality(conn: sqlite3.Connection) -> dict:
    """
    Run full data quality audit across all three tables.

    Returns:
        dict with comprehensive quality report.
    """
    report = {}

    for table in ["orders", "returns", "people"]:
        try:
            null_counts = audit_null_counts(conn, table)
            total_nulls = sum(null_counts.values())
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            report[table] = {
                "row_count": row_count,
                "total_nulls": total_nulls,
                "null_by_column": null_counts,
            }
            logger.info(
                "Table '%s': %d rows, %d total NULLs", table, row_count, total_nulls
            )
            if total_nulls > 0:
                for col, cnt in null_counts.items():
                    if cnt > 0:
                        logger.warning("  %s.%s: %d NULLs", table, col, cnt)
        except Exception as exc:
            logger.error("Error auditing table '%s': %s", table, exc)
            report[table] = {"error": str(exc)}

    # Duplicates
    report["duplicates"] = detect_duplicates(conn)

    # Ship mode comparison
    ship_df = compare_ship_mode(conn)
    report["ship_mode_standardization"] = ship_df.to_dict(orient="records")

    return report


def run_cleaning_pipeline(conn: sqlite3.Connection) -> dict:
    """
    Main cleaning entry point. Runs quality audit and returns cleaning log.

    Cleaning decisions documented:
    1. NULLs in text columns (city, state, etc.): retained as-is since SQLite
       LEFT JOINs may produce NULLs that are semantically meaningful.
    2. Numeric columns (sales, quantity, discount, profit): cast to REAL/INTEGER
       in the analytical SQL query.
    3. Dates (order_date, ship_date): stored as TEXT in ISO format; Python
       layer converts to datetime64 for duration calculations.
    4. Ship mode: standardized via TRIM(UPPER()) in the analytical query.
    5. Duplicates in Orders: if detected, they are reported but NOT deleted —
       the analyst reviews before removal to avoid accidental data loss.
    6. Profit margins: negative margins are intentionally preserved (legitimate
       business data showing losses on heavily discounted items).

    Args:
        conn: Active SQLite connection.

    Returns:
        dict with the full cleaning audit report.
    """
    logger.info("=" * 60)
    logger.info("Running Data Cleaning Pipeline")
    logger.info("=" * 60)

    report = report_data_quality(conn)

    # Log cleaning summary
    for table in ["orders", "returns", "people"]:
        info = report.get(table, {})
        logger.info(
            "Table %-10s | Rows: %6d | NULLs: %4d",
            table,
            info.get("row_count", 0),
            info.get("total_nulls", 0),
        )

    dup_info = report.get("duplicates", {})
    logger.info("Duplicate Summary: Orders=%d, Returns=%d, People=%d",
                dup_info.get("orders_duplicates", 0),
                dup_info.get("returns_duplicates", 0),
                dup_info.get("people_duplicates", 0))

    return report
