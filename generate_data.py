"""
generate_data.py
-----------------
Creates a realistic sales dataset split into 3 relational tables
(customers, products, orders) -- mirroring how a real sales database
is structured, so the SQL analysis later can use genuine JOINs.

Run this once to produce the CSVs in /data. Then run analysis.py.
"""

import numpy as np
import pandas as pd

np.random.seed(42)  # fixed seed = reproducible data every time you run this

# -----------------------------------------------------------------
# 1. CUSTOMERS TABLE
# -----------------------------------------------------------------
N_CUSTOMERS = 2000
REGIONS = ["North", "South", "East", "West"]

customers = pd.DataFrame({
    "customer_id": range(1, N_CUSTOMERS + 1),
    "customer_name": [f"Customer_{i}" for i in range(1, N_CUSTOMERS + 1)],
    "region": np.random.choice(REGIONS, size=N_CUSTOMERS, p=[0.3, 0.25, 0.25, 0.2]),
    "signup_date": pd.to_datetime("2022-01-01") +
                    pd.to_timedelta(np.random.randint(0, 700, N_CUSTOMERS), unit="D"),
})

# -----------------------------------------------------------------
# 2. PRODUCTS TABLE
# -----------------------------------------------------------------
CATEGORIES = {
    "Electronics": (2000, 60000),
    "Furniture": (1500, 40000),
    "Apparel": (300, 5000),
    "Groceries": (50, 1500),
    "Sports": (500, 8000),
}
N_PRODUCTS = 200

product_rows = []
for i in range(1, N_PRODUCTS + 1):
    category = np.random.choice(list(CATEGORIES.keys()))
    low, high = CATEGORIES[category]
    unit_price = round(np.random.uniform(low, high), 2)
    unit_cost = round(unit_price * np.random.uniform(0.55, 0.8), 2)  # cost is 55-80% of price
    product_rows.append({
        "product_id": i,
        "product_name": f"{category}_Product_{i}",
        "category": category,
        "unit_price": unit_price,
        "unit_cost": unit_cost,
    })
products = pd.DataFrame(product_rows)

# -----------------------------------------------------------------
# 3. ORDERS TABLE (the fact table -- 50,000+ rows)
# -----------------------------------------------------------------
N_ORDERS = 52000
start_date = pd.to_datetime("2023-01-01")
end_date = pd.to_datetime("2024-12-31")
date_range_days = (end_date - start_date).days

# Simulate mild seasonality: more orders in Nov/Dec (holiday season)
order_dates = start_date + pd.to_timedelta(
    np.random.randint(0, date_range_days, N_ORDERS), unit="D"
)
seasonal_boost = order_dates.month.isin([11, 12])
# duplicate ~15% of holiday-season rows to boost volume realistically
boost_idx = np.random.choice(np.where(seasonal_boost)[0],
                              size=int(seasonal_boost.sum() * 0.4), replace=False)
order_dates = order_dates.append(order_dates[boost_idx]) if hasattr(order_dates, "append") \
    else pd.DatetimeIndex(list(order_dates) + list(order_dates[boost_idx]))

n_final = len(order_dates)

orders = pd.DataFrame({
    "order_id": range(1, n_final + 1),
    "customer_id": np.random.randint(1, N_CUSTOMERS + 1, n_final),
    "product_id": np.random.randint(1, N_PRODUCTS + 1, n_final),
    "order_date": order_dates,
    "quantity": np.random.randint(1, 6, n_final),
    "discount": np.round(np.random.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2], n_final), 2),
})

# -----------------------------------------------------------------
# SAVE
# -----------------------------------------------------------------
customers.to_csv("data/customers.csv", index=False)
products.to_csv("data/products.csv", index=False)
orders.to_csv("data/orders.csv", index=False)

print(f"customers.csv -> {len(customers)} rows")
print(f"products.csv  -> {len(products)} rows")
print(f"orders.csv    -> {len(orders)} rows")
