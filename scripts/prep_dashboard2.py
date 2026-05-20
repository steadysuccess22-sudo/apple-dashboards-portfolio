"""
Dashboard 2 prep: Operational Metrics & Pipeline Health (Online Retail II).

Loads both sheets of online_retail.xlsx, cleans conservatively, and emits
four CSVs ready for Tableau plus a data quality summary.

Cleaning rules (per spec):
  - Drop rows where Quantity <= 0 or Price <= 0
  - Drop rows where Invoice starts with 'C' (cancellations)
  - KEEP rows with null Customer ID for revenue/order-level metrics
    (~22.77% of rows = real revenue, not noise)
  - Drop nulls in Customer ID ONLY when computing customer-level metrics

Outputs:
  ./output/dashboard2_daily.csv      (daily aggregates + 7-day MA + anomaly flag)
  ./output/dashboard2_countries.csv  (top 10 countries by revenue)
  ./output/dashboard2_heatmap.csv    (hour x day-of-week revenue + orders)
  ./output/dashboard2_data_quality.csv  (stage-by-stage drop summary)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

ROLLING_WINDOW = 7
ANOMALY_BASELINE_WINDOW = 30  # for rolling mean/std used by anomaly flag
ANOMALY_SIGMA = 2.0

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_combined() -> pd.DataFrame:
    xls_path = DATA / "online_retail.xlsx"
    xls = pd.ExcelFile(xls_path)
    frames = []
    for sh in xls.sheet_names:
        df = pd.read_excel(xls_path, sheet_name=sh)
        df["_source_sheet"] = sh
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    # Normalize column names: Online Retail II uses 'Invoice', 'Price', 'Customer ID'
    # The original Online Retail (v1) used 'InvoiceNo', 'UnitPrice', 'CustomerID'.
    rename_map = {
        "Invoice": "InvoiceNo",
        "Price": "UnitPrice",
        "Customer ID": "CustomerID",
    }
    combined = combined.rename(columns=rename_map)
    combined["InvoiceNo"] = combined["InvoiceNo"].astype(str)
    return combined


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Apply conservative cleaning rules and record what was dropped at each stage."""
    summary: list[dict] = []
    start = len(df)
    summary.append({"Stage": "0_raw_combined", "Rows": start, "Dropped_This_Stage": 0,
                    "Pct_Of_Raw": 100.0, "Note": "Both sheets concatenated"})

    # Stage 1: drop cancellations (InvoiceNo starts with 'C')
    mask_cancel = df["InvoiceNo"].str.startswith("C", na=False)
    dropped = int(mask_cancel.sum())
    df = df.loc[~mask_cancel].copy()
    summary.append({"Stage": "1_drop_cancellations", "Rows": len(df), "Dropped_This_Stage": dropped,
                    "Pct_Of_Raw": round(len(df) / start * 100, 2),
                    "Note": "Invoice codes starting with 'C'"})

    # Stage 2: drop non-positive quantity
    mask_q = df["Quantity"] <= 0
    dropped = int(mask_q.sum())
    df = df.loc[~mask_q].copy()
    summary.append({"Stage": "2_drop_nonpositive_quantity", "Rows": len(df), "Dropped_This_Stage": dropped,
                    "Pct_Of_Raw": round(len(df) / start * 100, 2),
                    "Note": "Quantity <= 0 (returns / adjustments)"})

    # Stage 3: drop non-positive price
    mask_p = df["UnitPrice"] <= 0
    dropped = int(mask_p.sum())
    df = df.loc[~mask_p].copy()
    summary.append({"Stage": "3_drop_nonpositive_price", "Rows": len(df), "Dropped_This_Stage": dropped,
                    "Pct_Of_Raw": round(len(df) / start * 100, 2),
                    "Note": "UnitPrice <= 0 (adjustments / errors)"})

    # Note: we deliberately KEEP rows with null CustomerID at this stage.
    null_cust = int(df["CustomerID"].isna().sum())
    summary.append({"Stage": "4_kept_null_customerid", "Rows": len(df), "Dropped_This_Stage": 0,
                    "Pct_Of_Raw": round(len(df) / start * 100, 2),
                    "Note": f"{null_cust:,} rows have null CustomerID — kept for revenue/order metrics; "
                            "filtered out only when computing customer-level metrics"})
    return df, summary


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Revenue"] = (df["Quantity"] * df["UnitPrice"]).round(2)
    dt = df["InvoiceDate"]
    df["Date"] = dt.dt.date
    df["Hour"] = dt.dt.hour
    df["DayOfWeek"] = dt.dt.day_name()
    df["WeekNumber"] = dt.dt.isocalendar().week.astype(int)
    df["YearMonth"] = dt.dt.to_period("M").dt.to_timestamp()
    return df


def daily_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Date", sort=True)
    daily = pd.DataFrame({
        "Revenue": g["Revenue"].sum(),
        "Order_Count": g["InvoiceNo"].nunique(),
        # customer-level metric: drop nulls before counting
        "Unique_Customers": g.apply(
            lambda s: s.loc[s["CustomerID"].notna(), "CustomerID"].nunique(),
            include_groups=False,
        ),
        "Line_Items": g.size(),
    }).reset_index()
    daily["Date"] = pd.to_datetime(daily["Date"])
    daily["Avg_Order_Value"] = (daily["Revenue"] / daily["Order_Count"]).round(2)

    # 7-day moving average of revenue (centered=False, trailing window)
    daily["Revenue_7day_MA"] = (
        daily["Revenue"].rolling(ROLLING_WINDOW, min_periods=1).mean().round(2)
    )

    # Anomaly flag: |revenue - rolling_mean_30| > 2 * rolling_std_30
    base_mean = daily["Revenue"].rolling(ANOMALY_BASELINE_WINDOW, min_periods=7).mean()
    base_std = daily["Revenue"].rolling(ANOMALY_BASELINE_WINDOW, min_periods=7).std()
    upper = base_mean + ANOMALY_SIGMA * base_std
    lower = base_mean - ANOMALY_SIGMA * base_std
    is_anom = (daily["Revenue"] > upper) | (daily["Revenue"] < lower)
    daily["Anomaly_Flag"] = is_anom.fillna(False).astype(int)
    daily["Anomaly_Type"] = np.select(
        [daily["Revenue"] > upper, daily["Revenue"] < lower],
        ["High", "Low"],
        default="Normal",
    )
    daily["Rolling_Mean_30"] = base_mean.round(2)
    daily["Rolling_Std_30"] = base_std.round(2)

    # Calendar helpers for filtering / display
    daily["Year"] = daily["Date"].dt.year
    daily["Month"] = daily["Date"].dt.month
    daily["Month_Name"] = daily["Date"].dt.strftime("%b")
    daily["DayOfWeek"] = daily["Date"].dt.day_name()
    daily["WeekNumber"] = daily["Date"].dt.isocalendar().week.astype(int)

    daily["Revenue"] = daily["Revenue"].round(2)
    return daily


def country_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Country", as_index=False).agg(
        Revenue=("Revenue", "sum"),
        Order_Count=("InvoiceNo", "nunique"),
        Line_Items=("Revenue", "size"),
    )
    g["Avg_Order_Value"] = (g["Revenue"] / g["Order_Count"]).round(2)
    # customer-level: filter nulls
    cust = (
        df.dropna(subset=["CustomerID"])
        .groupby("Country")["CustomerID"]
        .nunique()
        .rename("Unique_Customers")
        .reset_index()
    )
    g = g.merge(cust, on="Country", how="left").fillna({"Unique_Customers": 0})
    g["Unique_Customers"] = g["Unique_Customers"].astype(int)
    g["Revenue"] = g["Revenue"].round(2)
    g = g.sort_values("Revenue", ascending=False).reset_index(drop=True)
    g["Rank"] = g.index + 1
    g["Is_Top10"] = (g["Rank"] <= 10).astype(int)
    return g


def hour_dow_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["DayOfWeek", "Hour"], as_index=False).agg(
        Revenue=("Revenue", "sum"),
        Order_Count=("InvoiceNo", "nunique"),
        Line_Items=("Revenue", "size"),
    )
    # Ensure ordering for Tableau
    g["DayOfWeek_Order"] = g["DayOfWeek"].map({d: i + 1 for i, d in enumerate(DAY_ORDER)})
    g["Revenue"] = g["Revenue"].round(2)
    g = g.sort_values(["DayOfWeek_Order", "Hour"]).reset_index(drop=True)
    return g


def main() -> None:
    print("Loading both sheets...")
    raw = load_combined()
    print(f"Raw combined: {raw.shape}")

    cleaned, dq = clean(raw)
    print(f"Cleaned: {cleaned.shape}")

    enriched = add_derived(cleaned)

    daily = daily_aggregate(enriched)
    countries = country_breakdown(enriched)
    heatmap = hour_dow_heatmap(enriched)
    dq_df = pd.DataFrame(dq)

    daily_path = OUT / "dashboard2_daily.csv"
    countries_path = OUT / "dashboard2_countries.csv"
    heatmap_path = OUT / "dashboard2_heatmap.csv"
    dq_path = OUT / "dashboard2_data_quality.csv"

    daily.to_csv(daily_path, index=False)
    countries.to_csv(countries_path, index=False)
    heatmap.to_csv(heatmap_path, index=False)
    dq_df.to_csv(dq_path, index=False)

    print("\n=== Outputs ===")
    for p in (daily_path, countries_path, heatmap_path, dq_path):
        print(f"  {p}  ({p.stat().st_size:,} bytes)")

    print("\n--- Data Quality Summary ---")
    print(dq_df.to_string(index=False))

    print(f"\n--- Daily aggregates ({daily.shape}) ---")
    print(f"Date range: {daily['Date'].min().date()} -> {daily['Date'].max().date()}")
    print(f"Anomalies flagged: {int(daily['Anomaly_Flag'].sum())} of {len(daily)} days "
          f"({daily['Anomaly_Flag'].mean():.1%})")
    print(daily.head(10).to_string(index=False))

    print(f"\n--- Top 10 Countries ---")
    print(countries.head(10).to_string(index=False))

    print(f"\n--- Heatmap (head 14) shape={heatmap.shape} ---")
    print(heatmap.head(14).to_string(index=False))


if __name__ == "__main__":
    main()
