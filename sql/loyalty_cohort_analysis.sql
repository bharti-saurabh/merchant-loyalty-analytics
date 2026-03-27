-- Customer Cohort Retention Analysis
-- Straive Strategic Analytics | Merchant Loyalty Analytics

WITH first_purchase AS (
    SELECT customer_id,
        DATE_TRUNC('month', MIN(txn_date)) AS cohort_month
    FROM fact_transactions
    WHERE status = 'POSTED'
    GROUP BY customer_id
),

customer_activity AS (
    SELECT t.customer_id,
        fp.cohort_month,
        DATE_TRUNC('month', t.txn_date) AS activity_month,
        DATEDIFF('month', fp.cohort_month, DATE_TRUNC('month', t.txn_date)) AS months_since_acquisition
    FROM fact_transactions t
    JOIN first_purchase fp ON t.customer_id = fp.customer_id
    WHERE t.status = 'POSTED'
    GROUP BY 1, 2, 3, 4
),

cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_customers
    FROM first_purchase
    GROUP BY cohort_month
)

SELECT
    ca.cohort_month,
    cs.cohort_customers,
    ca.months_since_acquisition,
    COUNT(DISTINCT ca.customer_id)                                           AS active_customers,
    COUNT(DISTINCT ca.customer_id) * 1.0 / cs.cohort_customers              AS retention_rate,
    SUM(t.amount)                                                            AS cohort_revenue,
    AVG(t.amount)                                                            AS avg_order_value,
    SUM(t.amount) / COUNT(DISTINCT ca.customer_id)                          AS revenue_per_active_customer
FROM customer_activity ca
JOIN cohort_size cs ON ca.cohort_month = cs.cohort_month
JOIN fact_transactions t ON ca.customer_id = t.customer_id
    AND DATE_TRUNC('month', t.txn_date) = ca.activity_month
    AND t.status = 'POSTED'
WHERE ca.cohort_month >= CURRENT_DATE - INTERVAL '24 months'
  AND ca.months_since_acquisition IN (0,1,2,3,5,8,11,17,23)
GROUP BY 1,2,3
ORDER BY ca.cohort_month, ca.months_since_acquisition
