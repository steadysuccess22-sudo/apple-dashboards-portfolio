"""Profile both datasets and write reports to ./output/."""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)


def profile(df: pd.DataFrame, name: str, date_cols: list[str]) -> str:
    buf = io.StringIO()
    w = buf.write
    w(f"=== Profile: {name} ===\n\n")
    w(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} cols\n\n")

    w("Columns & dtypes:\n")
    for c, dt in df.dtypes.items():
        w(f"  - {c}: {dt}\n")
    w("\n")

    for dc in date_cols:
        if dc in df.columns:
            s = pd.to_datetime(df[dc], errors="coerce")
            w(f"Date range [{dc}]: {s.min()} -> {s.max()} (nulls: {s.isna().sum():,})\n")
    w("\n")

    miss = df.isna().sum()
    miss = miss[miss > 0].sort_values(ascending=False)
    w("Missing values (cols with > 0 nulls):\n")
    if miss.empty:
        w("  (none)\n")
    else:
        for c, n in miss.items():
            w(f"  - {c}: {n:,} ({n / len(df):.2%})\n")
    w("\n")

    num = df.select_dtypes(include="number")
    if not num.empty:
        w("Numeric stats:\n")
        w(num.describe().T.to_string())
        w("\n\n")

    w("Head (5 rows):\n")
    w(df.head(5).to_string())
    w("\n")
    return buf.getvalue()


def main() -> None:
    # Dashboard 1 - Superstore
    ss = pd.read_csv(DATA / "superstore.csv", parse_dates=["Order Date", "Ship Date"])
    rep1 = profile(ss, "Superstore (Dashboard 1)", ["Order Date", "Ship Date"])
    (OUT / "profile_dashboard1.txt").write_text(rep1, encoding="utf-8")

    # Dashboard 2 - Online Retail II (2 sheets)
    xls_path = DATA / "online_retail.xlsx"
    xls = pd.ExcelFile(xls_path)
    print(f"online_retail sheets: {xls.sheet_names}")
    frames = []
    for sh in xls.sheet_names:
        df = pd.read_excel(xls_path, sheet_name=sh)
        df["_sheet"] = sh
        frames.append(df)
        print(f"  - {sh}: {df.shape}")
    retail = pd.concat(frames, ignore_index=True)
    date_col = "InvoiceDate" if "InvoiceDate" in retail.columns else None
    rep2 = profile(retail, "Online Retail II combined (Dashboard 2)", [date_col] if date_col else [])
    (OUT / "profile_dashboard2.txt").write_text(rep2, encoding="utf-8")

    print("\n--- DASHBOARD 1 REPORT ---")
    print(rep1)
    print("\n--- DASHBOARD 2 REPORT ---")
    print(rep2)


if __name__ == "__main__":
    main()
