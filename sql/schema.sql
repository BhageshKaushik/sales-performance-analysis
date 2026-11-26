-- ============================================================
-- schema.sql — Sales Performance Analysis System
-- Creates Orders, Returns, and People tables in SQLite
-- ============================================================

-- Drop existing tables to allow re-runs
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS returns;
DROP TABLE IF EXISTS people;

-- ============================================================
-- Orders Table
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    row_id          INTEGER,
    order_id        TEXT,
    order_date      TEXT,
    ship_date       TEXT,
    ship_mode       TEXT,
    customer_id     TEXT,
    customer_name   TEXT,
    segment         TEXT,
    country         TEXT,
    city            TEXT,
    state           TEXT,
    postal_code     TEXT,
    region          TEXT,
    product_id      TEXT,
    category        TEXT,
    sub_category    TEXT,
    product_name    TEXT,
    sales           REAL,
    quantity        INTEGER,
    discount        REAL,
    profit          REAL
);

-- ============================================================
-- Returns Table
-- ============================================================
CREATE TABLE IF NOT EXISTS returns (
    returned        TEXT,
    order_id        TEXT
);

-- ============================================================
-- People Table
-- ============================================================
CREATE TABLE IF NOT EXISTS people (
    person          TEXT,
    region          TEXT
);
