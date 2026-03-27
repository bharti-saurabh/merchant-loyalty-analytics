"""
RFM Segmentation — Merchant Loyalty Analytics
Straive Strategic Analytics
"""
import pandas as pd
import numpy as np
from datetime import date
import logging

log = logging.getLogger(__name__)

RFM_SEGMENTS = {
    (5,5,5): "Champion",        (5,5,4): "Champion",
    (5,4,5): "Loyal",           (4,5,5): "Loyal",          (4,4,5): "Loyal",
    (5,3,4): "Potential",       (4,3,4): "Potential",
    (3,1,1): "At Risk",         (2,2,2): "At Risk",        (2,1,3): "At Risk",
    (1,1,1): "Lost",            (1,1,2): "Lost",            (1,2,1): "Lost",
}

def compute_rfm(df: pd.DataFrame, snapshot_date: date) -> pd.DataFrame:
    """Compute RFM scores from transaction-level data."""
    df["txn_date"] = pd.to_datetime(df["txn_date"])
    snap = pd.Timestamp(snapshot_date)

    rfm = df.groupby("customer_id").agg(
        last_txn_date=("txn_date", "max"),
        frequency=("txn_id", "count"),
        monetary=("amount", "sum"),
    ).reset_index()

    rfm["recency_days"] = (snap - rfm["last_txn_date"]).dt.days
    rfm["R"] = pd.qcut(rfm["recency_days"].rank(method="first"), 5, labels=[5,4,3,2,1]).astype(int)
    rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"),    5, labels=[1,2,3,4,5]).astype(int)
    rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"),     5, labels=[1,2,3,4,5]).astype(int)
    rfm["rfm_score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)

    def assign_segment(row):
        key = (row["R"], row["F"], row["M"])
        return RFM_SEGMENTS.get(key, _rule_segment(row["R"], row["F"], row["M"]))

    def _rule_segment(r, f, m):
        if r >= 4: return "New" if f == 1 else "Loyal"
        if r <= 2: return "At Risk" if f >= 3 else "Lost"
        return "Potential"

    rfm["segment"] = rfm.apply(assign_segment, axis=1)
    log.info("Segment distribution:\n" + rfm["segment"].value_counts().to_string())
    return rfm


def revenue_concentration(rfm: pd.DataFrame) -> pd.DataFrame:
    """Show what % of revenue comes from each segment."""
    total = rfm["monetary"].sum()
    return rfm.groupby("segment").agg(
        customers=("customer_id","count"),
        revenue=("monetary","sum"),
    ).assign(pct_customers=lambda x: x["customers"]/x["customers"].sum()*100,
             pct_revenue=lambda x: x["revenue"]/total*100).sort_values("pct_revenue", ascending=False)
