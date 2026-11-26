-- ============================================================
-- analysis.sql — Master Analytical JOIN Query
-- Sales Performance Analysis System
-- ============================================================

-- ============================================================
-- Master Analytical Dataset
-- Orders LEFT JOIN Returns LEFT JOIN People
-- Includes all derived columns required for analysis
-- ============================================================
SELECT
    -- Orders base columns (cleaned)
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

    -- Returns join: IsReturned flag
    CASE WHEN TRIM(UPPER(r.returned)) = 'YES' THEN 1 ELSE 0 END AS is_returned,

    -- People join: Sales Representative
    TRIM(p.person)                              AS sales_rep,

    -- Derived: Date components
    CAST(SUBSTR(TRIM(o.order_date), 1, 4) AS INTEGER)   AS order_year,
    CAST(SUBSTR(TRIM(o.order_date), 6, 2) AS INTEGER)   AS order_month,
    CASE
        WHEN CAST(SUBSTR(TRIM(o.order_date), 6, 2) AS INTEGER) BETWEEN 1 AND 3  THEN 1
        WHEN CAST(SUBSTR(TRIM(o.order_date), 6, 2) AS INTEGER) BETWEEN 4 AND 6  THEN 2
        WHEN CAST(SUBSTR(TRIM(o.order_date), 6, 2) AS INTEGER) BETWEEN 7 AND 9  THEN 3
        ELSE 4
    END                                                           AS order_quarter,

    -- Derived: Unit Price (guard against 0 quantity)
    CASE
        WHEN CAST(o.quantity AS INTEGER) > 0
        THEN CAST(o.sales AS REAL) / CAST(o.quantity AS INTEGER)
        ELSE NULL
    END                                                           AS unit_price,

    -- Derived: Profit Margin (guard against 0 sales)
    CASE
        WHEN CAST(o.sales AS REAL) != 0
        THEN CAST(o.profit AS REAL) / CAST(o.sales AS REAL)
        ELSE NULL
    END                                                           AS profit_margin,

    -- Derived: Shipping Duration in days
    -- SQLite doesn't have native date diff; we store dates as text YYYY-MM-DD
    -- The Python layer will compute numeric shipping duration
    TRIM(o.ship_date)                                             AS ship_date_raw,
    TRIM(o.order_date)                                            AS order_date_raw

FROM orders o
LEFT JOIN returns r
    ON TRIM(o.order_id) = TRIM(r.order_id)
LEFT JOIN people p
    ON TRIM(UPPER(o.region)) = TRIM(UPPER(p.region));
