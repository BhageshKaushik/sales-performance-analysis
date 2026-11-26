"""
test_analysis.py — Tests for SalesAnalyzer
Sales Performance Analysis System
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from analysis import SalesAnalyzer


@pytest.fixture
def sample_df():
    """
    Create a minimal but comprehensive analytical DataFrame for testing.
    Mirrors the schema produced by the SQL analytical JOIN.
    """
    return pd.DataFrame({
        "order_id": ["CA-001", "CA-001", "CA-002", "CA-003", "CA-004", "CA-005"],
        "order_date": pd.to_datetime([
            "2021-01-15", "2021-01-15", "2021-02-20",
            "2021-03-10", "2021-04-05", "2021-05-20",
        ]),
        "ship_date": pd.to_datetime([
            "2021-01-18", "2021-01-18", "2021-02-24",
            "2021-03-15", "2021-04-09", "2021-05-24",
        ]),
        "ship_mode": ["FIRST CLASS", "FIRST CLASS", "STANDARD CLASS",
                      "SECOND CLASS", "STANDARD CLASS", "FIRST CLASS"],
        "customer_id": ["CUS-001", "CUS-001", "CUS-002", "CUS-003", "CUS-002", "CUS-003"],
        "customer_name": ["Alice Smith", "Alice Smith", "Bob Jones",
                          "Carol White", "Bob Jones", "Carol White"],
        "segment": ["CONSUMER", "CONSUMER", "CORPORATE",
                    "HOME OFFICE", "CORPORATE", "HOME OFFICE"],
        "country": ["US"] * 6,
        "city": ["New York", "New York", "Los Angeles", "Chicago", "Los Angeles", "Chicago"],
        "state": ["New York", "New York", "California", "Illinois", "California", "Illinois"],
        "postal_code": ["10001"] * 6,
        "region": ["EAST", "EAST", "WEST", "CENTRAL", "WEST", "CENTRAL"],
        "product_id": ["FUR-001", "OFF-001", "TEC-001", "FUR-002", "OFF-001", "TEC-002"],
        "category": ["FURNITURE", "OFFICE SUPPLIES", "TECHNOLOGY",
                     "FURNITURE", "OFFICE SUPPLIES", "TECHNOLOGY"],
        "sub_category": ["Bookcases", "Art", "Phones", "Chairs", "Art", "Machines"],
        "product_name": ["Product A", "Product B", "Product C",
                          "Product D", "Product B", "Product E"],
        "sales": [261.96, 14.62, 907.15, 350.00, 20.00, 1500.00],
        "quantity": [2, 3, 7, 4, 2, 5],
        "discount": [0.0, 0.1, 0.2, 0.0, 0.3, 0.0],
        "profit": [41.91, -6.87, 90.72, 55.00, -8.00, 300.00],
        "is_returned": [1, 0, 0, 1, 0, 0],
        "sales_rep": ["Anna", "Anna", "Chuck", "Kelly", "Chuck", "Kelly"],
        "order_year": [2021] * 6,
        "order_month": [1, 1, 2, 3, 4, 5],
        "order_quarter": [1, 1, 1, 1, 2, 2],
        "unit_price": [130.98, 4.87, 129.59, 87.50, 10.00, 300.00],
        "profit_margin": [0.1600, -0.4699, 0.1000, 0.1571, -0.4000, 0.2000],
    })


class TestSalesPerformance:
    def test_returns_dict(self, sample_df):
        result = SalesAnalyzer(sample_df).sales_performance()
        assert isinstance(result, dict)

    def test_total_sales_correct(self, sample_df):
        result = SalesAnalyzer(sample_df).sales_performance()
        expected = round(sample_df["sales"].sum(), 2)
        assert abs(result["total_sales"] - expected) < 0.01

    def test_total_profit_correct(self, sample_df):
        result = SalesAnalyzer(sample_df).sales_performance()
        expected = round(sample_df["profit"].sum(), 2)
        assert abs(result["total_profit"] - expected) < 0.01

    def test_total_orders_unique_count(self, sample_df):
        result = SalesAnalyzer(sample_df).sales_performance()
        assert result["total_orders"] == sample_df["order_id"].nunique()

    def test_total_returned_correct(self, sample_df):
        result = SalesAnalyzer(sample_df).sales_performance()
        # CA-001 and CA-003 have is_returned=1; unique returned orders = 2
        assert result["total_returned"] == 2

    def test_overall_profit_margin_no_zero_div(self):
        """Guard against division by zero when total_sales = 0."""
        df = pd.DataFrame({
            "order_id": ["X"], "sales": [0.0], "profit": [0.0],
            "quantity": [1], "is_returned": [0],
            "order_date": pd.to_datetime(["2021-01-01"]),
            "ship_date": pd.to_datetime(["2021-01-03"]),
        })
        result = SalesAnalyzer(df).sales_performance()
        assert result["overall_profit_margin"] == 0.0


class TestTopProducts:
    def test_top_products_by_sales_returns_df(self, sample_df):
        result = SalesAnalyzer(sample_df).top_products_by_sales(5)
        assert isinstance(result, pd.DataFrame)

    def test_top_products_sorted_descending(self, sample_df):
        result = SalesAnalyzer(sample_df).top_products_by_sales()
        assert result["total_sales"].is_monotonic_decreasing

    def test_top_customers_sorted_descending(self, sample_df):
        result = SalesAnalyzer(sample_df).top_customers_by_sales()
        assert result["total_sales"].is_monotonic_decreasing


class TestGeoAnalysis:
    def test_returns_dict_with_correct_keys(self, sample_df):
        result = SalesAnalyzer(sample_df).geo_analysis()
        assert "by_state" in result
        assert "by_city" in result
        assert "by_region" in result
        assert "high_sales_negative_profit" in result

    def test_state_sales_sum_matches_total(self, sample_df):
        result = SalesAnalyzer(sample_df).geo_analysis()
        assert abs(result["by_state"]["total_sales"].sum() - sample_df["sales"].sum()) < 0.01


class TestCategoryAnalysis:
    def test_returns_dict_with_correct_keys(self, sample_df):
        result = SalesAnalyzer(sample_df).category_analysis()
        assert "by_category" in result
        assert "by_sub_category" in result
        assert "best_category" in result
        assert "worst_category" in result

    def test_profit_margin_computed(self, sample_df):
        result = SalesAnalyzer(sample_df).category_analysis()
        assert "profit_margin" in result["by_category"].columns


class TestReturnAnalysis:
    def test_overall_return_rate_between_0_and_1(self, sample_df):
        result = SalesAnalyzer(sample_df).return_analysis()
        assert 0.0 <= result["overall_return_rate"] <= 1.0

    def test_return_rate_by_category_sums(self, sample_df):
        result = SalesAnalyzer(sample_df).return_analysis()
        assert "return_rate" in result["by_category"].columns
        assert (result["by_category"]["return_rate"] <= 1.0).all()


class TestDiscountAnalysis:
    def test_returns_dict_with_threshold(self, sample_df):
        result = SalesAnalyzer(sample_df).discount_analysis()
        assert "by_discount_range" in result
        assert "threshold" in result
        assert "threshold_evidence" in result

    def test_discount_ranges_cover_all_rows(self, sample_df):
        result = SalesAnalyzer(sample_df).discount_analysis()
        # order_count sums unique orders per discount bucket; total should equal
        # unique order count in the full DataFrame.
        total_rows = result["by_discount_range"]["order_count"].sum()
        unique_orders = sample_df["order_id"].nunique()
        # Allow for the fact that multi-line orders may appear in multiple buckets
        # (one order can have lines in different discount ranges); just verify > 0
        assert total_rows >= unique_orders

    def test_no_division_by_zero_in_margin(self, sample_df):
        """Rows with zero sales should produce NaN margin, not error."""
        df = sample_df.copy()
        df.loc[0, "sales"] = 0.0
        result = SalesAnalyzer(df).discount_analysis()
        # Should complete without raising
        assert "by_discount_range" in result


class TestShippingDuration:
    def test_shipping_duration_computed(self, sample_df):
        analyzer = SalesAnalyzer(sample_df)
        assert "shipping_duration" in analyzer.df.columns

    def test_shipping_duration_non_negative(self, sample_df):
        analyzer = SalesAnalyzer(sample_df)
        durations = analyzer.df["shipping_duration"].dropna()
        assert (durations >= 0).all()
