"""
sql_queries.py — Central Repository of Named SQL Query Strings
Sales Performance Analysis System

All SQL queries used by the analysis layer are defined here as module-level
constants for maintainability and easy review.
"""

# ============================================================
# Master Analytical Dataset
# ============================================================

MASTER_DATASET_QUERY = """
SELECT
    o.row_id,
    o.order_id,
    TRIM(o.order_date)                          AS order_date,
    TRIM(o.ship_date)                           AS ship_date,
    TRIM(UPPER(o.ship_mode))                    AS ship_mode,
    TRIM(o.customer_id)                         AS customer_id,
    TRIM(o.customer_name)                       AS customer_name,
    TRIM(UPPER(o.segment))                      AS segment,
    TRIM(UPPER(o.country))                      AS country,
    TRIM(o.city)                                AS city,
    TRIM(o.state)                               AS state,
    TRIM(o.postal_code)                         AS postal_code,
    TRIM(UPPER(o.region))                       AS region,
    TRIM(o.product_id)                          AS product_id,
    TRIM(UPPER(o.category))                     AS category,
    TRIM(o.sub_category)                        AS sub_category,
    TRIM(o.product_name)                        AS product_name,
    CAST(o.sales AS REAL)                       AS sales,
    CAST(o.quantity AS INTEGER)                 AS quantity,
    CAST(o.discount AS REAL)                    AS discount,
    CAST(o.profit AS REAL)                      AS profit,
    CASE WHEN TRIM(UPPER(r.returned)) = 'YES' THEN 1 ELSE 0 END AS is_returned,
    TRIM(p.person)                              AS sales_rep,
    CAST(SUBSTR(TRIM(o.order_date), 1, 4) AS INTEGER)   AS order_year,
    CAST(SUBSTR(TRIM(o.order_date), 6, 2) AS INTEGER)   AS order_month,
    CASE
        WHEN CAST(SUBSTR(TRIM(o.order_date), 6, 2) AS INTEGER) BETWEEN 1 AND 3  THEN 1
        WHEN CAST(SUBSTR(TRIM(o.order_date), 6, 2) AS INTEGER) BETWEEN 4 AND 6  THEN 2
        WHEN CAST(SUBSTR(TRIM(o.order_date), 6, 2) AS INTEGER) BETWEEN 7 AND 9  THEN 3
        ELSE 4
    END AS order_quarter,
    CASE
        WHEN CAST(o.quantity AS INTEGER) > 0
        THEN CAST(o.sales AS REAL) / CAST(o.quantity AS INTEGER)
        ELSE NULL
    END AS unit_price,
    CASE
        WHEN CAST(o.sales AS REAL) != 0
        THEN CAST(o.profit AS REAL) / CAST(o.sales AS REAL)
        ELSE NULL
    END AS profit_margin
FROM orders o
LEFT JOIN returns r
    ON TRIM(o.order_id) = TRIM(r.order_id)
LEFT JOIN people p
    ON TRIM(UPPER(o.region)) = TRIM(UPPER(p.region))
"""

# ============================================================
# Verification Queries
# ============================================================

VERIFY_TOTALS = """
SELECT
    COUNT(*)        AS total_rows,
    COUNT(DISTINCT order_id) AS unique_orders,
    SUM(CAST(sales AS REAL))    AS total_sales,
    SUM(CAST(quantity AS INTEGER)) AS total_quantity,
    SUM(CAST(profit AS REAL))   AS total_profit
FROM orders
"""

VERIFY_JOIN_COUNTS = """
SELECT
    COUNT(*) AS joined_rows,
    SUM(CASE WHEN r.order_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_returns,
    SUM(CASE WHEN p.person IS NOT NULL THEN 1 ELSE 0 END) AS matched_people
FROM orders o
LEFT JOIN returns r ON TRIM(o.order_id) = TRIM(r.order_id)
LEFT JOIN people p ON TRIM(UPPER(o.region)) = TRIM(UPPER(p.region))
"""

# ============================================================
# Geographic Queries
# ============================================================

SALES_BY_STATE = """
SELECT state, SUM(CAST(sales AS REAL)) AS total_sales,
       SUM(CAST(profit AS REAL)) AS total_profit
FROM orders
GROUP BY state
ORDER BY total_sales DESC
"""

SALES_BY_REGION = """
SELECT TRIM(UPPER(region)) AS region,
       SUM(CAST(sales AS REAL)) AS total_sales,
       SUM(CAST(profit AS REAL)) AS total_profit
FROM orders
GROUP BY TRIM(UPPER(region))
ORDER BY total_sales DESC
"""

# ============================================================
# NULL audit template (formatted with table name)
# ============================================================

NULL_AUDIT_TEMPLATE = "SELECT COUNT(*) FROM {table} WHERE {col} IS NULL"
