"""
Step 1: clean the raw DataCo file and split it into a star schema.
Run from the repo root:  python notebooks/01_clean_and_model.py
Input : data/DataCoSupplyChainDataset.csv
Output: data/processed/*.csv  (one file per table, ready to load into Postgres)
"""
from pathlib import Path
import pandas as pd

RAW = Path("data/DataCoSupplyChainDataset.csv")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RAW, encoding="latin-1")
print(f"Raw: {df.shape[0]:,} rows x {df.shape[1]} columns")

# ---- 1. Cleaning decisions (document these in your README) ----------------
# PII: not needed for analysis, and it shouldn't sit in a portfolio repo.
# Empty/useless: Product Description is 100% null, Order Zipcode ~86% null,
#   Product Image is just a URL.
# Duplicates: 'Benefit per order' = 'Order Profit Per Order'; Customer Id =
#   Order Customer Id; Order Item Cardprod Id = Product Card Id.
drop_cols = [
    "Customer Email", "Customer Fname", "Customer Lname", "Customer Password",
    "Customer Street", "Product Description", "Order Zipcode", "Product Image",
    "Benefit per order", "Order Customer Id", "Order Item Cardprod Id",
]
df = df.drop(columns=drop_cols)

df["order_date"] = pd.to_datetime(df["order date (DateOrders)"], format="%m/%d/%Y %H:%M")
df["shipping_date"] = pd.to_datetime(df["shipping date (DateOrders)"], format="%m/%d/%Y %H:%M")
df = df.drop(columns=["order date (DateOrders)", "shipping date (DateOrders)"])
df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]

# ---- 2. Dimensions ---------------------------------------------------------
dim_customer = (df[["customer_id", "customer_segment", "customer_city",
                    "customer_state", "customer_country"]]
                .drop_duplicates("customer_id"))

dim_product = (df[["product_card_id", "product_name", "category_id", "category_name",
                   "department_id", "department_name", "product_price", "product_status"]]
               .drop_duplicates("product_card_id"))

loc_cols = ["order_city", "order_state", "order_country", "order_region", "market"]
dim_location = df[loc_cols].drop_duplicates().reset_index(drop=True)
dim_location.insert(0, "location_key", dim_location.index + 1)

dates = pd.DataFrame({"date": pd.date_range(df["order_date"].min().normalize(),
                                            df["order_date"].max().normalize())})
dim_date = pd.DataFrame({
    "date_key": dates["date"].dt.strftime("%Y%m%d").astype(int),
    "date": dates["date"].dt.date,
    "year": dates["date"].dt.year,
    "quarter": dates["date"].dt.quarter,
    "month": dates["date"].dt.month,
    "month_name": dates["date"].dt.month_name(),
    "day_of_week": dates["date"].dt.day_name(),
    "is_weekend": dates["date"].dt.dayofweek >= 5,
})

# ---- 3. Fact table (one row per order line item) ---------------------------
fact = df.merge(dim_location, on=loc_cols, how="left")
fact["order_date_key"] = fact["order_date"].dt.strftime("%Y%m%d").astype(int)
fact = fact.rename(columns={
    "days_for_shipping_real": "actual_ship_days",
    "days_for_shipment_scheduled": "scheduled_ship_days",
    "late_delivery_risk": "is_late",
    "order_item_id": "order_item_id",
    "order_item_product_price": "unit_price",
    "order_item_quantity": "quantity",
    "order_item_discount": "discount_amount",
    "order_item_discount_rate": "discount_rate",
    "order_item_total": "item_total",
    "order_profit_per_order": "profit",
    "order_item_profit_ratio": "profit_ratio",
})[[
    "order_item_id", "order_id", "order_date", "order_date_key", "shipping_date",
    "customer_id", "product_card_id", "location_key", "shipping_mode", "order_status",
    "delivery_status", "scheduled_ship_days", "actual_ship_days", "is_late",
    "quantity", "unit_price", "discount_amount", "discount_rate",
    "sales", "item_total", "profit", "profit_ratio",
]]

# Source stores float noise (e.g. 13.10999966); round to sensible precision.
for c in ["unit_price", "discount_amount", "sales", "item_total", "profit"]:
    fact[c] = fact[c].round(2)
for c in ["discount_rate", "profit_ratio"]:
    fact[c] = fact[c].round(4)

# ---- 4. Sanity checks (fail loudly if the data isn't what we expect) -------
assert fact["order_item_id"].is_unique
assert fact["location_key"].notna().all()
assert set(fact["customer_id"]) <= set(dim_customer["customer_id"])
assert set(fact["product_card_id"]) <= set(dim_product["product_card_id"])
assert len(fact) == len(df)

tables = {"dim_customer": dim_customer, "dim_product": dim_product,
          "dim_location": dim_location, "dim_date": dim_date, "fact_order_item": fact}
for name, t in tables.items():
    t.to_csv(OUT / f"{name}.csv", index=False)
    print(f"{name:16s} {len(t):>9,} rows")
