"""
visualizations.py — Professional Chart Generation
Sales Performance Analysis System

Creates all 10 required visualizations using Matplotlib and Seaborn.
Charts are saved as PNG files in output/visualizations/.
"""

import logging
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for file saving
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIZ_DIR = PROJECT_ROOT / "output" / "visualizations"

# ============================================================
# Design System
# ============================================================

PALETTE = {
    "primary": "#1E3A5F",
    "secondary": "#2E86AB",
    "accent": "#00C2CC",
    "positive": "#27AE60",
    "negative": "#E74C3C",
    "warning": "#F39C12",
    "neutral": "#7F8C8D",
    "background": "#F8FAFC",
    "text": "#2C3E50",
}

CHART_COLORS = [
    "#2E86AB", "#1E3A5F", "#00C2CC", "#27AE60", "#F39C12",
    "#E74C3C", "#8E44AD", "#16A085", "#D35400", "#2C3E50",
]

STYLE_PARAMS = {
    "figure.facecolor": PALETTE["background"],
    "axes.facecolor": "white",
    "axes.edgecolor": "#DEE2E6",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#DEE2E6",
    "grid.linestyle": "--",
    "grid.alpha": 0.6,
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 150,
}


def apply_style():
    """Apply global matplotlib style parameters."""
    plt.rcParams.update(STYLE_PARAMS)


def save_chart(fig: plt.Figure, filename: str) -> Path:
    """Save figure to output/visualizations/ directory."""
    VIZ_DIR.mkdir(parents=True, exist_ok=True)
    path = VIZ_DIR / filename
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=PALETTE["background"])
    plt.close(fig)
    logger.info("Saved chart: %s", path)
    return path


class Visualizer:
    """
    Generates all required visualizations for the Sales Analysis project.
    """

    def __init__(self, df: pd.DataFrame, results: dict):
        """
        Args:
            df: Cleaned analytical DataFrame.
            results: Results dict from SalesAnalyzer.run_all().
        """
        self.df = df
        self.results = results
        apply_style()

    # ============================================================
    # 1. Total Sales by State (Horizontal Bar)
    # ============================================================

    def chart_sales_by_state(self) -> Path:
        """Bar chart — Total sales by state (top 20)."""
        geo = self.results["geo"]["by_state"].head(20)

        fig, ax = plt.subplots(figsize=(12, 9))
        bars = ax.barh(
            geo["state"][::-1], geo["total_sales"][::-1],
            color=CHART_COLORS[1], edgecolor="white", linewidth=0.5,
        )
        # Color bars by profit
        profits = geo["total_profit"][::-1].values
        for bar, profit in zip(bars, profits):
            bar.set_facecolor(PALETTE["positive"] if profit >= 0 else PALETTE["negative"])
            bar.set_alpha(0.85)

        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e3:.0f}K"))
        ax.set_xlabel("Total Sales (USD)")
        ax.set_title("Total Sales by State — Top 20 States\n"
                     "(Green = Profitable | Red = Loss-making)", pad=15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Annotate values
        for bar in bars:
            width = bar.get_width()
            ax.text(width + max(geo["total_sales"]) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"${width/1e3:.1f}K",
                    va="center", ha="left", fontsize=7.5)

        fig.tight_layout()
        return save_chart(fig, "01_sales_by_state.png")

    # ============================================================
    # 2. Sales by Category (Bar)
    # ============================================================

    def chart_sales_by_category(self) -> Path:
        """Bar chart — Sales and profit by category."""
        cat_data = self.results["category"]["by_category"]

        x = np.arange(len(cat_data))
        width = 0.35

        fig, ax = plt.subplots(figsize=(9, 6))
        bars1 = ax.bar(x - width / 2, cat_data["total_sales"], width,
                       label="Total Sales", color=CHART_COLORS[0], alpha=0.9)
        bars2 = ax.bar(x + width / 2, cat_data["total_profit"], width,
                       label="Total Profit",
                       color=[PALETTE["positive"] if p >= 0 else PALETTE["negative"]
                              for p in cat_data["total_profit"]],
                       alpha=0.9)

        ax.set_xticks(x)
        ax.set_xticklabels(cat_data["category"], fontsize=11)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1e3:.0f}K"))
        ax.set_ylabel("Amount (USD)")
        ax.set_title("Sales and Profit by Category", pad=15)
        ax.legend()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()
        return save_chart(fig, "02_sales_by_category.png")

    # ============================================================
    # 3. Sales Trend Over Time (Line)
    # ============================================================

    def chart_sales_trend(self) -> Path:
        """Line chart — Monthly sales and profit trends."""
        df = self.df.copy()
        df["year_month"] = pd.to_datetime(df["order_date"]).dt.to_period("M")
        monthly = (
            df.groupby("year_month")
            .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
            .reset_index()
        )
        monthly["year_month"] = monthly["year_month"].astype(str)

        fig, ax1 = plt.subplots(figsize=(14, 6))

        color_sales = CHART_COLORS[0]
        color_profit = PALETTE["positive"]

        x = range(len(monthly))
        ax1.plot(x, monthly["total_sales"], color=color_sales, linewidth=2.5,
                 marker="o", markersize=4, label="Total Sales")
        ax1.fill_between(x, monthly["total_sales"], alpha=0.1, color=color_sales)
        ax1.set_ylabel("Sales (USD)", color=color_sales)
        ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1e3:.0f}K"))

        ax2 = ax1.twinx()
        ax2.plot(x, monthly["total_profit"], color=color_profit, linewidth=2,
                 linestyle="--", marker="s", markersize=3.5, label="Total Profit")
        ax2.set_ylabel("Profit (USD)", color=color_profit)
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1e3:.0f}K"))

        # X-axis ticks — show every 3rd month label
        step = max(1, len(monthly) // 12)
        ticks = list(x)[::step]
        ax1.set_xticks(ticks)
        ax1.set_xticklabels(monthly["year_month"].iloc[ticks], rotation=45, ha="right")

        ax1.set_title("Monthly Sales and Profit Trends", pad=15)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
        ax1.spines["top"].set_visible(False)

        fig.tight_layout()
        return save_chart(fig, "03_sales_trend.png")

    # ============================================================
    # 4. Sales by Region (Pie)
    # ============================================================

    def chart_sales_by_region(self) -> Path:
        """Pie chart — Sales distribution by region."""
        geo = self.results["geo"]["by_region"]

        fig, ax = plt.subplots(figsize=(8, 7))
        wedge_colors = CHART_COLORS[:len(geo)]
        wedges, texts, autotexts = ax.pie(
            geo["total_sales"],
            labels=geo["region"],
            autopct="%1.1f%%",
            colors=wedge_colors,
            startangle=140,
            pctdistance=0.75,
            wedgeprops=dict(edgecolor="white", linewidth=2),
        )
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight("bold")
        for at in autotexts:
            at.set_fontsize(9)
            at.set_color("white")

        centre_circle = plt.Circle((0, 0), 0.55, fc="white")
        ax.add_artist(centre_circle)
        ax.set_title("Sales Distribution by Region", pad=20, fontsize=14, fontweight="bold")

        # Legend with dollar values
        legend_labels = [
            f"{row['region']}: ${row['total_sales']/1e3:.0f}K"
            for _, row in geo.iterrows()
        ]
        ax.legend(wedges, legend_labels, loc="lower center",
                  bbox_to_anchor=(0.5, -0.08), ncol=2, fontsize=9)

        fig.tight_layout()
        return save_chart(fig, "04_sales_by_region.png")

    # ============================================================
    # 5. Top 10 Products by Sales (Bar)
    # ============================================================

    def chart_top_products(self) -> Path:
        """Horizontal bar — Top 10 products by total sales."""
        prods = self.results["top_products_sales"]

        fig, ax = plt.subplots(figsize=(12, 7))
        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(prods))]
        bars = ax.barh(prods["product_name"][::-1], prods["total_sales"][::-1],
                       color=colors[::-1], alpha=0.9, edgecolor="white")

        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1e3:.1f}K"))
        ax.set_xlabel("Total Sales (USD)")
        ax.set_title("Top 10 Products by Total Sales", pad=15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        for bar in bars:
            width = bar.get_width()
            ax.text(width + max(prods["total_sales"]) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"${width/1e3:.1f}K", va="center", ha="left", fontsize=8)

        fig.tight_layout()
        return save_chart(fig, "05_top_products.png")

    # ============================================================
    # 6. Discount vs Profit Margin (Scatter)
    # ============================================================

    def chart_discount_vs_margin(self) -> Path:
        """Scatter plot — Discount rate vs Profit Margin by category."""
        df = self.df.dropna(subset=["discount", "profit_margin"]).copy()

        fig, ax = plt.subplots(figsize=(10, 7))
        categories = df["category"].unique()
        for i, cat in enumerate(categories):
            sub = df[df["category"] == cat]
            ax.scatter(
                sub["discount"], sub["profit_margin"],
                alpha=0.4, s=15,
                color=CHART_COLORS[i % len(CHART_COLORS)],
                label=cat,
            )

        # Trend line
        z = np.polyfit(df["discount"].fillna(0), df["profit_margin"].fillna(0), 1)
        p = np.poly1d(z)
        x_line = np.linspace(0, df["discount"].max(), 100)
        ax.plot(x_line, p(x_line), color=PALETTE["negative"], linewidth=2,
                linestyle="--", label="Trend Line", zorder=5)

        ax.axhline(0, color=PALETTE["neutral"], linewidth=1.2, linestyle="-")
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        ax.set_xlabel("Discount Rate")
        ax.set_ylabel("Profit Margin")
        ax.set_title("Discount Rate vs Profit Margin by Category", pad=15)
        ax.legend(fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()
        return save_chart(fig, "06_discount_vs_margin.png")

    # ============================================================
    # 7. Profit by Sub-Category (Bar)
    # ============================================================

    def chart_profit_by_subcategory(self) -> Path:
        """Bar chart — Profit by sub-category, colored by positive/negative."""
        sub = (
            self.results["category"]["by_sub_category"]
            .sort_values("total_profit", ascending=True)
        )

        fig, ax = plt.subplots(figsize=(12, 9))
        colors = [PALETTE["positive"] if p >= 0 else PALETTE["negative"]
                  for p in sub["total_profit"]]
        bars = ax.barh(sub["sub_category"], sub["total_profit"],
                       color=colors, alpha=0.85, edgecolor="white")

        ax.axvline(0, color=PALETTE["text"], linewidth=1.0)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1e3:.0f}K"))
        ax.set_xlabel("Total Profit (USD)")
        ax.set_title("Profit by Sub-Category\n(Green = Profit | Red = Loss)", pad=15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()
        return save_chart(fig, "07_profit_by_subcategory.png")

    # ============================================================
    # 8. Sales Representative Performance (Bar)
    # ============================================================

    def chart_rep_performance(self) -> Path:
        """Grouped bar — Sales rep performance: sales and profit."""
        reps = self.results["reps"]["by_rep"]
        reps = reps.dropna(subset=["sales_rep"])
        if reps.empty:
            logger.warning("No sales rep data available; skipping chart 8.")
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(0.5, 0.5, "No sales rep data available", transform=ax.transAxes,
                    ha="center", va="center", fontsize=14)
            return save_chart(fig, "08_rep_performance.png")

        x = np.arange(len(reps))
        width = 0.35
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.bar(x - width / 2, reps["total_sales"], width, label="Total Sales",
               color=CHART_COLORS[0], alpha=0.9)
        ax.bar(x + width / 2, reps["total_profit"], width, label="Total Profit",
               color=[PALETTE["positive"] if p >= 0 else PALETTE["negative"]
                      for p in reps["total_profit"]],
               alpha=0.9)

        ax.set_xticks(x)
        ax.set_xticklabels(reps["sales_rep"], rotation=15, ha="right")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1e3:.0f}K"))
        ax.set_ylabel("Amount (USD)")
        ax.set_title("Sales Representative Performance", pad=15)
        ax.legend()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()
        return save_chart(fig, "08_rep_performance.png")

    # ============================================================
    # 9. Return Rates by Category (Bar)
    # ============================================================

    def chart_return_rates(self) -> Path:
        """Bar chart — Return rates by category."""
        cat_ret = self.results["returns"]["by_category"]

        fig, ax = plt.subplots(figsize=(9, 5))
        colors = [CHART_COLORS[i] for i in range(len(cat_ret))]
        bars = ax.bar(cat_ret["category"], cat_ret["return_rate"] * 100,
                      color=colors, alpha=0.9, edgecolor="white", width=0.5)

        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3,
                    f"{h:.1f}%", ha="center", va="bottom", fontsize=10)

        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
        ax.set_ylabel("Return Rate (%)")
        ax.set_title("Return Rates by Product Category", pad=15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()
        return save_chart(fig, "09_return_rates_by_category.png")

    # ============================================================
    # 10. Shipping Duration by Ship Mode (Box)
    # ============================================================

    def chart_shipping_duration(self) -> Path:
        """Box plot — Shipping duration distribution by ship mode."""
        df = self.df.dropna(subset=["shipping_duration", "ship_mode"]).copy()
        df = df[df["shipping_duration"] >= 0]

        order = (
            df.groupby("ship_mode")["shipping_duration"]
            .median()
            .sort_values()
            .index.tolist()
        )

        fig, ax = plt.subplots(figsize=(10, 6))
        data_groups = [df[df["ship_mode"] == m]["shipping_duration"].values for m in order]
        bp = ax.boxplot(
            data_groups,
            tick_labels=order,
            patch_artist=True,
            showfliers=False,
            medianprops=dict(color="white", linewidth=2.5),
            whiskerprops=dict(color=PALETTE["neutral"], linewidth=1.5),
            capprops=dict(color=PALETTE["neutral"], linewidth=1.5),
            boxprops=dict(linewidth=1.5),
        )
        for patch, color in zip(bp["boxes"], CHART_COLORS):
            patch.set_facecolor(color)
            patch.set_alpha(0.85)

        ax.set_ylabel("Shipping Duration (Days)")
        ax.set_xlabel("Ship Mode")
        ax.set_title("Shipping Duration Distribution by Ship Mode", pad=15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()
        return save_chart(fig, "10_shipping_duration.png")

    # ============================================================
    # Generate all charts
    # ============================================================

    def generate_all(self) -> dict:
        """Generate all 10 charts and return paths dict."""
        logger.info("Generating all visualizations...")
        chart_methods = [
            ("sales_by_state", self.chart_sales_by_state),
            ("sales_by_category", self.chart_sales_by_category),
            ("sales_trend", self.chart_sales_trend),
            ("sales_by_region", self.chart_sales_by_region),
            ("top_products", self.chart_top_products),
            ("discount_vs_margin", self.chart_discount_vs_margin),
            ("profit_by_subcategory", self.chart_profit_by_subcategory),
            ("rep_performance", self.chart_rep_performance),
            ("return_rates", self.chart_return_rates),
            ("shipping_duration", self.chart_shipping_duration),
        ]

        paths = {}
        for name, method in chart_methods:
            try:
                path = method()
                paths[name] = path
                logger.info("Generated: %s", name)
            except Exception as exc:
                logger.error("Failed to generate chart '%s': %s", name, exc, exc_info=True)
                paths[name] = None

        logger.info("Visualization generation complete: %d/%d succeeded",
                    sum(1 for v in paths.values() if v), len(paths))
        return paths
