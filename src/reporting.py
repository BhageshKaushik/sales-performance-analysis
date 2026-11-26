"""
reporting.py — Automated Report and Export Generation
Sales Performance Analysis System

Generates:
- CSV exports of all key analytical DataFrames
- Multi-sheet Excel workbook
- Executive summary text report
"""

import logging
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "output" / "reports"
EXPORTS_DIR = PROJECT_ROOT / "output" / "exports"


def _ensure_dirs() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_csv_exports(results: dict) -> dict:
    """
    Export key analysis DataFrames as CSV files.

    Args:
        results: Results dict from SalesAnalyzer.run_all().

    Returns:
        dict of filename -> Path for each exported CSV.
    """
    _ensure_dirs()
    exports = {}

    csv_tables = {
        "kpi_summary": pd.DataFrame([results["kpis"]]),
        "top_products_by_sales": results["top_products_sales"],
        "top_products_by_quantity": results["top_products_qty"],
        "top_customers": results["top_customers"],
        "geo_by_state": results["geo"]["by_state"],
        "geo_by_region": results["geo"]["by_region"],
        "geo_by_city": results["geo"]["by_city"].head(50),
        "category_summary": results["category"]["by_category"],
        "subcategory_summary": results["category"]["by_sub_category"],
        "rep_performance": results["reps"]["by_rep"],
        "rep_by_category": results["reps"]["by_rep_category"],
        "return_by_category": results["returns"]["by_category"],
        "high_return_products": results["returns"]["high_return_products"],
        "shipping_stats": results["product_shipping"]["shipping_stats"],
        "product_performance": results["product_shipping"]["product_performance"],
        "discount_analysis": results["discounts"]["by_discount_range"],
    }

    for name, df in csv_tables.items():
        if df is None or (hasattr(df, "empty") and df.empty):
            logger.warning("Skipping empty CSV export: %s", name)
            continue
        path = EXPORTS_DIR / f"{name}.csv"
        df.to_csv(path, index=False, float_format="%.4f")
        exports[name] = path
        logger.info("Exported CSV: %s (%d rows)", name, len(df))

    return exports


def generate_excel_workbook(results: dict, df: Optional[pd.DataFrame] = None) -> Path:
    """
    Generate a multi-sheet Excel workbook with all key analyses.

    Args:
        results: Results dict from SalesAnalyzer.run_all().
        df: Optional full analytical DataFrame (for raw data sheet).

    Returns:
        Path to the generated Excel file.
    """
    _ensure_dirs()
    path = REPORTS_DIR / "sales_analysis_report.xlsx"

    sheets = {
        "KPI Summary": pd.DataFrame([results["kpis"]]),
        "Top Products": results["top_products_sales"],
        "Top Customers": results["top_customers"],
        "Geo by State": results["geo"]["by_state"],
        "Geo by Region": results["geo"]["by_region"],
        "Categories": results["category"]["by_category"],
        "Sub-Categories": results["category"]["by_sub_category"],
        "Reps": results["reps"]["by_rep"],
        "Rep by Category": results["reps"]["by_rep_category"],
        "Returns": results["returns"]["by_category"],
        "High Return Products": results["returns"]["high_return_products"],
        "Shipping Stats": results["product_shipping"]["shipping_stats"],
        "Discount Analysis": results["discounts"]["by_discount_range"],
    }

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        workbook = writer.book
        # Formats
        header_fmt = workbook.add_format({
            "bold": True,
            "bg_color": "#1E3A5F",
            "font_color": "white",
            "border": 1,
            "align": "center",
        })
        money_fmt = workbook.add_format({"num_format": "$#,##0.00"})
        pct_fmt = workbook.add_format({"num_format": "0.00%"})

        for sheet_name, sheet_df in sheets.items():
            if sheet_df is None or (hasattr(sheet_df, "empty") and sheet_df.empty):
                continue
            # Truncate sheet name to Excel limit (31 chars)
            sheet_name_safe = sheet_name[:31]
            sheet_df.to_excel(writer, sheet_name=sheet_name_safe, index=False, startrow=1)

            worksheet = writer.sheets[sheet_name_safe]
            # Write header with formatting
            for col_idx, col_name in enumerate(sheet_df.columns):
                worksheet.write(0, col_idx, col_name, header_fmt)
                # Auto-fit column width
                max_len = max(len(str(col_name)),
                              sheet_df[col_name].astype(str).str.len().max() if len(sheet_df) > 0 else 10)
                worksheet.set_column(col_idx, col_idx, min(max_len + 2, 40))

        logger.info("Excel workbook generated: %s", path)

    return path


def generate_executive_summary(results: dict, df: pd.DataFrame) -> Path:
    """
    Generate a detailed executive summary report as a text file.
    All conclusions are based on actual computed results.

    Args:
        results: Results dict from SalesAnalyzer.run_all().
        df: Full analytical DataFrame.

    Returns:
        Path to the generated summary file.
    """
    _ensure_dirs()
    path = REPORTS_DIR / "executive_summary.txt"

    kpis = results["kpis"]
    geo = results["geo"]
    cat = results["category"]
    reps = results["reps"]
    returns = results["returns"]
    discounts = results["discounts"]
    product_ship = results["product_shipping"]

    # Pull key facts
    best_state = geo["by_state"].iloc[0]["state"] if len(geo["by_state"]) > 0 else "N/A"
    best_state_sales = geo["by_state"].iloc[0]["total_sales"] if len(geo["by_state"]) > 0 else 0
    best_region = geo["by_region"].iloc[0]["region"] if len(geo["by_region"]) > 0 else "N/A"
    best_region_profit = geo["by_region"].iloc[0]["total_profit"] if len(geo["by_region"]) > 0 else 0

    best_cat = cat["best_category"]
    worst_cat = cat["worst_category"]

    best_subcat_row = cat["by_sub_category"].nlargest(1, "total_profit").iloc[0] if len(cat["by_sub_category"]) > 0 else None
    worst_subcat_row = cat["by_sub_category"].nsmallest(1, "total_profit").iloc[0] if len(cat["by_sub_category"]) > 0 else None

    top_rep_row = reps["by_rep"].iloc[0] if len(reps["by_rep"]) > 0 else None

    overall_rr = returns["overall_return_rate"]
    high_return = returns["high_return_products"]
    top_return_product = high_return.iloc[0]["product_name"] if len(high_return) > 0 else "N/A"
    top_return_rate = high_return.iloc[0]["return_rate"] if len(high_return) > 0 else 0

    disc_threshold = discounts["threshold"] or "No clear threshold identified"
    disc_evidence = discounts["threshold_evidence"]

    neg_profit_states = geo["high_sales_negative_profit"]
    underperformers = product_ship["underperforming_products"]

    ship_stats = product_ship["shipping_stats"]

    report_date = datetime.now().strftime("%B %d, %Y")

    lines = [
        "=" * 72,
        "SALES PERFORMANCE ANALYSIS — EXECUTIVE SUMMARY",
        "=" * 72,
        f"Report Generated: {report_date}",
        f"Dataset: Sample Superstore",
        "",
        "=" * 72,
        "1. OVERALL PERFORMANCE OVERVIEW",
        "=" * 72,
        f"  Total Revenue     : ${kpis['total_sales']:>14,.2f}",
        f"  Total Profit      : ${kpis['total_profit']:>14,.2f}",
        f"  Total Orders      : {kpis['total_orders']:>14,}",
        f"  Total Units Sold  : {kpis['total_quantity']:>14,}",
        f"  Avg Sales/Order   : ${kpis['avg_sales_per_order']:>14,.2f}",
        f"  Overall Profit Margin : {kpis['overall_profit_margin']:.2%}",
        f"  Total Returns     : {kpis['total_returned']:>14,}",
        f"  Overall Return Rate   : {kpis['return_rate']:.2%}",
        "",
        "=" * 72,
        "2. WHAT IS PERFORMING WELL",
        "=" * 72,
    ]

    lines += [
        f"  Best-Selling State: {best_state} (${best_state_sales:,.2f} in total sales)",
        f"  Most Profitable Region: {best_region} (${best_region_profit:,.2f} in profit)",
        f"  Best Performing Category: {best_cat}",
    ]
    if best_subcat_row is not None:
        lines.append(
            f"  Best Sub-Category: {best_subcat_row['sub_category']} "
            f"(Profit: ${best_subcat_row['total_profit']:,.2f})"
        )
    if top_rep_row is not None:
        lines.append(
            f"  Top Sales Representative: {top_rep_row['sales_rep']} "
            f"(Sales: ${top_rep_row['total_sales']:,.2f}, "
            f"Profit: ${top_rep_row['total_profit']:,.2f})"
        )

    lines += [
        "",
        "=" * 72,
        "3. UNDERPERFORMING PRODUCTS AND REGIONS",
        "=" * 72,
        f"  Worst Performing Category: {worst_cat}",
    ]
    if worst_subcat_row is not None:
        lines.append(
            f"  Worst Sub-Category: {worst_subcat_row['sub_category']} "
            f"(Profit: ${worst_subcat_row['total_profit']:,.2f})"
        )
    lines.append(
        f"  Products with Negative Adjusted Profit: {len(underperformers)}"
    )
    if len(neg_profit_states) > 0:
        states_list = ", ".join(neg_profit_states["state"].tolist())
        lines.append(
            f"  High-Sales States with Negative Profit: {states_list}"
        )

    lines += [
        "",
        "=" * 72,
        "4. DISCOUNT IMPACT ON PROFITABILITY",
        "=" * 72,
    ]
    disc_table = discounts["by_discount_range"]
    for _, row in disc_table.iterrows():
        margin_str = f"{row['profit_margin']:.2%}" if not (isinstance(row['profit_margin'], float) and np.isnan(row['profit_margin'])) else "N/A"
        lines.append(
            f"  {str(row['discount_range']):<12} | Sales: ${row['total_sales']:>12,.2f} | "
            f"Profit: ${row['total_profit']:>12,.2f} | Margin: {margin_str}"
        )
    lines += [
        "",
        f"  Critical Threshold: {disc_threshold}",
        f"  Evidence: {disc_evidence}",
        "",
        "=" * 72,
        "5. RETURN RATE ANALYSIS",
        "=" * 72,
        f"  Overall Return Rate: {overall_rr:.2%}",
        f"  Most Problematic Product: {top_return_product} (Return Rate: {top_return_rate:.2%})",
        "",
        "  Return Rates by Category:",
    ]
    for _, row in returns["by_category"].iterrows():
        lines.append(
            f"    {row['category']:<20} | {row['return_rate']:.2%} "
            f"({int(row['returned_orders'])} of {int(row['total_orders'])} orders)"
        )

    lines += [
        "",
        "=" * 72,
        "6. SHIPPING EFFICIENCY",
        "=" * 72,
    ]
    ship_overall = df.groupby("ship_mode")["shipping_duration"].agg(["mean", "median"]).reset_index()
    for _, row in ship_overall.iterrows():
        lines.append(
            f"  {str(row['ship_mode']):<20} | "
            f"Avg: {row['mean']:.1f} days | Median: {row['median']:.1f} days"
        )

    lines += [
        "",
        "=" * 72,
        "7. MANAGEMENT RECOMMENDATIONS",
        "=" * 72,
        "  1. DISCOUNT CONTROL: Cap discounts at the identified threshold.",
        "     Heavy discounts are eroding profit margins without sufficient",
        "     volume compensation. Implement discount approval workflows.",
        "",
        "  2. PRODUCT RETURNS: Investigate quality and packaging issues for",
        f"     products with return rates above {overall_rr:.2%} (overall average).",
        "     Review supplier agreements and implement post-return analysis.",
        "",
        f"  3. REGIONAL FOCUS: Invest further in {best_region} which shows",
        "     the strongest profit performance. Analyze what works in this",
        "     region and replicate best practices across underperforming areas.",
        "",
        f"  4. CATEGORY STRATEGY: {worst_cat} is underperforming on profit.",
        "     Review pricing strategy, supplier costs, and discount policies",
        "     specific to this category.",
        "",
        "  5. SHIPPING OPTIMIZATION: Analyze whether encouraging Standard Class",
        "     shipping (slower but lower cost) is impacting customer satisfaction",
        "     and return rates.",
        "",
        "=" * 72,
        "END OF EXECUTIVE SUMMARY",
        "=" * 72,
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Executive summary generated: %s", path)
    return path


def run_reporting(results: dict, df: pd.DataFrame) -> dict:
    """
    Main reporting entry point. Generates all reports and exports.

    Args:
        results: Results dict from SalesAnalyzer.run_all().
        df: Full analytical DataFrame.

    Returns:
        dict with paths to all generated files.
    """
    logger.info("=" * 60)
    logger.info("Running Report Generation")
    logger.info("=" * 60)

    output = {}
    output["csv_exports"] = generate_csv_exports(results)
    output["excel_workbook"] = generate_excel_workbook(results, df)
    output["executive_summary"] = generate_executive_summary(results, df)

    logger.info("Reporting complete.")
    return output
