"""
test_cleaning.py — Tests for Data Cleaning Module
Sales Performance Analysis System
"""

import sys
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data_cleaning import (
    audit_null_counts,
    detect_duplicates,
    compare_ship_mode,
    run_cleaning_pipeline,
)


@pytest.fixture
def populated_db():
    """
    Create an in-memory SQLite database populated with test data
    including intentional NULLs and duplicates.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE orders (
            row_id INTEGER, order_id TEXT, order_date TEXT, ship_date TEXT,
            ship_mode TEXT, customer_id TEXT, customer_name TEXT, segment TEXT,
            country TEXT, city TEXT, state TEXT, postal_code TEXT, region TEXT,
            product_id TEXT, category TEXT, sub_category TEXT, product_name TEXT,
            sales REAL, quantity INTEGER, discount REAL, profit REAL
        );
        CREATE TABLE returns (returned TEXT, order_id TEXT);
        CREATE TABLE people (person TEXT, region TEXT);

        INSERT INTO orders VALUES
            (1, 'CA-001', '2021-01-15', '2021-01-18', 'First Class',
             'CUS-001', 'Alice', 'Consumer', 'US', 'New York', 'New York',
             '10001', 'East', 'FUR-001', 'Furniture', 'Bookcases', 'Product A',
             261.96, 2, 0.0, 41.91),
            (2, 'CA-002', '2021-02-20', '2021-02-24', 'Standard Class',
             'CUS-002', 'Bob', 'Corporate', 'US', 'LA', 'California',
             '90001', 'West', 'OFF-001', 'Office Supplies', 'Art', 'Product B',
             14.62, 3, 0.1, -6.87),
            (3, 'CA-003', '2021-03-10', '2021-03-15', '  First Class  ',
             'CUS-003', NULL, 'Home Office', 'US', 'Chicago', 'Illinois',
             '60601', 'Central', 'TEC-001', 'Technology', 'Phones', 'Product C',
             907.15, 7, 0.2, 90.72),
            -- Duplicate: same order_id + product_id + quantity
            (4, 'CA-001', '2021-01-15', '2021-01-18', 'First Class',
             'CUS-001', 'Alice', 'Consumer', 'US', 'New York', 'New York',
             '10001', 'East', 'FUR-001', 'Furniture', 'Bookcases', 'Product A',
             261.96, 2, 0.0, 41.91);

        INSERT INTO returns VALUES ('Yes', 'CA-001'), ('Yes', 'CA-003');
        INSERT INTO people VALUES ('Anna', 'East'), ('Chuck', 'West'), ('Kelly', 'Central');
    """)
    yield conn
    conn.close()


class TestAuditNullCounts:
    def test_returns_dict(self, populated_db):
        result = audit_null_counts(populated_db, "orders")
        assert isinstance(result, dict)

    def test_detects_null_customer_name(self, populated_db):
        result = audit_null_counts(populated_db, "orders")
        assert result.get("null_customer_name", 0) == 1

    def test_no_nulls_in_returns(self, populated_db):
        result = audit_null_counts(populated_db, "returns")
        total = sum(result.values())
        assert total == 0

    def test_handles_empty_table(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE empty_table (col1 TEXT, col2 INTEGER)")
        conn.commit()
        result = audit_null_counts(conn, "empty_table")
        # SQLite SUM on an empty table returns None (NULL); treat None as 0
        assert all((v is None or v == 0) for v in result.values())
        conn.close()


class TestDetectDuplicates:
    def test_detects_order_duplicate(self, populated_db):
        result = detect_duplicates(populated_db)
        assert result["orders_duplicates"] >= 1

    def test_no_returns_duplicates(self, populated_db):
        result = detect_duplicates(populated_db)
        assert result["returns_duplicates"] == 0

    def test_no_people_duplicates(self, populated_db):
        result = detect_duplicates(populated_db)
        assert result["people_duplicates"] == 0

    def test_returns_dict_with_all_keys(self, populated_db):
        result = detect_duplicates(populated_db)
        assert "orders_duplicates" in result
        assert "returns_duplicates" in result
        assert "people_duplicates" in result


class TestCompareShipMode:
    def test_returns_dataframe(self, populated_db):
        result = compare_ship_mode(populated_db)
        assert isinstance(result, pd.DataFrame)

    def test_detects_whitespace_in_ship_mode(self, populated_db):
        result = compare_ship_mode(populated_db)
        corrected_rows = result[result["correction_status"] == "Corrected"]
        assert len(corrected_rows) >= 1


class TestRunCleaningPipeline:
    def test_returns_dict(self, populated_db):
        result = run_cleaning_pipeline(populated_db)
        assert isinstance(result, dict)

    def test_includes_all_tables(self, populated_db):
        result = run_cleaning_pipeline(populated_db)
        assert "orders" in result
        assert "returns" in result
        assert "people" in result

    def test_includes_duplicates_key(self, populated_db):
        result = run_cleaning_pipeline(populated_db)
        assert "duplicates" in result

    def test_row_counts_correct(self, populated_db):
        result = run_cleaning_pipeline(populated_db)
        assert result["orders"]["row_count"] == 4  # including duplicate
        assert result["returns"]["row_count"] == 2
        assert result["people"]["row_count"] == 3
