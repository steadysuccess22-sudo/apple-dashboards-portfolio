# Apple Data Analyst Portfolio — Financial Variance & Operational Metrics Dashboards

> Built for Apple Data Analyst & AI Automation Specialist (Posting #210265, Req #37276997).
> Submitted via Aquent — May 2026.

## 🔗 Live Dashboards
- **[Financial Performance & Variance Dashboard](https://public.tableau.com/views/dashboard1_financial_variance/FinancialPerformanceVarianceDashboard)** — 5 KPIs · 5 analytical charts · Sample-Superstore dataset
- **[Operational Metrics & Pipeline Health Dashboard](https://public.tableau.com/views/dashboard2_operational_metrics/OperationalMetricsPipelineHealthDashboard)** — 5 KPIs · 4 analytical charts · UCI Online Retail II
- **[Tableau Public profile](https://public.tableau.com/app/profile/phanindra.ram/vizzes)**

![Dashboard 1](screenshots/dashboard1_full.png)
![Dashboard 2](screenshots/dashboard2_full.png)

## About this project

Two end-to-end Tableau dashboards answering the kinds of questions a finance or operations team actually asks: where are we vs. plan, which segments are dragging margin, when do orders spike, and how clean is the data underneath. Each dashboard pairs a row of KPIs with deeper analytical views — variance heatmaps, margin matrices, hour-of-day demand patterns, and a transparent data-quality funnel.

The framing matches the Apple posting's emphasis on AI-automation literacy. Data prep is scripted in Python (profiling, cleaning, feature engineering) and the report layer is reproducible from this repo. Visual design and chart configuration were done manually in Tableau Desktop; AI assistance (Claude Code, Cursor) was used for code generation, XML diffing, and review — with every step source-controlled and inspectable.

## Dashboard 1: Financial Performance & Variance
- Dataset: Tableau Sample-Superstore, 10,194 rows × 21 cols (Jan 2023 – Dec 2026)
- 10 worksheets: 5 KPI tiles + Monthly Sales hero + MoM Variance + YoY Heatmap + Margin Matrix + Forecast Accuracy
- Headline metrics: $2.33M sales · $292K profit · 12.56% blended margin · 47.2% YoY · $289K 3-month forecast
- Key insights:
  - East × Home Office best margin (20.9%); Central × Consumer worst (3.4%)
  - Fasteners +515% YoY 2026 vs 2025
  - Binders, Tables, Machines structurally loss-making
- Engineering decisions:
  - Blended margin = SUM(profit)/SUM(sales) — not AVG of row-level percentages
  - Calculated fields for YoY/MoM variance and forecast deltas
  - Forecast = 3-month trailing moving average (simple baseline, would discuss alternatives with stakeholders)

## Dashboard 2: Operational Metrics & Pipeline Health
- Dataset: UCI ML Repository — Online Retail II, 1,067,371 raw rows (Dec 2009 – Dec 2011), two combined sheets
- 9 worksheets: 5 KPI tiles + Daily Revenue with 7-day MA + Hour × Day-of-Week Heatmap + Top 10 Countries + Data Quality Funnel
- Headline metrics: $20.97M revenue · 40K orders · 33.1K customers · $516.84 AOV · 30 anomaly days
- Key insights:
  - UK = 87% of revenue ($17.87M) — classic Pareto distribution, justifies UK-vs-Other color split
  - Tuesday 12-16 peak business hours
  - No Saturday operations visible in hour × day heatmap
  - Two major spike days (Nov 2010, Jan 2012) — likely promotional or B2B bulk orders
- Data quality differentiator:
  - 4-stage cleaning pipeline with documented row-level audit trail
  - 1,067,371 → 1,041,670 rows = 97.59% retention
  - Every dropped row justified: cancellations, Quantity ≤ 0, UnitPrice ≤ 0, null CustomerID kept (with caveats)

## Methodology — AI-assisted workflow
- Python data prep pipelines (pandas + openpyxl) for profiling, cleaning, feature engineering
- Tableau Desktop worksheet construction (manual; calculated fields, color encoding, layout)
- Direct Tableau .twb XML composition for dashboard layout assembly via Claude Code, with safety protocols:
  - All operations on TEST files; originals SHA-256 verified untouched
  - XSD-compliant XML validation before declaring success
  - Iterative refinement capped at 2 attempts per issue
- Every step reproducible from the scripts in this repo + the design_spec.md

## Repository structure

```
apple-dashboards-portfolio/
├── README.md
├── .gitignore
├── scripts/
│   ├── prep_dashboard1.py
│   ├── prep_dashboard2.py
│   └── profile_datasets.py
├── tableau/
│   ├── dashboard1_financial_variance.twb
│   └── dashboard2_operational_metrics.twb
├── data_raw/
│   └── superstore.csv            # Sample-Superstore (included with Tableau)
├── data_prepped/                 # cleaned outputs from prep scripts
│   ├── dashboard1_ready.csv
│   ├── dashboard2_daily.csv
│   ├── dashboard2_countries.csv
│   ├── dashboard2_heatmap.csv
│   └── dashboard2_data_quality.csv
├── docs/
│   └── design_spec.md
└── screenshots/
```

Online Retail II (~45 MB) is not committed — fetch it from the UCI link below.

## Reproducibility
- Python 3.10+ with pandas, openpyxl
- Raw data sources:
  - Sample-Superstore: included in `data_raw/` and ships with [Tableau Desktop](https://help.tableau.com/current/guides/get-started-tutorial/en-us/get-started-tutorial-connect.htm)
  - Online Retail II: [UCI ML Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii) — download `online_retail_II.xlsx` into `data_raw/` before running `prep_dashboard2.py`
- Run prep scripts: `python scripts/prep_dashboard1.py` and `python scripts/prep_dashboard2.py`
- Open .twb files in Tableau Desktop or Tableau Public (free) to inspect

## Honest caveats
- Sample-Superstore is synthetic data; a real engagement would involve stakeholder workshops to define metrics correctly
- "Customers" KPI is sum of daily distinct counts (not COUNT DISTINCT over full period) — would refactor in production
- YoY is aggregate across comparison years, not strict latest-year YoY
- MAPE not quoted on forecast accuracy (dense zero-filled grid would deflate it; would discuss filter approach with stakeholders)
- Data quality funnel methodology shows auditable provenance — every drop justified, no silent transformations

## Tech stack
Python · pandas · openpyxl · Tableau Desktop 2024.x · Tableau Public · Claude Code (Opus 4.7) · Cursor IDE

## Author
**K Phanindra Sai Ram**
Data Analyst | NLP & AI Automation
📧 applyphanindra@outlook.com
🔗 [LinkedIn](https://linkedin.com/in/applyphanindra) · [GitHub](https://github.com/steadysuccess22-sudo) · [Tableau Public](https://public.tableau.com/app/profile/phanindra.ram/vizzes)

---

*This project was built as a portfolio submission for the Apple Data Analyst & AI Automation Specialist role (Req #37276997). All data sources are publicly available; no proprietary information is included.*
