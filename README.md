# 📊 Sales Performance Analysis and Reporting System

> A production-quality, end-to-end retail analytics solution built on the **Sample Superstore** dataset using Python, SQLite, Pandas, Matplotlib, Plotly, and Streamlit.

---

## 🎯 Problem Statement

Retail businesses generate enormous volumes of transactional data but often lack the analytical infrastructure to convert that data into actionable business intelligence. This project addresses that gap by building a complete analytics pipeline — from raw CSV ingestion through to an interactive executive dashboard — covering sales performance, regional analysis, product profitability, discount effectiveness, return rates, and shipping efficiency.

---

## 🏆 Objectives

1. Ingest raw CSV data into a relational SQLite database.
2. Apply structured data cleaning using SQL.
3. Integrate three related tables via SQL JOINs.
4. Transfer cleaned data into Pandas for comprehensive analysis.
5. Generate professional visualizations using Matplotlib and Seaborn.
6. Present findings through an interactive Streamlit BI dashboard.
7. Automate report generation (Excel, CSV, executive summary).
8. Validate the entire pipeline with automated tests.

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13+ |
| Database | SQLite 3 |
| Data Analysis | Pandas 2.x, NumPy |
| Visualization | Matplotlib, Seaborn, Plotly Express |
| Dashboard | Streamlit 1.29+ |
| Reporting | openpyxl, XlsxWriter |
| Testing | pytest |
| Version Control | Git |

---

## 🏗 Architecture

```
CSV Files
   │
   ▼
[Ingestion Layer]  ──  ingestion.py
   │  Reads and normalizes column names
   ▼
[SQLite Database]  ──  database/sales.db
   │  Orders / Returns / People tables
   ▼
[Cleaning Layer]   ──  data_cleaning.py + cleaning.sql
   │  NULL audit, dedup, standardization
   ▼
[SQL JOIN Layer]   ──  analysis.sql
   │  Master LEFT JOIN query + derived columns
   ▼
[Pandas Analysis]  ──  analysis.py (SalesAnalyzer)
   │  9 analytical modules
   ├──────────────────┬──────────────────┐
   ▼                  ▼                  ▼
[Visualizations]  [Reporting]       [Dashboard]
 visualizations.py  reporting.py    dashboard/app.py
 10 charts          CSV/Excel/TXT   Streamlit app
```

---

## 🗄 Database Schema

### `orders` table (21 columns)
| Column | Type | Description |
|--------|------|-------------|
| row_id | INTEGER | Unique row identifier |
| order_id | TEXT | Order identifier |
| order_date | TEXT | Date of order (YYYY-MM-DD) |
| ship_date | TEXT | Date shipped (YYYY-MM-DD) |
| ship_mode | TEXT | Shipping method |
| customer_id | TEXT | Customer identifier |
| customer_name | TEXT | Customer full name |
| segment | TEXT | Consumer / Corporate / Home Office |
| country | TEXT | Country |
| city | TEXT | City |
| state | TEXT | State |
| postal_code | TEXT | Postal code |
| region | TEXT | East / West / Central / South |
| product_id | TEXT | Product identifier |
| category | TEXT | Furniture / Office Supplies / Technology |
| sub_category | TEXT | Product sub-category |
| product_name | TEXT | Full product name |
| sales | REAL | Line-item total after discount |
| quantity | INTEGER | Units sold |
| discount | REAL | Discount fraction (0.0–1.0) |
| profit | REAL | Net profit on the line item |

### `returns` table
| Column | Type | Description |
|--------|------|-------------|
| returned | TEXT | "Yes" if returned |
| order_id | TEXT | Foreign key to orders |

### `people` table
| Column | Type | Description |
|--------|------|-------------|
| person | TEXT | Sales representative name |
| region | TEXT | Region covered |

---

## 🧹 Data Cleaning Methodology

| Issue | Strategy |
|-------|----------|
| NULL text values | Retained — semantically meaningful in LEFT JOINs |
| Numeric type coercion | CAST in SQL; `pd.to_numeric(errors='coerce')` in Pandas |
| Date parsing | ISO 8601 TEXT in SQLite; `pd.to_datetime()` in Pandas |
| Whitespace in ship_mode | `TRIM(UPPER(ship_mode))` applied in analytical query |
| Duplicate rows | Detected and reported; not silently deleted |
| Negative profit margins | **Preserved** — legitimate business data |
| Division by zero | Guarded with `CASE WHEN ... != 0` in SQL and `if != 0` in Python |

---

## 📊 Analysis Performed

| Section | Description |
|---------|-------------|
| A. Sales Performance | Revenue, profit, margin, orders, units sold |
| B. Top Performance | Top 10 products by sales/qty; top 10 customers |
| C. Geographic | State, city, region — sales and profit |
| D. Category | Category and sub-category profitability |
| E. Reps | Per-rep totals and category breakdown |
| F. Returns | Return rates at product and category level |
| G. Segments | Region × Segment cross-tabulation |
| H. Shipping | Duration stats by mode; return rates by mode |
| I. Discounts | Binned discount ranges; threshold analysis |

---

## 📈 Visualizations

| # | Chart | Type |
|---|-------|------|
| 1 | Total sales by state | Horizontal bar |
| 2 | Sales by category | Grouped bar |
| 3 | Sales trends over time | Dual-axis line |
| 4 | Sales by region | Donut pie |
| 5 | Top 10 products | Horizontal bar |
| 6 | Discount vs Profit Margin | Scatter + trend line |
| 7 | Profit by sub-category | Horizontal bar (pos/neg) |
| 8 | Sales rep performance | Grouped bar |
| 9 | Return rates by category | Bar |
| 10 | Shipping duration by mode | Box plot |

All charts saved to `output/visualizations/` as PNG at 150 DPI.

---

## 🚀 Installation & Execution

### 1. Clone / Navigate to project

```bash
cd sales-performance-analysis
```

### 2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Place real dataset files

If you have the official Tableau Sample Superstore dataset:

```
data/raw/Orders.csv
data/raw/Returns.csv
data/raw/People.csv
```

If not provided, the pipeline will **automatically generate a realistic synthetic dataset** on first run.

### 5. Run the full pipeline

```bash
python main.py
```

This executes all phases: DB init → ingestion → cleaning → analysis → visualizations → reports.

### 6. Launch the interactive dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser.

### 7. Run automated tests

```bash
python -m pytest tests/ -v
```

---

## 📁 Output Files

After running `python main.py`, the following are generated:

```
output/
├── visualizations/
│   ├── 01_sales_by_state.png
│   ├── 02_sales_by_category.png
│   ├── 03_sales_trend.png
│   ├── 04_sales_by_region.png
│   ├── 05_top_products.png
│   ├── 06_discount_vs_margin.png
│   ├── 07_profit_by_subcategory.png
│   ├── 08_rep_performance.png
│   ├── 09_return_rates_by_category.png
│   └── 10_shipping_duration.png
├── reports/
│   ├── executive_summary.txt
│   └── sales_analysis_report.xlsx
└── exports/
    ├── kpi_summary.csv
    ├── top_products_by_sales.csv
    ├── geo_by_state.csv
    └── ... (13 CSV files total)
```

---

## 💡 Key Business Insights

> All insights are dynamically computed from the actual dataset. Run `python main.py` to generate the executive summary with specific numbers.

The system provides evidence-backed insights on:
- Which states and regions generate the most revenue vs. profit
- Which product sub-categories are loss-making despite high sales
- The discount threshold beyond which margin erosion outweighs volume gains
- Products with statistically high return rates
- Sales representative performance comparison by region and category
- Shipping mode efficiency and its correlation with return rates

---

## 🔮 Future Improvements

1. **Real-time data ingestion** — Replace CSV pipeline with database connectors (PostgreSQL, BigQuery).
2. **Machine learning** — Churn prediction, demand forecasting, return probability scoring.
3. **REST API** — Expose analytical endpoints via FastAPI for integration with BI tools.
4. **Scheduled reports** — Automate weekly/monthly report generation with email delivery.
5. **Geospatial maps** — Add choropleth maps for state-level visualization.
6. **A/B discount testing** — Design and analyze discount experiments statistically.
7. **Customer lifetime value** — Model CLV per segment and region.

---

## 👨‍💻 Project Structure

```
sales-performance-analysis/
├── data/
│   ├── raw/              # Input CSV files
│   └── processed/        # (reserved for derived data)
├── database/
│   └── sales.db          # SQLite database
├── src/
│   ├── database.py       # DB connection & schema
│   ├── ingestion.py      # CSV → SQLite ingestion
│   ├── data_cleaning.py  # Cleaning pipeline
│   ├── sql_queries.py    # SQL query constants
│   ├── analysis.py       # SalesAnalyzer class
│   ├── visualizations.py # Chart generation
│   └── reporting.py      # Reports & exports
├── dashboard/
│   └── app.py            # Streamlit BI dashboard
├── sql/
│   ├── schema.sql        # Table definitions
│   ├── cleaning.sql      # Cleaning queries
│   └── analysis.sql      # Master JOIN query
├── output/
│   ├── reports/          # Excel + executive summary
│   ├── visualizations/   # PNG charts
│   └── exports/          # CSV exports
├── tests/
│   ├── test_ingestion.py
│   ├── test_cleaning.py
│   └── test_analysis.py
├── main.py               # Pipeline entry point
├── requirements.txt
├── pyproject.toml        # pytest configuration
├── .gitignore
└── README.md
```

---

*Built as a portfolio-quality data engineering and analytics project demonstrating end-to-end data pipeline design, SQL mastery, Pandas analysis, and professional data visualization.*
