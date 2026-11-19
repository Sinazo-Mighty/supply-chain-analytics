-- Analysis queries for the DataCo supply chain project.
-- Written in standard SQL that runs on both PostgreSQL (Supabase) and DuckDB.
-- Convention: "delivered" lines exclude delivery_status = 'Shipping canceled',
-- because a cancelled shipment can't be on time or late.

-- name: q1_delivery_by_shipping_mode
-- Business question: Which shipping modes miss their promised delivery times?
SELECT
    shipping_mode,
    MAX(scheduled_ship_days)                         AS promised_days,
    ROUND(AVG(actual_ship_days), 2)                  AS avg_actual_days,
    COUNT(*)                                         AS order_lines,
    ROUND(100.0 * AVG(is_late), 1)                   AS pct_late
FROM fact_order_item
WHERE delivery_status <> 'Shipping canceled'
GROUP BY shipping_mode
ORDER BY pct_late DESC;

-- name: q2_profit_leaks_by_department
-- Business question: Where are we losing money, and how much?
SELECT
    p.department_name,
    COUNT(*)                                                    AS order_lines,
    ROUND(100.0 * AVG(CASE WHEN f.profit < 0 THEN 1 ELSE 0 END), 1) AS pct_loss_making,
    ROUND(SUM(CASE WHEN f.profit < 0 THEN f.profit ELSE 0 END), 0)  AS total_losses,
    ROUND(SUM(f.profit), 0)                                     AS net_profit
FROM fact_order_item f
JOIN dim_product p ON p.product_card_id = f.product_card_id
GROUP BY p.department_name
ORDER BY total_losses ASC;

-- name: q3_monthly_trend
-- Business question: How are sales, profit and lateness trending over time?
-- Uses CTE + window functions (3-month moving average, month-on-month change).
WITH monthly AS (
    SELECT
        d.year,
        d.month,
        ROUND(SUM(f.sales), 0)                        AS sales,
        ROUND(SUM(f.profit), 0)                       AS profit,
        ROUND(100.0 * AVG(f.is_late), 1)              AS pct_late
    FROM fact_order_item f
    JOIN dim_date d ON d.date_key = f.order_date_key
    WHERE f.delivery_status <> 'Shipping canceled'
    GROUP BY d.year, d.month
)
SELECT
    year, month, sales, profit, pct_late,
    ROUND(AVG(sales) OVER (ORDER BY year, month
                           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0) AS sales_3m_avg,
    ROUND(100.0 * (sales - LAG(sales) OVER (ORDER BY year, month))
          / NULLIF(LAG(sales) OVER (ORDER BY year, month), 0), 1)        AS sales_mom_pct
FROM monthly
ORDER BY year, month;

-- name: q4_markets_and_regions
-- Business question: Does geography explain late deliveries or profit?
SELECT
    l.market,
    COUNT(*)                                     AS order_lines,
    ROUND(SUM(f.sales), 0)                       AS sales,
    ROUND(SUM(f.profit), 0)                      AS profit,
    ROUND(100.0 * AVG(f.is_late), 1)             AS pct_late
FROM fact_order_item f
JOIN dim_location l ON l.location_key = f.location_key
WHERE f.delivery_status <> 'Shipping canceled'
GROUP BY l.market
ORDER BY sales DESC;

-- name: q5_discount_bands
-- Business question: Do bigger discounts cost us profit?
SELECT
    CASE
        WHEN discount_rate = 0     THEN '0%'
        WHEN discount_rate < 0.10  THEN '1-9%'
        WHEN discount_rate < 0.20  THEN '10-19%'
        ELSE '20%+'
    END                                          AS discount_band,
    COUNT(*)                                     AS order_lines,
    ROUND(AVG(profit_ratio), 3)                  AS avg_profit_ratio,
    ROUND(100.0 * AVG(CASE WHEN profit < 0 THEN 1 ELSE 0 END), 1) AS pct_loss_making
FROM fact_order_item
GROUP BY 1
ORDER BY MIN(discount_rate);

-- name: q6_top_and_bottom_products
-- Business question: Which products make and lose the most money?
-- Uses RANK() window functions to pull the top 5 and bottom 5.
WITH product_profit AS (
    SELECT
        p.product_name,
        p.category_name,
        ROUND(SUM(f.profit), 0) AS net_profit,
        RANK() OVER (ORDER BY SUM(f.profit) DESC) AS rank_best,
        RANK() OVER (ORDER BY SUM(f.profit) ASC)  AS rank_worst
    FROM fact_order_item f
    JOIN dim_product p ON p.product_card_id = f.product_card_id
    GROUP BY p.product_name, p.category_name
)
SELECT product_name, category_name, net_profit,
       CASE WHEN rank_best <= 5 THEN 'top 5' ELSE 'bottom 5' END AS group_label
FROM product_profit
WHERE rank_best <= 5 OR rank_worst <= 5
ORDER BY net_profit DESC;
