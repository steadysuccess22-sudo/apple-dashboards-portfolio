"""
Dashboard 1 prep: Financial Variance & Forecasting (Superstore).

Aggregates Superstore line items to monthly grain by
(Category, Sub-Category, Region, Segment) and pre-computes all
variance, YoY, and forecast columns so Tableau is pure drag-and-drop.

Output: ./output/dashboard1_ready.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

GROUP_KEYS = ["Category", "Sub-Category", "Region", "Segment"]
FORECAST_HORIZON = 3  # months to project past the last actual
MA_WINDOW = 3  # 3-month moving average


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA / "superstore.csv", parse_dates=["Order Date"])
    keep = ["Order Date", *GROUP_KEYS, "Sales", "Profit", "Quantity", "Discount"]
    return df[keep].copy()


def monthly_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    df["YearMonth"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    agg = (
        df.groupby(["YearMonth", *GROUP_KEYS], as_index=False)
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Quantity=("Quantity", "sum"),
            Discount=("Discount", "mean"),  # average discount applied
        )
    )
    return agg


def densify(agg: pd.DataFrame) -> pd.DataFrame:
    """Create a dense monthly grid so MoM/YoY aren't skewed by missing months."""
    months = pd.date_range(agg["YearMonth"].min(), agg["YearMonth"].max(), freq="MS")
    combos = (
        agg[GROUP_KEYS].drop_duplicates().reset_index(drop=True)
    )
    grid = combos.assign(_k=1).merge(
        pd.DataFrame({"YearMonth": months, "_k": 1}), on="_k"
    ).drop(columns="_k")
    full = grid.merge(agg, on=["YearMonth", *GROUP_KEYS], how="left")
    fill_zero = ["Sales", "Profit", "Quantity"]
    full[fill_zero] = full[fill_zero].fillna(0)
    full["Discount"] = full["Discount"].fillna(0)
    return full.sort_values([*GROUP_KEYS, "YearMonth"]).reset_index(drop=True)


def add_variance_and_forecast(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(GROUP_KEYS, sort=False)

    # MoM: compare to prior month within same group
    df["Sales_Prior_Month"] = g["Sales"].shift(1)
    df["Sales_MoM_Variance"] = df["Sales"] - df["Sales_Prior_Month"]
    df["Sales_MoM_Variance_Pct"] = np.where(
        df["Sales_Prior_Month"].abs() > 0,
        df["Sales_MoM_Variance"] / df["Sales_Prior_Month"] * 100.0,
        np.nan,
    )

    # YoY: compare to same month, prior year, within same group (12-month lag)
    df["Sales_Prior_Year"] = g["Sales"].shift(12)
    df["Sales_YoY_Variance"] = df["Sales"] - df["Sales_Prior_Year"]
    df["Sales_YoY_Variance_Pct"] = np.where(
        df["Sales_Prior_Year"].abs() > 0,
        df["Sales_YoY_Variance"] / df["Sales_Prior_Year"] * 100.0,
        np.nan,
    )

    # Trailing 3-month moving average -> use prior 3 months as forecast for current month
    df["Sales_Forecast"] = g["Sales"].transform(
        lambda s: s.shift(1).rolling(MA_WINDOW, min_periods=1).mean()
    )
    df["Forecast_vs_Actual_Delta"] = df["Sales"] - df["Sales_Forecast"]

    # Profit margin %
    df["Profit_Margin_Pct"] = np.where(
        df["Sales"] != 0, df["Profit"] / df["Sales"] * 100.0, np.nan
    )

    # Calendar fields
    df["Year"] = df["YearMonth"].dt.year
    df["Month"] = df["YearMonth"].dt.month
    df["Month_Name"] = df["YearMonth"].dt.strftime("%b")

    # Variance direction for color coding
    eps = 1e-9
    df["Variance_Direction"] = np.select(
        [df["Sales_MoM_Variance"] > eps, df["Sales_MoM_Variance"] < -eps],
        ["Positive", "Negative"],
        default="Flat",
    )

    # Row type marker (actual data; forecast rows added separately)
    df["Row_Type"] = "Actual"
    return df


def append_forward_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """Add FORECAST_HORIZON future months per group with Sales=NaN, forecast = trailing MA."""
    out_rows = []
    for keys, sub in df.groupby(GROUP_KEYS, sort=False):
        sub = sub.sort_values("YearMonth")
        last_month = sub["YearMonth"].max()
        future_months = pd.date_range(
            last_month + pd.offsets.MonthBegin(1), periods=FORECAST_HORIZON, freq="MS"
        )
        # Use a rolling 3-month MA that incrementally consumes its own forecasts
        history = list(sub["Sales"].tail(MA_WINDOW))
        for fm in future_months:
            fcst = float(np.mean(history[-MA_WINDOW:])) if history else np.nan
            row = dict(zip(GROUP_KEYS, keys))
            row.update(
                {
                    "YearMonth": fm,
                    "Sales": np.nan,
                    "Profit": np.nan,
                    "Quantity": np.nan,
                    "Discount": np.nan,
                    "Sales_Prior_Month": np.nan,
                    "Sales_MoM_Variance": np.nan,
                    "Sales_MoM_Variance_Pct": np.nan,
                    "Sales_Prior_Year": np.nan,
                    "Sales_YoY_Variance": np.nan,
                    "Sales_YoY_Variance_Pct": np.nan,
                    "Sales_Forecast": fcst,
                    "Forecast_vs_Actual_Delta": np.nan,
                    "Profit_Margin_Pct": np.nan,
                    "Year": fm.year,
                    "Month": fm.month,
                    "Month_Name": fm.strftime("%b"),
                    "Variance_Direction": "Flat",
                    "Row_Type": "Forecast",
                }
            )
            out_rows.append(row)
            history.append(fcst)
    if not out_rows:
        return df
    return pd.concat([df, pd.DataFrame(out_rows)], ignore_index=True)


def round_numeric(df: pd.DataFrame) -> pd.DataFrame:
    money = ["Sales", "Profit", "Sales_Prior_Month", "Sales_MoM_Variance",
             "Sales_Prior_Year", "Sales_YoY_Variance", "Sales_Forecast",
             "Forecast_vs_Actual_Delta"]
    pct = ["Sales_MoM_Variance_Pct", "Sales_YoY_Variance_Pct", "Profit_Margin_Pct"]
    for c in money:
        if c in df:
            df[c] = df[c].round(2)
    for c in pct:
        if c in df:
            df[c] = df[c].round(2)
    if "Discount" in df:
        df["Discount"] = df["Discount"].round(4)
    return df


def main() -> None:
    raw = load()
    print(f"Loaded raw: {raw.shape}")

    agg = monthly_aggregate(raw)
    print(f"Aggregated (sparse): {agg.shape}")

    dense = densify(agg)
    print(f"Densified grid: {dense.shape}")

    with_vars = add_variance_and_forecast(dense)
    full = append_forward_forecast(with_vars)
    full = round_numeric(full)

    full = full.sort_values([*GROUP_KEYS, "YearMonth"]).reset_index(drop=True)

    out_cols = [
        "YearMonth", "Year", "Month", "Month_Name", "Row_Type",
        "Category", "Sub-Category", "Region", "Segment",
        "Sales", "Profit", "Quantity", "Discount", "Profit_Margin_Pct",
        "Sales_Prior_Month", "Sales_MoM_Variance", "Sales_MoM_Variance_Pct",
        "Sales_Prior_Year", "Sales_YoY_Variance", "Sales_YoY_Variance_Pct",
        "Sales_Forecast", "Forecast_vs_Actual_Delta", "Variance_Direction",
    ]
    full = full[out_cols]

    out_path = OUT / "dashboard1_ready.csv"
    full.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
    print(f"Final shape: {full.shape[0]:,} rows x {full.shape[1]} cols")
    print(f"\nRow_Type breakdown:\n{full['Row_Type'].value_counts().to_string()}")
    print(f"\nDate range: {full['YearMonth'].min().date()} -> {full['YearMonth'].max().date()}")
    print(f"\nColumns:\n  " + "\n  ".join(out_cols))
    print(f"\nHead (5):\n{full.head().to_string()}")
    print(f"\nSample with variance (mid-series, Furniture/Chairs/East/Consumer):")
    sample = full[
        (full["Category"] == "Furniture")
        & (full["Sub-Category"] == "Chairs")
        & (full["Region"] == "East")
        & (full["Segment"] == "Consumer")
    ].head(15)
    print(sample.to_string(index=False))


if __name__ == "__main__":
    main()
