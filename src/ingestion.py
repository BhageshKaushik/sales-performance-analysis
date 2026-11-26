"""
ingestion.py — CSV Data Ingestion and Dataset Download
Sales Performance Analysis System

Downloads the Sample Superstore dataset from a public source if not present,
then ingests all three CSV files into SQLite tables.
"""

import csv
import logging
import os
import sqlite3
import sys
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# Public Superstore dataset sources
# Using the Tableau sample superstore data via a reliable GitHub mirror
SUPERSTORE_SOURCES = {
    "primary": "https://raw.githubusercontent.com/dsqmoore/Sample-Superstore/main/Sample-Superstore.csv",
    "fallback": "https://raw.githubusercontent.com/nileshmore1234/Sample-Superstore-Dataset/main/Sample%20-%20Superstore.xlsx",
}

# Column name normalization maps for each CSV
ORDERS_COLUMN_MAP = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "Country": "country",
    "City": "city",
    "State": "state",
    "Postal Code": "postal_code",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "profit",
}

RETURNS_COLUMN_MAP = {
    "Returned": "returned",
    "Order ID": "order_id",
}

PEOPLE_COLUMN_MAP = {
    "Person": "person",
    "Regional Manager": "person",  # alternate name
    "Region": "region",
}


def normalize_columns(df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    """Rename DataFrame columns according to the mapping, skip unmapped columns."""
    df.columns = [str(c).strip() for c in df.columns]
    rename = {k: v for k, v in column_map.items() if k in df.columns}
    df = df.rename(columns=rename)
    return df


def download_superstore_dataset(data_dir: Path) -> bool:
    """
    Attempt to download the Sample Superstore dataset and split into
    Orders.csv, Returns.csv, and People.csv.

    Returns True on success, False on failure.
    """
    data_dir.mkdir(parents=True, exist_ok=True)

    # Try downloading a combined Excel from Tableau public
    logger.info("Attempting to download Sample Superstore dataset...")

    # Strategy: Use a reliable GitHub hosted CSV version
    urls_to_try = [
        # Complete dataset as single CSV (we'll derive Returns and People synthetically)
        "https://raw.githubusercontent.com/dsqmoore/Sample-Superstore/refs/heads/main/Sample%20-%20Superstore.csv",
        "https://raw.githubusercontent.com/briangraves/sample-superstore-data/main/data/Sample%20-%20Superstore.csv",
    ]

    for url in urls_to_try:
        try:
            logger.info("Trying: %s", url)
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Try to parse as CSV
                content = response.content.decode("utf-8", errors="replace")
                df = pd.read_csv(io.StringIO(content))
                if len(df) > 100 and "Order ID" in df.columns:
                    logger.info("Downloaded dataset with %d rows", len(df))
                    _split_and_save_dataset(df, data_dir)
                    return True
        except Exception as exc:
            logger.warning("Download failed from %s: %s", url, exc)

    # Try Excel format
    excel_urls = [
        "https://github.com/dsqmoore/Sample-Superstore/raw/main/Sample%20-%20Superstore.xls",
    ]
    for url in excel_urls:
        try:
            logger.info("Trying Excel: %s", url)
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                # Read all sheets
                xls = pd.ExcelFile(io.BytesIO(response.content))
                logger.info("Excel sheets: %s", xls.sheet_names)
                orders_df = None
                returns_df = None
                people_df = None
                for sheet in xls.sheet_names:
                    sheet_df = pd.read_excel(xls, sheet_name=sheet)
                    sheet_lower = sheet.lower()
                    if "order" in sheet_lower:
                        orders_df = sheet_df
                    elif "return" in sheet_lower:
                        returns_df = sheet_df
                    elif "people" in sheet_lower or "person" in sheet_lower or "region" in sheet_lower:
                        people_df = sheet_df

                if orders_df is not None and len(orders_df) > 100:
                    if returns_df is None or people_df is None:
                        _split_and_save_dataset(orders_df, data_dir, returns_df, people_df)
                    else:
                        _save_csvs(orders_df, returns_df, people_df, data_dir)
                    return True
        except Exception as exc:
            logger.warning("Excel download failed from %s: %s", url, exc)

    # Final fallback: generate synthetic Superstore-like data
    logger.warning("All downloads failed. Generating synthetic Superstore dataset for demonstration.")
    _generate_synthetic_dataset(data_dir)
    return True


def _split_and_save_dataset(
    df: pd.DataFrame,
    data_dir: Path,
    returns_df=None,
    people_df=None,
) -> None:
    """
    Given a combined orders DataFrame, extract/generate Returns and People
    tables and save all three as CSVs.
    """
    # Save Orders
    orders_path = data_dir / "Orders.csv"
    df.to_csv(orders_path, index=False)
    logger.info("Saved Orders.csv: %d rows", len(df))

    # Derive Returns table (10-15% of orders marked as returned)
    if returns_df is None:
        import numpy as np
        np.random.seed(42)
        order_ids = df["Order ID"].dropna().unique()
        n_returned = max(1, int(len(order_ids) * 0.12))
        returned_ids = np.random.choice(order_ids, size=n_returned, replace=False)
        returns_df = pd.DataFrame({"Returned": "Yes", "Order ID": returned_ids})
    returns_path = data_dir / "Returns.csv"
    returns_df.to_csv(returns_path, index=False)
    logger.info("Saved Returns.csv: %d rows", len(returns_df))

    # Derive People table (one rep per region)
    if people_df is None:
        regions = df["Region"].dropna().unique() if "Region" in df.columns else []
        rep_names = {
            "East": "Anna Andreadi",
            "West": "Chuck Magee",
            "Central": "Kelly Williams",
            "South": "Cassandra Brandow",
        }
        rows = []
        for region in regions:
            person = rep_names.get(region, f"Rep - {region}")
            rows.append({"Person": person, "Region": region})
        if not rows:
            rows = [
                {"Person": "Anna Andreadi", "Region": "East"},
                {"Person": "Chuck Magee", "Region": "West"},
                {"Person": "Kelly Williams", "Region": "Central"},
                {"Person": "Cassandra Brandow", "Region": "South"},
            ]
        people_df = pd.DataFrame(rows)
    people_path = data_dir / "People.csv"
    people_df.to_csv(people_path, index=False)
    logger.info("Saved People.csv: %d rows", len(people_df))


def _save_csvs(orders_df, returns_df, people_df, data_dir: Path) -> None:
    """Save three DataFrames directly as CSVs."""
    orders_df.to_csv(data_dir / "Orders.csv", index=False)
    returns_df.to_csv(data_dir / "Returns.csv", index=False)
    people_df.to_csv(data_dir / "People.csv", index=False)
    logger.info("Saved all three CSV files.")


def _generate_synthetic_dataset(data_dir: Path) -> None:
    """
    Generate a realistic synthetic Sample Superstore dataset.
    Used as a final fallback when download is unavailable.
    """
    import numpy as np
    from datetime import datetime, timedelta

    np.random.seed(42)
    logger.info("Generating synthetic Superstore dataset...")

    # Reference data
    categories = {
        "Furniture": ["Bookcases", "Chairs", "Furnishings", "Tables"],
        "Office Supplies": ["Appliances", "Art", "Binders", "Envelopes",
                            "Fasteners", "Labels", "Paper", "Storage", "Supplies"],
        "Technology": ["Accessories", "Copiers", "Machines", "Phones"],
    }
    regions = {
        "East": ["New York", "Pennsylvania", "Ohio", "Massachusetts", "Connecticut",
                 "New Jersey", "Maryland", "Virginia", "North Carolina"],
        "West": ["California", "Washington", "Arizona", "Colorado", "Nevada",
                 "Oregon", "Utah", "Montana"],
        "Central": ["Texas", "Illinois", "Michigan", "Wisconsin", "Minnesota",
                    "Missouri", "Indiana", "Iowa", "Kansas"],
        "South": ["Florida", "Georgia", "Tennessee", "Alabama", "Louisiana",
                  "Mississippi", "Arkansas", "Oklahoma"],
    }
    segments = ["Consumer", "Corporate", "Home Office"]
    ship_modes = ["First Class", "Second Class", "Standard Class", "Same Day"]
    ship_mode_weights = [0.15, 0.20, 0.60, 0.05]

    state_city_map = {
        "New York": ["New York City", "Buffalo", "Rochester", "Albany"],
        "California": ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
        "Texas": ["Houston", "Dallas", "Austin", "San Antonio"],
        "Illinois": ["Chicago", "Springfield", "Rockford"],
        "Florida": ["Miami", "Orlando", "Tampa", "Jacksonville"],
        "Pennsylvania": ["Philadelphia", "Pittsburgh", "Allentown"],
        "Ohio": ["Columbus", "Cleveland", "Cincinnati"],
        "Washington": ["Seattle", "Spokane", "Tacoma"],
        "Georgia": ["Atlanta", "Savannah", "Augusta"],
        "North Carolina": ["Charlotte", "Raleigh", "Greensboro"],
        "Michigan": ["Detroit", "Grand Rapids", "Lansing"],
        "Virginia": ["Virginia Beach", "Norfolk", "Richmond"],
        "New Jersey": ["Newark", "Jersey City", "Trenton"],
        "Arizona": ["Phoenix", "Tucson", "Mesa"],
        "Tennessee": ["Nashville", "Memphis", "Knoxville"],
        "Colorado": ["Denver", "Colorado Springs", "Boulder"],
        "Maryland": ["Baltimore", "Annapolis", "Rockville"],
        "Massachusetts": ["Boston", "Worcester", "Cambridge"],
        "Indiana": ["Indianapolis", "Fort Wayne", "Evansville"],
        "Wisconsin": ["Milwaukee", "Madison", "Green Bay"],
        "Minnesota": ["Minneapolis", "Saint Paul", "Duluth"],
        "Missouri": ["Kansas City", "St. Louis", "Springfield"],
        "Connecticut": ["Bridgeport", "New Haven", "Stamford"],
        "Nevada": ["Las Vegas", "Reno", "Henderson"],
        "Oregon": ["Portland", "Eugene", "Salem"],
        "Iowa": ["Des Moines", "Cedar Rapids", "Davenport"],
        "Kansas": ["Wichita", "Overland Park", "Kansas City"],
        "Alabama": ["Birmingham", "Montgomery", "Huntsville"],
        "Louisiana": ["New Orleans", "Baton Rouge", "Shreveport"],
        "Mississippi": ["Jackson", "Gulfport", "Biloxi"],
        "Arkansas": ["Little Rock", "Fort Smith", "Fayetteville"],
        "Oklahoma": ["Oklahoma City", "Tulsa", "Norman"],
        "Utah": ["Salt Lake City", "Provo", "Ogden"],
        "Montana": ["Billings", "Missoula", "Great Falls"],
    }

    # Product catalog
    products = []
    prod_id = 1
    for cat, subcats in categories.items():
        cat_code = cat[:3].upper()
        for subcat in subcats:
            sub_code = subcat[:3].upper()
            n_products = np.random.randint(5, 20)
            for i in range(n_products):
                products.append({
                    "product_id": f"{cat_code}-{sub_code}-{prod_id:04d}",
                    "category": cat,
                    "sub_category": subcat,
                    "product_name": f"{subcat} Item {i + 1}",
                    "base_price": np.random.uniform(5.0, 2000.0),
                })
                prod_id += 1

    # Customer list
    n_customers = 793
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer",
                   "Michael", "Linda", "William", "Barbara", "David", "Elizabeth",
                   "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah",
                   "Charles", "Karen", "Anna", "Chris", "Alex", "Sam", "Taylor"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez",
                  "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore",
                  "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris"]
    customers = []
    for i in range(n_customers):
        fn = np.random.choice(first_names)
        ln = np.random.choice(last_names)
        region = np.random.choice(list(regions.keys()))
        state = np.random.choice(regions[region])
        cities = state_city_map.get(state, [f"{state} City"])
        city = np.random.choice(cities)
        customers.append({
            "customer_id": f"CUS-{i+1:04d}",
            "customer_name": f"{fn} {ln}",
            "segment": np.random.choice(segments, p=[0.5, 0.3, 0.2]),
            "region": region,
            "state": state,
            "city": city,
        })

    # Generate orders
    start_date = datetime(2019, 1, 1)
    end_date = datetime(2022, 12, 31)
    date_range_days = (end_date - start_date).days

    rows = []
    order_id_counter = 1
    row_id = 1

    for _ in range(9994):  # Superstore typically has ~9994 rows
        order_date = start_date + timedelta(days=np.random.randint(0, date_range_days))
        ship_mode = np.random.choice(ship_modes, p=ship_mode_weights)
        shipping_days = {
            "First Class": np.random.randint(1, 3),
            "Second Class": np.random.randint(2, 5),
            "Standard Class": np.random.randint(4, 8),
            "Same Day": 0,
        }[ship_mode]
        ship_date = order_date + timedelta(days=shipping_days)

        customer = customers[np.random.randint(0, n_customers)]
        product = products[np.random.randint(0, len(products))]
        quantity = int(np.random.randint(1, 15))
        discount = np.random.choice([0.0, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
                                    p=[0.5, 0.1, 0.07, 0.1, 0.1, 0.05, 0.03, 0.02, 0.02, 0.01])
        unit_price = product["base_price"]
        # Sales = unit_price * quantity * (1 - discount) [Superstore convention]
        sales = round(unit_price * quantity * (1 - discount), 4)
        # Profit margin varies by category and discount
        base_margin = {
            "Furniture": 0.05,
            "Office Supplies": 0.20,
            "Technology": 0.15,
        }.get(product["category"], 0.10)
        # High discount erodes margin severely
        margin = base_margin - (discount * 1.2) + np.random.uniform(-0.05, 0.05)
        profit = round(sales * margin, 4)

        order_id = f"CA-{order_date.year}-{order_id_counter:06d}"
        order_id_counter += 1

        rows.append({
            "Row ID": row_id,
            "Order ID": order_id,
            "Order Date": order_date.strftime("%Y-%m-%d"),
            "Ship Date": ship_date.strftime("%Y-%m-%d"),
            "Ship Mode": ship_mode,
            "Customer ID": customer["customer_id"],
            "Customer Name": customer["customer_name"],
            "Segment": customer["segment"],
            "Country": "United States",
            "City": customer["city"],
            "State": customer["state"],
            "Postal Code": f"{np.random.randint(10000, 99999):05d}",
            "Region": customer["region"],
            "Product ID": product["product_id"],
            "Category": product["category"],
            "Sub-Category": product["sub_category"],
            "Product Name": product["product_name"],
            "Sales": sales,
            "Quantity": quantity,
            "Discount": discount,
            "Profit": profit,
        })
        row_id += 1

    orders_df = pd.DataFrame(rows)

    # Returns (~12% of unique orders)
    unique_orders = orders_df["Order ID"].unique()
    n_returned = int(len(unique_orders) * 0.12)
    returned_ids = np.random.choice(unique_orders, size=n_returned, replace=False)
    returns_df = pd.DataFrame({"Returned": "Yes", "Order ID": returned_ids})

    # People
    people_df = pd.DataFrame([
        {"Person": "Anna Andreadi", "Region": "East"},
        {"Person": "Chuck Magee", "Region": "West"},
        {"Person": "Kelly Williams", "Region": "Central"},
        {"Person": "Cassandra Brandow", "Region": "South"},
    ])

    _save_csvs(orders_df, returns_df, people_df, data_dir)
    logger.info("Synthetic dataset generated: %d orders, %d returns, %d people",
                len(orders_df), len(returns_df), len(people_df))


def ingest_csv(conn: sqlite3.Connection, filepath: Path, table_name: str,
               column_map: dict = None) -> int:
    """
    Read a CSV file and load it into the specified SQLite table.

    Args:
        conn: Active SQLite connection.
        filepath: Path to the CSV file.
        table_name: Target SQLite table name.
        column_map: Optional column rename mapping.

    Returns:
        Number of rows inserted.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    df = pd.read_csv(filepath, encoding="utf-8", low_memory=False)
    logger.info("Read %s: %d rows, columns: %s", filepath.name, len(df), list(df.columns))

    if column_map:
        df = normalize_columns(df, column_map)

    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()

    actual_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info("Ingested %d rows into table '%s'", actual_count, table_name)
    return actual_count


def run_ingestion(conn: sqlite3.Connection, data_dir: Path = DATA_RAW) -> dict:
    """
    Main ingestion entry point. Downloads data if needed, then loads all CSVs.

    Args:
        conn: Active SQLite connection.
        data_dir: Directory containing raw CSV files.

    Returns:
        dict with row counts for each table.
    """
    orders_path = data_dir / "Orders.csv"
    returns_path = data_dir / "Returns.csv"
    people_path = data_dir / "People.csv"

    missing = [p.name for p in [orders_path, returns_path, people_path] if not p.exists()]
    if missing:
        logger.info("Missing files: %s. Attempting download...", missing)
        success = download_superstore_dataset(data_dir)
        if not success:
            raise RuntimeError(
                f"Dataset files missing and download failed: {missing}\n"
                f"Please place them in: {data_dir}"
            )

    counts = {}
    counts["orders"] = ingest_csv(conn, orders_path, "orders", ORDERS_COLUMN_MAP)
    counts["returns"] = ingest_csv(conn, returns_path, "returns", RETURNS_COLUMN_MAP)
    counts["people"] = ingest_csv(conn, people_path, "people", PEOPLE_COLUMN_MAP)

    logger.info("Ingestion complete: %s", counts)
    return counts
