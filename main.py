"""
main.py — End-to-End Pipeline Entry Point
Sales Performance Analysis System

Usage:
    python main.py

Executes all phases sequentially:
  Phase 1: Database initialization
  Phase 2: Data ingestion (download + CSV → SQLite)
  Phase 3: Data cleaning and quality audit
  Phase 4: SQL → Pandas data transfer
  Phase 5: Comprehensive data analysis
  Phase 6: Visualization generation
  Phase 7: Report and export generation
"""

import logging
import sys
import time
from pathlib import Path

# ── Logging setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", mode="w"),
    ],
)
logger = logging.getLogger("main")

# ── Path setup ────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from database import connect_db, execute_schema
from ingestion import run_ingestion
from data_cleaning import run_cleaning_pipeline
from analysis import SalesAnalyzer
from visualizations import Visualizer
from reporting import run_reporting


def banner(phase: int, title: str):
    """Print a formatted phase banner."""
    print(f"\n{'='*70}")
    print(f"  PHASE {phase}: {title.upper()}")
    print(f"{'='*70}")


def main() -> int:
    """
    Execute the full end-to-end data pipeline.

    Returns:
        0 on success, 1 on failure.
    """
    start_time = time.time()
    print("\n" + "█" * 70)
    print("  SALES PERFORMANCE ANALYSIS AND REPORTING SYSTEM")
    print("  Retail Analytics Pipeline — Sample Superstore Dataset")
    print("█" * 70)

    # ── Phase 1: Database Initialization ─────────────────────
    banner(1, "Database Initialization")
    try:
        conn = connect_db()
        execute_schema(conn)
        logger.info("✅ Database initialized successfully.")
    except Exception as exc:
        logger.error("❌ Database initialization failed: %s", exc)
        return 1

    # ── Phase 2: Data Ingestion ───────────────────────────────
    banner(2, "Data Ingestion (Download + CSV → SQLite)")
    try:
        counts = run_ingestion(conn)
        logger.info("✅ Ingestion complete: %s", counts)
        for table, count in counts.items():
            print(f"   Table '{table}': {count:,} rows")
    except Exception as exc:
        logger.error("❌ Ingestion failed: %s", exc)
        return 1

    # ── Phase 3: Data Cleaning ────────────────────────────────
    banner(3, "Data Cleaning & Quality Audit (SQL)")
    try:
        cleaning_report = run_cleaning_pipeline(conn)
        logger.info("✅ Cleaning pipeline complete.")
        for table in ["orders", "returns", "people"]:
            info = cleaning_report.get(table, {})
            print(f"   {table:<10} | Rows: {info.get('row_count', 0):>7,} | "
                  f"NULLs: {info.get('total_nulls', 0):>5,}")
        dup = cleaning_report.get("duplicates", {})
        print(f"   Duplicates — Orders: {dup.get('orders_duplicates', 0)}, "
              f"Returns: {dup.get('returns_duplicates', 0)}, "
              f"People: {dup.get('people_duplicates', 0)}")
    except Exception as exc:
        logger.error("❌ Cleaning pipeline failed: %s", exc)
        return 1

    # ── Phase 4: SQL → Pandas ─────────────────────────────────
    banner(4, "SQL → Pandas Data Transfer")
    try:
        from database import get_analytical_dataset
        import pandas as pd

        df = get_analytical_dataset(conn)
        # Parse dates and compute shipping duration
        for col in ["order_date", "ship_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        if "order_date" in df.columns and "ship_date" in df.columns:
            df["shipping_duration"] = (df["ship_date"] - df["order_date"]).dt.days
        for col in ["sales", "profit", "quantity", "discount", "unit_price", "profit_margin"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "order_date" in df.columns:
            df["year_month"] = df["order_date"].dt.to_period("M").astype(str)

        logger.info("✅ Analytical DataFrame loaded: %d rows × %d columns", len(df), len(df.columns))
        print(f"   Rows: {len(df):,} | Columns: {len(df.columns)}")
        print(f"   Missing values: {df.isnull().sum().sum():,}")
        print(f"   Total Sales (Pandas): ${df['sales'].sum():,.2f}")
        print(f"   Total Profit (Pandas): ${df['profit'].sum():,.2f}")
    except Exception as exc:
        logger.error("❌ SQL → Pandas transfer failed: %s", exc)
        return 1

    # ── Phase 5: Analysis ─────────────────────────────────────
    banner(5, "Comprehensive Sales Analysis")
    try:
        analyzer = SalesAnalyzer(df)
        results = analyzer.run_all()
        kpis = results["kpis"]
        print(f"   Total Sales    : ${kpis['total_sales']:>14,.2f}")
        print(f"   Total Profit   : ${kpis['total_profit']:>14,.2f}")
        print(f"   Total Orders   : {kpis['total_orders']:>14,}")
        print(f"   Profit Margin  : {kpis['overall_profit_margin']:>14.2%}")
        print(f"   Return Rate    : {kpis['return_rate']:>14.2%}")
        disc = results["discounts"]
        print(f"   Discount Threshold: {disc['threshold'] or 'None identified'}")
        logger.info("✅ Analysis complete.")
    except Exception as exc:
        logger.error("❌ Analysis failed: %s", exc)
        return 1

    # ── Phase 6: Visualizations ───────────────────────────────
    banner(6, "Generating Visualizations (10 Charts)")
    try:
        viz = Visualizer(df, results)
        chart_paths = viz.generate_all()
        success = sum(1 for v in chart_paths.values() if v)
        print(f"   Generated {success}/{len(chart_paths)} charts successfully.")
        for name, path in chart_paths.items():
            status = "✅" if path else "❌"
            print(f"   {status} {name}: {path}")
        logger.info("✅ Visualizations complete: %d/%d", success, len(chart_paths))
    except Exception as exc:
        logger.error("❌ Visualization generation failed: %s", exc)
        return 1

    # ── Phase 7: Reporting ────────────────────────────────────
    banner(7, "Report & Export Generation")
    try:
        report_output = run_reporting(results, df)
        csv_count = len(report_output.get("csv_exports", {}))
        print(f"   CSV exports: {csv_count} files")
        print(f"   Excel workbook: {report_output.get('excel_workbook', 'N/A')}")
        print(f"   Executive summary: {report_output.get('executive_summary', 'N/A')}")
        logger.info("✅ Reporting complete.")
    except Exception as exc:
        logger.error("❌ Reporting failed: %s", exc)
        return 1

    # ── Closing ───────────────────────────────────────────────
    from database import close_db
    close_db(conn)

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"  ✅ PIPELINE COMPLETE — Total time: {elapsed:.1f}s")
    print(f"  Dashboard: streamlit run dashboard/app.py")
    print(f"  Tests:     python -m pytest tests/ -v")
    print(f"{'='*70}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
