-- ============================================================
-- cleaning.sql — Data Cleaning Queries
-- Sales Performance Analysis System
-- ============================================================

-- ============================================================
-- 1. NULL Audit — Orders Table
-- ============================================================
SELECT
    SUM(CASE WHEN row_id IS NULL THEN 1 ELSE 0 END)       AS null_row_id,
    SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END)      AS null_order_id,
    SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END)    AS null_order_date,
    SUM(CASE WHEN ship_date IS NULL THEN 1 ELSE 0 END)     AS null_ship_date,
    SUM(CASE WHEN ship_mode IS NULL THEN 1 ELSE 0 END)     AS null_ship_mode,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END)   AS null_customer_id,
    SUM(CASE WHEN customer_name IS NULL THEN 1 ELSE 0 END) AS null_customer_name,
    SUM(CASE WHEN segment IS NULL THEN 1 ELSE 0 END)       AS null_segment,
    SUM(CASE WHEN country IS NULL THEN 1 ELSE 0 END)       AS null_country,
    SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END)          AS null_city,
    SUM(CASE WHEN state IS NULL THEN 1 ELSE 0 END)         AS null_state,
    SUM(CASE WHEN postal_code IS NULL THEN 1 ELSE 0 END)   AS null_postal_code,
    SUM(CASE WHEN region IS NULL THEN 1 ELSE 0 END)        AS null_region,
    SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END)    AS null_product_id,
    SUM(CASE WHEN category IS NULL THEN 1 ELSE 0 END)      AS null_category,
    SUM(CASE WHEN sub_category IS NULL THEN 1 ELSE 0 END)  AS null_sub_category,
    SUM(CASE WHEN product_name IS NULL THEN 1 ELSE 0 END)  AS null_product_name,
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END)         AS null_sales,
    SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END)      AS null_quantity,
    SUM(CASE WHEN discount IS NULL THEN 1 ELSE 0 END)      AS null_discount,
    SUM(CASE WHEN profit IS NULL THEN 1 ELSE 0 END)        AS null_profit
FROM orders;

-- ============================================================
-- 2. NULL Audit — Returns Table
-- ============================================================
SELECT
    SUM(CASE WHEN returned IS NULL THEN 1 ELSE 0 END)  AS null_returned,
    SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END)  AS null_order_id
FROM returns;

-- ============================================================
-- 3. NULL Audit — People Table
-- ============================================================
SELECT
    SUM(CASE WHEN person IS NULL THEN 1 ELSE 0 END)   AS null_person,
    SUM(CASE WHEN region IS NULL THEN 1 ELSE 0 END)   AS null_region
FROM people;

-- ============================================================
-- 4. Duplicate Detection — Orders (Order ID + Product ID + Quantity)
-- ============================================================
SELECT order_id, product_id, quantity, COUNT(*) AS duplicate_count
FROM orders
GROUP BY order_id, product_id, quantity
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- ============================================================
-- 5. Duplicate Detection — Returns
-- ============================================================
SELECT order_id, COUNT(*) AS duplicate_count
FROM returns
GROUP BY order_id
HAVING COUNT(*) > 1;

-- ============================================================
-- 6. Duplicate Detection — People
-- ============================================================
SELECT person, region, COUNT(*) AS duplicate_count
FROM people
GROUP BY person, region
HAVING COUNT(*) > 1;

-- ============================================================
-- 7. Ship Mode Comparison (Standardize Whitespace)
-- ============================================================
SELECT
    ship_mode                          AS ship_mode_original,
    TRIM(UPPER(ship_mode))             AS ship_mode_corrected,
    CASE WHEN TRIM(UPPER(ship_mode)) != UPPER(ship_mode)
         THEN 'Needs Correction'
         ELSE 'OK'
    END                                AS correction_needed
FROM orders
GROUP BY ship_mode;
