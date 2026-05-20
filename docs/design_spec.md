# Tableau Dashboard Design Spec

Two dashboards, one consistent visual language, both built on pre-aggregated CSVs so Tableau is pure drag-and-drop.

---

## Shared Visual System

**Why one palette across both dashboards:** a portfolio reads as a single body of work. Reusing the palette signals deliberate design, not ad-hoc styling.

| Role | Hex | Use |
|---|---|---|
| Primary (brand blue) | `#1F4E79` | KPI numbers, axis titles, primary marks |
| Secondary (mid blue) | `#4A90E2` | Bars, line marks, hover states |
| Tertiary (pale blue) | `#D6E4F2` | Background fills, low-intensity heatmap |
| Accent — positive | `#2E7D32` | Favorable variance, beat forecast |
| Accent — negative | `#C62828` | Unfavorable variance, anomaly High/Low |
| Accent — neutral | `#9E9E9E` | Flat / Normal |
| Surface | `#F4F6F8` | Dashboard background |
| Text primary | `#1C1C1E` | Labels, headlines |
| Text muted | `#6B7280` | Captions, footnotes |

**Typography:** Tableau default (Benton Sans) for everything; 22pt dashboard title, 14pt worksheet titles, 11pt axis, 10pt tooltips.

**Sizing target:** 1300 × 820 px (fits Tableau Public at default zoom; readable in PDF screenshot).

**Layout grid:** 12-column implicit grid with 8px gutters. Title bar → KPI strip → hero chart → 2-up support row → footer/source note.

---

## Dashboard 1 — Financial Variance & Forecasting

**Source:** `output/dashboard1_ready.csv` (10,353 rows, monthly grain × Category × Sub-Category × Region × Segment, includes 3-month forward forecast rows)

**Business question:**
*"Where are we beating or missing plan, what's driving month-over-month and year-over-year movement, and what does the next quarter look like at current run-rate?"*

This is the JD's "financial variance reporting + month-over-month forecasting + P&L analysis" line item.

### Worksheets (6)

| # | Title | Chart type | Encoding | What it shows |
|---|---|---|---|---|
| W1 | **KPI strip** | 5 BANs | Text marks | Total Sales · Total Profit · Profit Margin % · YoY Sales Δ% · 3-mo Forecast Total |
| W2 | **Sales trend with forecast** | Dual-line area | X: YearMonth · Y: Sales (solid) + Sales_Forecast (dashed) · Color: Row_Type | Hero chart. Actual sales line continues into a dashed forecast tail for the next 3 months. |
| W3 | **MoM variance** | Diverging bar | X: YearMonth · Y: Sales_MoM_Variance_Pct · Color: Variance_Direction | Where months popped or dropped. Green/red bars above/below zero. |
| W4 | **YoY heatmap** | Matrix heatmap | Rows: Sub-Category · Columns: Year · Color: Sales_YoY_Variance_Pct (diverging −/+) | Which product lines grew or shrank year-over-year. Quick scan for outliers. |
| W5 | **Profit margin by segment & region** | Highlight table | Rows: Region · Cols: Segment · Color: Profit_Margin_Pct · Label: Profit (formatted $) | P&L view — which Region × Segment cells are margin-accretive vs dilutive. |
| W6 | **Forecast accuracy** | Bar + reference line | X: YearMonth (last 12 months) · Y: Forecast_vs_Actual_Delta · Color: positive/negative | Honesty check on the 3-month moving-average forecast. Bars above zero = we beat forecast. |

### Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  W1: KPI STRIP — 5 big numbers across the top (height ~110 px)     │
├──────────────────────────────────┬─────────────────────────────────┤
│                                  │                                 │
│  W2: Sales trend + forecast      │  W3: MoM variance bars          │
│  (hero, 60% width)               │  (40% width, ~360 px tall)      │
│                                  │                                 │
├──────────────────────────────────┼─────────────────────────────────┤
│                                  │                                 │
│  W4: YoY heatmap                 │  W5: Profit margin matrix       │
│  (50% width)                     │  (50% width)                    │
│                                  │                                 │
├──────────────────────────────────┴─────────────────────────────────┤
│  W6: Forecast vs Actual delta — last 12 months (full width, ~140 px)│
└────────────────────────────────────────────────────────────────────┘
```

### Filters (top of dashboard, single row)

- **Year** (multi-select dropdown, default = All)
- **Region** (multi-select dropdown)
- **Segment** (multi-select dropdown)
- **Category** (single-select, drives Sub-Category cascade)
- **Sub-Category** (multi-select, dependent on Category)
- **Row_Type** (toggle: Actual / Forecast / Both, default Both)

### Interactivity

- **Highlight action** on Category — clicking a category in W4 or W5 highlights that category across W2, W3, W6.
- **Tooltip action** — hovering W2 reveals the W3 mini-tooltip values for the same month.
- **Sort by W4** ascending/descending — clicking a year column sorts sub-categories by YoY growth in that year.

### Tooltip content per worksheet

| Worksheet | Tooltip |
|---|---|
| W1 (KPI) | static (no tooltip needed) |
| W2 | `[Month_Name] [Year]` — Sales: `$[Sales]` · Forecast: `$[Sales_Forecast]` · Δ vs forecast: `$[Forecast_vs_Actual_Delta]` · MoM: `[Sales_MoM_Variance_Pct]%` · YoY: `[Sales_YoY_Variance_Pct]%` |
| W3 | `[Month_Name] [Year]` — MoM change: `[Sales_MoM_Variance_Pct]%` (`$[Sales_MoM_Variance]`) · Prior month: `$[Sales_Prior_Month]` |
| W4 | `[Sub-Category] in [Year]` — YoY: `[Sales_YoY_Variance_Pct]%` · This year: `$[Sales]` · Prior year: `$[Sales_Prior_Year]` |
| W5 | `[Region] / [Segment]` — Sales: `$[Sales]` · Profit: `$[Profit]` · Margin: `[Profit_Margin_Pct]%` |
| W6 | `[Month_Name] [Year]` — Forecast: `$[Sales_Forecast]` · Actual: `$[Sales]` · Δ: `$[Forecast_vs_Actual_Delta]` (`[positive/negative]`) |

---

## Dashboard 2 — Operational Metrics & Pipeline Health

**Sources:**
- `output/dashboard2_daily.csv` (604 rows, daily aggregates with 7-day MA, 30-day rolling baseline, anomaly flag)
- `output/dashboard2_countries.csv` (~40 rows, ranked, `Is_Top10` flag)
- `output/dashboard2_heatmap.csv` (85 rows, hour × day-of-week)
- `output/dashboard2_data_quality.csv` (5 rows, cleaning funnel)

**Business question:**
*"What's the daily revenue pulse, when do anomalies fire, what's the hourly/weekly transaction rhythm, and which geographies drive the book — with the data quality story shown openly?"*

This is the JD's "operational metrics + data quality monitoring + maximize team throughput" line item. The data-quality funnel is the differentiator.

### Worksheets (6)

| # | Title | Chart type | Encoding | What it shows |
|---|---|---|---|---|
| W1 | **KPI strip** | 5 BANs | Text marks | Total Revenue · Total Orders · Unique Customers · Avg Order Value · Anomaly Days (count + %) |
| W2 | **Daily revenue with 7-day MA + anomalies** | Line + rolling line + dot overlay | X: Date · Y: Revenue (line) + Revenue_7day_MA (smoothed line) · Anomaly_Flag=1 plotted as dots colored by Anomaly_Type | Hero chart. The smooth line frames context; red dots = High anomaly, blue dots = Low anomaly. |
| W3 | **Hour × Day-of-Week heatmap** | Density heatmap | Rows: DayOfWeek (Mon→Sun) · Cols: Hour · Color: Revenue (sequential blue) | Operational rhythm — when are customers transacting. |
| W4 | **Top 10 countries** | Horizontal bar | Y: Country (rank-sorted desc) · X: Revenue · Color: highlight UK as primary, rest secondary | Geographic concentration. UK at 87% of revenue is the headline. |
| W5 | **Data quality funnel** | Bar chart + step-down labels | Y: Stage · X: Rows · Annotation: % retained at each step | Auditable cleaning trail — what was dropped and why. |
| W6 | **AOV vs Order volume scatter** | Scatter | X: Order_Count · Y: Avg_Order_Value · Size: Revenue · Label: Country (top 10 only) | Reveals the "few big orders" vs "many small orders" countries (e.g. Netherlands AOV $2.4K but only 228 orders). |

### Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  W1: KPI STRIP — Revenue · Orders · Customers · AOV · Anomalies    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  W2: Daily revenue + 7-day MA + anomaly dots (HERO, full width)    │
│      (~280 px tall)                                                │
│                                                                    │
├──────────────────────────────────┬─────────────────────────────────┤
│                                  │                                 │
│  W3: Hour × Day heatmap          │  W4: Top 10 countries           │
│  (60% width)                     │  (40% width)                    │
│                                  │                                 │
├──────────────────────────────────┼─────────────────────────────────┤
│                                  │                                 │
│  W5: Data quality funnel         │  W6: AOV vs Order volume        │
│  (50% width)                     │  (50% width)                    │
│                                  │                                 │
└────────────────────────────────────────────────────────────────────┘
```

### Filters (top of dashboard)

- **Date range** (slider, default = full range)
- **Country** (multi-select, default = All)
- **DayOfWeek** (multi-select)
- **Anomaly_Flag** (toggle: All / Only Anomalies, default All)
- **Is_Top10** (toggle on W4 scatter only — restrict country labels in W6 to top 10)

### Interactivity

- **Highlight action** on Country — clicking a country in W4 highlights its share across W2 and W3 (where Country exists in source — note W3 is country-agnostic in current build).
- **Filter action** from W2 to all other sheets — clicking an anomaly dot filters the rest of the dashboard to that date range ±7 days.
- **URL action** on data quality funnel — clicking opens the prep script in a separate tab (linking to GitHub Gist or README) to show the auditable code.

### Tooltip content per worksheet

| Worksheet | Tooltip |
|---|---|
| W1 (KPI) | static |
| W2 | `[Date]` — Revenue: `$[Revenue]` · 7-day MA: `$[Revenue_7day_MA]` · Orders: `[Order_Count]` · Customers: `[Unique_Customers]` · AOV: `$[Avg_Order_Value]` · *if Anomaly_Flag=1:* "⚠ [Anomaly_Type] anomaly — `[Revenue]` is `[(Revenue - Rolling_Mean_30)/Rolling_Std_30]`σ from 30-day mean" |
| W3 | `[DayOfWeek] @ [Hour]:00` — Revenue: `$[Revenue]` · Orders: `[Order_Count]` · Line items: `[Line_Items]` |
| W4 | `[Country] (rank #[Rank])` — Revenue: `$[Revenue]` · Orders: `[Order_Count]` · Customers: `[Unique_Customers]` · AOV: `$[Avg_Order_Value]` |
| W5 | `[Stage]` — Rows remaining: `[Rows]` · Dropped at this stage: `[Dropped_This_Stage]` · `[Note]` |
| W6 | `[Country]` — `[Order_Count]` orders @ `$[Avg_Order_Value]` AOV → `$[Revenue]` total |

---

## Notes for Tableau implementation

1. **Both dashboards use the same color palette.** Apply it once via Tableau's "Edit Colors" → save as custom palette `Apple-Portfolio-2026.tps` in `My Tableau Repository/Preferences.tml`.
2. **`Variance_Direction` in Dashboard 1 maps directly to color** — `Positive`→`#2E7D32`, `Negative`→`#C62828`, `Flat`→`#9E9E9E`.
3. **`Anomaly_Type` in Dashboard 2 maps directly to color** — `High`→`#C62828`, `Low`→`#1F4E79`, `Normal`→transparent (or filter out).
4. **`Row_Type` in Dashboard 1 controls line style** — `Actual`→solid, `Forecast`→dashed. Achieved via a calculated field referencing `[Row_Type]` on the Path or via a dual-axis line trick.
5. **Forecast continuity:** The forecast line and actual line should connect at the last actual month. Both lines reference `Sales_Forecast` for forecast rows; `Sales` for actual rows. Use `IFNULL([Sales], [Sales_Forecast])` if joining into one continuous line.
6. **Currency formatting:** $ symbol, thousands separator, 0 decimals on KPIs ($17,870,978), 2 decimals on detail tooltips ($17,870,977.76).
7. **Performance:** All four CSVs are < 60 KB. Use Tableau Extract (Hyper) for snappy filtering; live connection is fine but extract is faster on Tableau Public.

---

## Acceptance criteria for "done"

- Both dashboards open in Tableau Public without warnings.
- All filters function and cascade as specified.
- Tooltips render the listed fields with correct formatting.
- KPI strip totals match the underlying CSV (spot-check by SUM in pandas).
- No calculated fields beyond the 5 noted above (1 IFNULL for forecast continuity, 1 sigma calculation in W2 tooltip).
- Dashboard renders cleanly at 1300 × 820 px.
