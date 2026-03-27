-- Share of Wallet Estimation
-- Straive Strategic Analytics | Merchant Loyalty Analytics

WITH customer_total_card_spend AS (
    -- Estimate total card spend capacity from network data
    SELECT
        n.customer_id,
        SUM(n.total_card_spend_12m)                              AS network_total_spend,
        SUM(CASE WHEN n.mcc_category = :target_mcc_category
                 THEN n.total_card_spend_12m ELSE 0 END)         AS category_total_spend
    FROM dim_network_spend_estimates n   -- network-provided spend estimates by customer
    GROUP BY n.customer_id
),

merchant_spend AS (
    SELECT customer_id,
        SUM(amount)                                              AS merchant_spend_12m,
        COUNT(txn_id)                                           AS merchant_txn_count
    FROM fact_transactions
    WHERE txn_date >= CURRENT_DATE - INTERVAL '12 months'
      AND status = 'POSTED'
    GROUP BY customer_id
)

SELECT
    ms.customer_id,
    ms.merchant_spend_12m,
    ns.network_total_spend,
    ns.category_total_spend,
    ms.merchant_spend_12m / NULLIF(ns.network_total_spend, 0)    AS share_of_total_wallet,
    ms.merchant_spend_12m / NULLIF(ns.category_total_spend, 0)   AS share_of_category_wallet,
    ns.category_total_spend - ms.merchant_spend_12m              AS untapped_category_spend,
    CASE
        WHEN ms.merchant_spend_12m / NULLIF(ns.category_total_spend,0) >= 0.5
             THEN 'Primary — Retention Focus'
        WHEN ms.merchant_spend_12m / NULLIF(ns.category_total_spend,0) >= 0.2
             THEN 'Secondary — Growth Opportunity'
        ELSE 'Marginal — Acquisition Target'
    END                                                          AS wallet_tier
FROM merchant_spend ms
JOIN customer_total_card_spend ns ON ms.customer_id = ns.customer_id
ORDER BY untapped_category_spend DESC
