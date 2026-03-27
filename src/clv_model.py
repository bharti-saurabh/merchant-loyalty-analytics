"""
Customer Lifetime Value Model — Merchant Loyalty Analytics
Straive Strategic Analytics
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

log = logging.getLogger(__name__)


def compute_historical_clv(df: pd.DataFrame, periods: int = 12) -> pd.DataFrame:
    """Compute historical CLV per customer over rolling periods."""
    df["month"] = pd.to_datetime(df["txn_date"]).dt.to_period("M")
    monthly = df.groupby(["customer_id","month"])["amount"].sum().reset_index()
    monthly_pivot = monthly.pivot(index="customer_id", columns="month", values="amount").fillna(0)

    last_n = monthly_pivot.iloc[:, -periods:]
    clv_hist = last_n.sum(axis=1).rename("clv_trailing_12m")
    avg_monthly = last_n.mean(axis=1).rename("avg_monthly_spend")
    months_active = (last_n > 0).sum(axis=1).rename("active_months")
    return pd.concat([clv_hist, avg_monthly, months_active], axis=1).reset_index()


def predict_future_clv(clv_hist: pd.DataFrame, horizon_months: int = 12) -> pd.DataFrame:
    """Simple linear extrapolation of CLV trajectory per customer."""
    clv = clv_hist.copy()
    clv["predicted_clv"] = clv["avg_monthly_spend"] * horizon_months * (clv["active_months"] / 12).clip(0.1, 1)
    clv["clv_tier"] = pd.qcut(clv["predicted_clv"], q=4, labels=["Bronze","Silver","Gold","Platinum"])
    log.info("CLV tier distribution:\n" + clv["clv_tier"].value_counts().to_string())
    return clv


def top_decile_profile(clv: pd.DataFrame, rfm: pd.DataFrame) -> pd.DataFrame:
    """Characterise the top-10% CLV customers."""
    threshold = clv["predicted_clv"].quantile(0.90)
    top = clv[clv["predicted_clv"] >= threshold]
    merged = top.merge(rfm[["customer_id","segment","R","F","M"]], on="customer_id", how="left")
    log.info(f"Top decile: {len(merged):,} customers | avg CLV: {merged['predicted_clv'].mean():.0f}")
    return merged
