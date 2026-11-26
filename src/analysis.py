"""
analysis.py — Pandas-based Sales Performance Analysis
Sales Performance Analysis System

SalesAnalyzer class providing all required analytical methods.
All results are computed dynamically from the actual dataset.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SalesAnalyzer:
    """
    Comprehensive sales performance analyzer operating on a cleaned DataFrame.

    The DataFrame is expected to have the schema produced by the SQL analytical
    JOIN query in sql/analysis.sql.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize the analyzer and compute shipping duration.

        Args:
            df: Cleaned, joined analytical DataFrame from SQL.
        """
        self.df = df.copy()
        self._prepare_dataframe()

    def _prepare_dataframe(self) -> None:
        """
        Post-load DataFrame preparation:
        - Parse date columns to datetime.
        - Compute shipping_duration in days.
        - Ensure numeric columns are correct dtype.
        """
        # Parse dates
        for col in ["order_date", "ship_date"]:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors="coerce")

        # Shipping duration in days (integer)
        if "order_date" in self.df.columns and "ship_date" in self.df.columns:
            self.df["shipping_duration"] = (
                self.df["ship_date"] - self.df["order_date"]
            ).dt.days

        # Ensure numeric types
        for col in ["sales", "profit", "quantity", "discount", "unit_price", "profit_margin"]:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        # Year-Month string for time series
        if "order_date" in self.df.columns:
            self.df["year_month"] = self.df["order_date"].dt.to_period("M").astype(str)

        logger.info("DataFrame prepared: %d rows, %d columns", len(self.df), len(self.df.columns))

    # ============================================================
    # A. Sales Performance KPIs
    # ============================================================

    def sales_performance(self) -> dict:
        """
        Compute top-level sales KPIs.

        Returns:
            dict with total_sales, total_quantity, total_profit,
            avg_sales_per_order, overall_profit_margin, total_orders.
        """
        df = self.df
        total_sales = df["sales"].sum()
        total_profit = df["profit"].sum()
        total_quantity = int(df["quantity"].sum())
        total_orders = df["order_id"].nunique()
        avg_sales_per_order = total_sales / total_orders if total_orders > 0 else 0.0
        overall_profit_margin = (
            total_profit / total_sales if total_sales != 0 else 0.0
        )
        total_returned = int(df["is_returned"].sum()) if "is_returned" in df.columns else 0
        return_rate = total_returned / total_orders if total_orders > 0 else 0.0

        result = {
            "total_sales": round(total_sales, 2),
            "total_profit": round(total_profit, 2),
            "total_quantity": total_quantity,
            "total_orders": total_orders,
            "avg_sales_per_order": round(avg_sales_per_order, 2),
            "overall_profit_margin": round(overall_profit_margin, 4),
            "total_returned": total_returned,
            "return_rate": round(return_rate, 4),
        }
        logger.info("Sales KPIs computed: %s", result)
        return result

    def verify_counts(self) -> dict:
        """
        Verification report for data integrity checks.

        Returns:
            dict with row_count, missing_values, and KPI summary.
        """
        df = self.df
        result = {
            "row_count": len(df),
            "missing_values": df.isnull().sum().to_dict(),
            "total_sales": round(df["sales"].sum(), 2),
            "total_quantity": int(df["quantity"].sum()),
            "total_profit": round(df["profit"].sum(), 2),
        }
        logger.info("Verification: rows=%d, total_sales=%.2f", result["row_count"], result["total_sales"])
        return result

    # ============================================================
    # B. Top Performance
    # ============================================================

    def top_products_by_sales(self, n: int = 10) -> pd.DataFrame:
        """Top N products ranked by total sales."""
        return (
            self.df.groupby("product_name")["sales"]
            .sum()
            .reset_index()
            .rename(columns={"sales": "total_sales"})
            .nlargest(n, "total_sales")
            .reset_index(drop=True)
        )

    def top_products_by_quantity(self, n: int = 10) -> pd.DataFrame:
        """Top N products ranked by total quantity sold."""
        return (
            self.df.groupby("product_name")["quantity"]
            .sum()
            .reset_index()
            .rename(columns={"quantity": "total_quantity"})
            .nlargest(n, "total_quantity")
            .reset_index(drop=True)
        )

    def top_customers_by_sales(self, n: int = 10) -> pd.DataFrame:
        """Top N customers ranked by total sales."""
        return (
            self.df.groupby(["customer_id", "customer_name"])["sales"]
            .sum()
            .reset_index()
            .rename(columns={"sales": "total_sales"})
            .nlargest(n, "total_sales")
            .reset_index(drop=True)
        )

    # ============================================================
    # C. Geographical Analysis
    # ============================================================

    def geo_analysis(self) -> dict:
        """
        Sales and profit aggregated at state, city, and region levels.

        Returns:
            dict with keys 'by_state', 'by_city', 'by_region',
            and 'high_sales_negative_profit'.
        """
        def _agg(group_col):
            return (
                self.df.groupby(group_col)
                .agg(
                    total_sales=("sales", "sum"),
                    total_profit=("profit", "sum"),
                    order_count=("order_id", "nunique"),
                )
                .reset_index()
                .sort_values("total_sales", ascending=False)
            )

        by_state = _agg("state")
        by_city = _agg("city")
        by_region = _agg("region")

        # High-sales locations with negative profit
        threshold = by_state["total_sales"].quantile(0.75)
        high_sales_negative = by_state[
            (by_state["total_sales"] >= threshold) & (by_state["total_profit"] < 0)
        ]

        return {
            "by_state": by_state,
            "by_city": by_city,
            "by_region": by_region,
            "high_sales_negative_profit": high_sales_negative,
        }

    # ============================================================
    # D. Category Analysis
    # ============================================================

    def category_analysis(self) -> dict:
        """
        Sales and profit by category and sub-category.

        Returns:
            dict with 'by_category', 'by_sub_category',
            'best_category', 'worst_category'.
        """
        by_cat = (
            self.df.groupby("category")
            .agg(
                total_sales=("sales", "sum"),
                total_profit=("profit", "sum"),
                total_quantity=("quantity", "sum"),
            )
            .reset_index()
        )
        by_cat["profit_margin"] = by_cat.apply(
            lambda r: r["total_profit"] / r["total_sales"]
            if r["total_sales"] != 0 else np.nan,
            axis=1,
        )

        by_subcat = (
            self.df.groupby(["category", "sub_category"])
            .agg(
                total_sales=("sales", "sum"),
                total_profit=("profit", "sum"),
                total_quantity=("quantity", "sum"),
            )
            .reset_index()
        )
        by_subcat["profit_margin"] = by_subcat.apply(
            lambda r: r["total_profit"] / r["total_sales"]
            if r["total_sales"] != 0 else np.nan,
            axis=1,
        )

        best = by_cat.loc[by_cat["total_profit"].idxmax(), "category"]
        worst = by_cat.loc[by_cat["total_profit"].idxmin(), "category"]

        return {
            "by_category": by_cat,
            "by_sub_category": by_subcat,
            "best_category": best,
            "worst_category": worst,
        }

    # ============================================================
    # E. Sales Representative Analysis
    # ============================================================

    def rep_analysis(self) -> dict:
        """
        Sales representative performance analysis.

        Returns:
            dict with 'by_rep', 'by_rep_category', 'strongest_category_per_rep'.
        """
        by_rep = (
            self.df.groupby("sales_rep")
            .agg(
                total_sales=("sales", "sum"),
                total_profit=("profit", "sum"),
                total_quantity=("quantity", "sum"),
                order_count=("order_id", "nunique"),
            )
            .reset_index()
            .sort_values("total_sales", ascending=False)
        )

        by_rep_cat = (
            self.df.groupby(["sales_rep", "category"])
            .agg(
                total_sales=("sales", "sum"),
                total_quantity=("quantity", "sum"),
            )
            .reset_index()
        )

        # Strongest category per rep (by total sales)
        strongest = (
            by_rep_cat.loc[
                by_rep_cat.groupby("sales_rep")["total_sales"].idxmax()
            ]
            [["sales_rep", "category", "total_sales"]]
            .rename(columns={"category": "strongest_category"})
            .reset_index(drop=True)
        )

        return {
            "by_rep": by_rep,
            "by_rep_category": by_rep_cat,
            "strongest_category_per_rep": strongest,
        }

    # ============================================================
    # F. Return Analysis
    # ============================================================

    def return_analysis(self) -> dict:
        """
        Analyze return rates at product, category, and overall levels.

        Returns:
            dict with 'total_returned', 'overall_return_rate',
            'by_product', 'by_category', 'high_return_products'.
        """
        df = self.df
        total_orders = df["order_id"].nunique()
        total_returned = int(df.groupby("order_id")["is_returned"].max().sum())
        overall_return_rate = total_returned / total_orders if total_orders > 0 else 0.0

        # Return rate by product
        prod_grp = df.groupby("product_name").agg(
            total_orders=("order_id", "nunique"),
            returned_orders=("is_returned", "max"),
        )
        # Recalculate properly: group by product+order first
        order_product = df.groupby(["product_name", "order_id"])["is_returned"].max().reset_index()
        prod_return = order_product.groupby("product_name").agg(
            total_orders=("order_id", "nunique"),
            returned_orders=("is_returned", "sum"),
        ).reset_index()
        prod_return["return_rate"] = (
            prod_return["returned_orders"] / prod_return["total_orders"]
        )
        prod_return = prod_return.sort_values("return_rate", ascending=False)

        # Return rate by category
        cat_order = df.groupby(["category", "order_id"])["is_returned"].max().reset_index()
        cat_return = cat_order.groupby("category").agg(
            total_orders=("order_id", "nunique"),
            returned_orders=("is_returned", "sum"),
        ).reset_index()
        cat_return["return_rate"] = (
            cat_return["returned_orders"] / cat_return["total_orders"]
        )

        # High return rate products (above mean + 1 std)
        threshold = prod_return["return_rate"].mean() + prod_return["return_rate"].std()
        high_return = prod_return[prod_return["return_rate"] > threshold].head(20)

        return {
            "total_returned": total_returned,
            "overall_return_rate": round(overall_return_rate, 4),
            "by_product": prod_return,
            "by_category": cat_return,
            "high_return_products": high_return,
        }

    # ============================================================
    # G. Regional and Customer Segment Analysis
    # ============================================================

    def segment_analysis(self) -> dict:
        """
        Customer segment distribution by region and cross-tabulation.

        Returns:
            dict with 'by_region_rep', 'segment_by_region', 'crosstab'.
        """
        by_region_rep = (
            self.df.groupby(["region", "sales_rep"])
            .agg(
                total_sales=("sales", "sum"),
                total_profit=("profit", "sum"),
            )
            .reset_index()
        )

        seg_by_region = (
            self.df.groupby(["region", "segment"])["order_id"]
            .nunique()
            .reset_index()
            .rename(columns={"order_id": "order_count"})
        )

        crosstab = pd.crosstab(self.df["region"], self.df["segment"])

        return {
            "by_region_rep": by_region_rep,
            "segment_by_region": seg_by_region,
            "crosstab": crosstab,
        }

    # ============================================================
    # H. Product Performance and Shipping Efficiency
    # ============================================================

    def product_shipping_analysis(self) -> dict:
        """
        Product-level metrics and shipping duration statistics.

        Returns:
            dict with 'product_performance', 'shipping_stats',
            'return_by_ship_mode', 'underperforming_products'.
        """
        df = self.df

        # Product-level aggregation
        order_product = df.groupby(["product_name", "order_id"])["is_returned"].max().reset_index()
        prod_ret = order_product.groupby("product_name").agg(
            returned_orders=("is_returned", "sum"),
            total_orders=("order_id", "nunique"),
        ).reset_index()
        prod_ret["product_return_rate"] = (
            prod_ret["returned_orders"] / prod_ret["total_orders"]
        )

        prod_perf = (
            df.groupby("product_name")
            .agg(
                total_sales=("sales", "sum"),
                total_quantity=("quantity", "sum"),
                total_profit=("profit", "sum"),
            )
            .reset_index()
        )
        prod_perf = prod_perf.merge(prod_ret[["product_name", "product_return_rate"]],
                                     on="product_name", how="left")
        prod_perf["adjusted_profit"] = prod_perf["total_profit"] * (
            1 - prod_perf["product_return_rate"].fillna(0)
        )

        # Underperforming: negative adjusted profit
        underperforming = prod_perf[prod_perf["adjusted_profit"] < 0].sort_values("adjusted_profit")

        # Shipping duration stats by ship_mode and region
        ship_stats = (
            df.groupby(["ship_mode", "region"])["shipping_duration"]
            .agg(["mean", "median", "std"])
            .reset_index()
            .rename(columns={"mean": "avg_duration", "median": "median_duration", "std": "std_duration"})
        )

        # Return rate by ship_mode and region
        order_ship = df.groupby(["ship_mode", "region", "order_id"])["is_returned"].max().reset_index()
        ret_ship = order_ship.groupby(["ship_mode", "region"]).agg(
            returned_orders=("is_returned", "sum"),
            total_orders=("order_id", "nunique"),
        ).reset_index()
        ret_ship["return_rate"] = ret_ship["returned_orders"] / ret_ship["total_orders"]

        return {
            "product_performance": prod_perf,
            "shipping_stats": ship_stats,
            "return_by_ship_mode": ret_ship,
            "underperforming_products": underperforming,
        }

    # ============================================================
    # I. Discount Analysis
    # ============================================================

    def discount_analysis(self) -> dict:
        """
        Analyze the impact of discounts on sales volume and profit margin.

        Groups discounts into ranges and computes totals and margins.
        Identifies the discount threshold beyond which additional volume
        does not compensate for margin erosion — determined from actual data.

        Returns:
            dict with 'by_discount_range', 'threshold', 'threshold_evidence'.
        """
        df = self.df.copy()

        # Define discount ranges
        bins = [-0.001, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.01]
        labels = ["No Discount", "1-10%", "11-20%", "21-30%", "31-40%", "41-50%", "51%+"]
        df["discount_range"] = pd.cut(df["discount"], bins=bins, labels=labels)

        grouped = (
            df.groupby("discount_range", observed=False)
            .agg(
                total_sales=("sales", "sum"),
                total_profit=("profit", "sum"),
                total_quantity=("quantity", "sum"),
                order_count=("order_id", "nunique"),
            )
            .reset_index()
        )
        grouped["profit_margin"] = grouped.apply(
            lambda r: r["total_profit"] / r["total_sales"]
            if r["total_sales"] != 0 else np.nan,
            axis=1,
        )

        # Determine threshold: first discount range where profit_margin turns negative
        # and stays negative for all higher ranges
        threshold = None
        threshold_evidence = "No clear threshold identified."

        ordered_labels = labels
        margins = dict(zip(grouped["discount_range"].astype(str), grouped["profit_margin"]))

        # Find first bucket with negative margin
        prev_margin = None
        for label in ordered_labels:
            m = margins.get(label)
            if m is None or np.isnan(m):
                continue
            if m < 0:
                if threshold is None:
                    threshold = label
                    threshold_evidence = (
                        f"Profit margin turns negative at discount range '{label}' "
                        f"(margin = {m:.2%}). "
                        f"Previous range margin was {prev_margin:.2%} if applicable."
                        if prev_margin is not None
                        else f"Profit margin turns negative at discount range '{label}' "
                             f"(margin = {m:.2%})."
                    )
                    break
            prev_margin = m

        if threshold is None:
            # No range goes negative; find where margin drops most steeply
            grouped_sorted = grouped.dropna(subset=["profit_margin"]).sort_values("discount_range")
            if len(grouped_sorted) >= 2:
                grouped_sorted["margin_drop"] = grouped_sorted["profit_margin"].diff().abs()
                max_drop_idx = grouped_sorted["margin_drop"].idxmax()
                if max_drop_idx is not None:
                    threshold = str(grouped_sorted.loc[max_drop_idx, "discount_range"])
                    drop_val = grouped_sorted.loc[max_drop_idx, "margin_drop"]
                    threshold_evidence = (
                        f"No discount range produces a negative margin. "
                        f"The steepest margin drop ({drop_val:.2%}) occurs at '{threshold}', "
                        f"suggesting this is the critical inflection point."
                    )

        return {
            "by_discount_range": grouped,
            "threshold": threshold,
            "threshold_evidence": threshold_evidence,
        }

    # ============================================================
    # Convenience: run all analyses
    # ============================================================

    def run_all(self) -> dict:
        """Run all analysis methods and return a combined results dict."""
        logger.info("Running full analysis suite...")
        return {
            "kpis": self.sales_performance(),
            "verification": self.verify_counts(),
            "top_products_sales": self.top_products_by_sales(),
            "top_products_qty": self.top_products_by_quantity(),
            "top_customers": self.top_customers_by_sales(),
            "geo": self.geo_analysis(),
            "category": self.category_analysis(),
            "reps": self.rep_analysis(),
            "returns": self.return_analysis(),
            "segments": self.segment_analysis(),
            "product_shipping": self.product_shipping_analysis(),
            "discounts": self.discount_analysis(),
        }
