-- =====================================================================
-- Olist Brazilian E-Commerce Analytics
-- Step 4: SQL Business Analysis Queries
-- Database: Olist_Ecommerce (Server: .\SQLEXPRESS)
-- =====================================================================

USE Olist_Ecommerce;
GO

-- =====================================================================
-- QUERY 1: Total Orders, Delivered Orders, and Order Status Breakdown
-- Business Purpose:
--   Measure total platform order volume, determine overall delivery
--   fulfillment success rate, and inspect the operational pipeline.
-- =====================================================================

-- Part A: High-Level Summary (Totals & Delivered Percentage)
SELECT 
    COUNT(*) AS total_orders,
    COUNT(CASE WHEN order_status = 'delivered' THEN 1 END) AS delivered_orders,
    ROUND(
        100.0 * COUNT(CASE WHEN order_status = 'delivered' THEN 1 END) / COUNT(*), 
        2
    ) AS delivered_percentage
FROM orders;

-- Part B: Breakdown by Order Status
SELECT 
    order_status,
    COUNT(*) AS order_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS percentage_of_total
FROM orders
GROUP BY order_status
ORDER BY order_count DESC;
GO


-- =====================================================================
-- QUERY 2: Total Product Revenue and Freight Charges
-- Business Purpose:
--   Quantify product merchandise value (GMV) vs. shipping charges (freight)
--   for all orders placed versus successfully delivered orders.
-- =====================================================================

SELECT 
    'All Orders' AS order_scope,
    COUNT(DISTINCT oi.order_id) AS orders_count,
    COUNT(oi.order_item_id) AS total_items_sold,
    SUM(oi.price) AS total_item_revenue,
    SUM(oi.freight_value) AS total_freight_value,
    SUM(oi.price + oi.freight_value) AS total_order_value,
    ROUND(
        100.0 * SUM(oi.freight_value) / SUM(oi.price + oi.freight_value), 
        2
    ) AS freight_percentage_of_total
FROM order_items oi

UNION ALL

SELECT 
    'Delivered Orders Only' AS order_scope,
    COUNT(DISTINCT oi.order_id) AS orders_count,
    COUNT(oi.order_item_id) AS total_items_sold,
    SUM(oi.price) AS total_item_revenue,
    SUM(oi.freight_value) AS total_freight_value,
    SUM(oi.price + oi.freight_value) AS total_order_value,
    ROUND(
        100.0 * SUM(oi.freight_value) / SUM(oi.price + oi.freight_value), 
        2
    ) AS freight_percentage_of_total
FROM order_items oi
INNER JOIN orders o 
    ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered';
GO


-- =====================================================================
-- QUERY 3: Monthly Revenue and Order Volume Trends
-- Business Purpose:
--   Track platform growth, sales seasonality, and Average Order Value (AOV)
--   month over month across all delivered orders.
-- =====================================================================

SELECT 
    FORMAT(o.order_purchase_timestamp, 'yyyy-MM') AS order_year_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(oi.order_item_id) AS total_items_sold,
    SUM(oi.price) AS total_product_revenue,
    SUM(oi.freight_value) AS total_freight_value,
    SUM(oi.price + oi.freight_value) AS total_order_value,
    ROUND(
        SUM(oi.price + oi.freight_value) / COUNT(DISTINCT o.order_id), 
        2
    ) AS average_order_value
FROM orders o
INNER JOIN order_items oi 
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY FORMAT(o.order_purchase_timestamp, 'yyyy-MM')
ORDER BY order_year_month;
GO


-- =====================================================================
-- QUERY 4: Top 10 Product Categories by Revenue
-- Business Purpose:
--   Identify the top-selling categories by realized product revenue,
--   measuring units sold, average item price, and revenue share.
-- =====================================================================

SELECT TOP 10
    COALESCE(ct.product_category_name_english, p.product_category_name, 'Unknown') AS category_name,
    COUNT(oi.order_item_id) AS items_sold,
    COUNT(DISTINCT oi.order_id) AS orders_count,
    SUM(oi.price) AS total_product_revenue,
    ROUND(AVG(oi.price), 2) AS average_item_price,
    ROUND(
        100.0 * SUM(oi.price) / SUM(SUM(oi.price)) OVER(), 
        2
    ) AS percentage_of_total_revenue
FROM order_items oi
INNER JOIN orders o 
    ON oi.order_id = o.order_id
INNER JOIN products p 
    ON oi.product_id = p.product_id
LEFT JOIN category_translation ct 
    ON p.product_category_name = ct.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY COALESCE(ct.product_category_name_english, p.product_category_name, 'Unknown')
ORDER BY total_product_revenue DESC;
GO


-- =====================================================================
-- QUERY 5: Unique vs. Repeat Customer Dynamics
-- Business Purpose:
--   Identify individual buyers using customer_unique_id, measure
--   one-time vs. repeat purchasing rates, and inspect order frequency.
-- =====================================================================

-- Part A: Customer Summary (One-Time vs. Repeat)
WITH CustomerOrderCounts AS (
    SELECT 
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS total_orders_placed
    FROM olist_customers_dataset c
    INNER JOIN orders o 
        ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT 
    COUNT(*) AS total_unique_customers,
    COUNT(CASE WHEN total_orders_placed = 1 THEN 1 END) AS one_time_customers,
    COUNT(CASE WHEN total_orders_placed > 1 THEN 1 END) AS repeat_customers,
    ROUND(
        100.0 * COUNT(CASE WHEN total_orders_placed = 1 THEN 1 END) / COUNT(*), 
        2
    ) AS one_time_percentage,
    ROUND(
        100.0 * COUNT(CASE WHEN total_orders_placed > 1 THEN 1 END) / COUNT(*), 
        2
    ) AS repeat_percentage
FROM CustomerOrderCounts;

-- Part B: Order Frequency Distribution
WITH CustomerOrderCounts AS (
    SELECT 
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS orders_count
    FROM olist_customers_dataset c
    INNER JOIN orders o 
        ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT 
    orders_count,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS percentage_of_customers
FROM CustomerOrderCounts
GROUP BY orders_count
ORDER BY orders_count;
GO


-- =====================================================================
-- QUERY 6: Payment Method Breakdown and Credit Card Installments
-- Business Purpose:
--   Evaluate payment preferences, transaction counts, total monetary volume,
--   average transaction values, and credit card installment usage.
-- =====================================================================

-- Part A: Payment Method Performance
SELECT 
    payment_type,
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT order_id) AS distinct_orders_count,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 
        2
    ) AS percentage_of_transactions,
    SUM(payment_value) AS total_payment_value,
    ROUND(
        100.0 * SUM(payment_value) / SUM(SUM(payment_value)) OVER(), 
        2
    ) AS percentage_of_total_value,
    ROUND(AVG(payment_value), 2) AS avg_payment_transaction_value,
    ROUND(AVG(CAST(payment_installments AS FLOAT)), 2) AS avg_installments
FROM order_payments
WHERE payment_type <> 'not_defined'
GROUP BY payment_type
ORDER BY total_payment_value DESC;

-- Part B: Credit Card Installment Distribution
SELECT 
    payment_installments,
    COUNT(*) AS credit_card_transactions,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 
        2
    ) AS percentage_of_cc_transactions,
    SUM(payment_value) AS total_value,
    ROUND(AVG(payment_value), 2) AS avg_transaction_value
FROM order_payments
WHERE payment_type = 'credit_card'
GROUP BY payment_installments
ORDER BY payment_installments;
GO


-- =====================================================================
-- QUERY 7: Delivery Performance and Review Score Analysis
-- Business Purpose:
--   Assess on-time vs. late delivery rates (for delivered orders with
--   actual and estimated dates) and measure customer satisfaction impact.
-- =====================================================================

-- Step 1: Deduplicate reviews to get exactly one latest review per order
WITH DeduplicatedReviews AS (
    SELECT 
        order_id,
        review_score,
        ROW_NUMBER() OVER(
            PARTITION BY order_id 
            ORDER BY review_creation_date DESC, review_answer_timestamp DESC
        ) AS rn
    FROM order_reviews
),
LatestReview AS (
    SELECT 
        order_id,
        review_score
    FROM DeduplicatedReviews
    WHERE rn = 1
),
-- Step 2: Classify delivery performance for delivered orders
DeliveryClassification AS (
    SELECT 
        o.order_id,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        -- Calculate actual delivery time in days from purchase to delivery
        ROUND(
            CAST(DATEDIFF(second, o.order_purchase_timestamp, o.order_delivered_customer_date) AS FLOAT) / 86400.0, 
            2
        ) AS actual_delivery_days,
        -- Classify as On-Time or Late
        CASE 
            WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On-Time'
            ELSE 'Late'
        END AS delivery_status,
        r.review_score
    FROM orders o
    LEFT JOIN LatestReview r 
        ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
)
-- Step 3: Performance summary and review score association
SELECT 
    delivery_status,
    COUNT(*) AS total_orders,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 
        2
    ) AS percentage_of_delivered_orders,
    ROUND(AVG(actual_delivery_days), 2) AS avg_delivery_days,
    COUNT(review_score) AS reviewed_orders_count,
    ROUND(AVG(CAST(review_score AS FLOAT)), 2) AS avg_customer_satisfaction_score,
    ROUND(
        100.0 * COUNT(CASE WHEN review_score >= 4 THEN 1 END) / COUNT(review_score), 
        2
    ) AS positive_review_percentage,
    ROUND(
        100.0 * COUNT(CASE WHEN review_score <= 2 THEN 1 END) / COUNT(review_score), 
        2
    ) AS negative_review_percentage
FROM DeliveryClassification
GROUP BY delivery_status;
GO
