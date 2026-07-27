"""
Sales Performance Dashboard - Analysis Script
-----------------------------------------------
Loads 3 relational CSVs (customers, products, orders) into a local
SQLite database, then answers real business questions using SQL
(JOINs, CTEs, window functions) -- exactly what the resume claims.

Run:
    python generate_data.py   (only needed once, creates the CSVs)
    python analysis.py
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------------
# 1. LOAD CSVs INTO AN IN-MEMORY SQL DATABASE
# -----------------------------------------------------------------
# Why SQLite: it lets us write and run REAL SQL against the data
# without needing a separate database server -- perfect for a
# portfolio project that needs to be fully self-contained on GitHub.
conn = sqlite3.connect(":memory:")

customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")
orders = pd.read_csv("data/orders.csv", parse_dates=["order_date"])

customers.to_sql("customers", conn, index=False, if_exists="replace")
products.to_sql("products", conn, index=False, if_exists="replace")
orders.to_sql("orders", conn, index=False, if_exists="replace")

print(f"Loaded: {len(customers)} customers, {len(products)} products, {len(orders)} orders")

def run_query(sql):
    """Small helper so every query below is one clean line to call."""
    return pd.read_sql_query(sql, conn)

# -----------------------------------------------------------------
# 2. CORE METRIC: REVENUE + PROFIT PER ORDER
# -----------------------------------------------------------------
# revenue = quantity * unit_price * (1 - discount)
# profit  = revenue - (quantity * unit_cost)
# We compute this once as a CTE (temporary named query) and reuse it
# in every question below via `WITH order_metrics AS (...)`.
ORDER_METRICS_CTE = """
WITH order_metrics AS (
    SELECT
        o.order_id,
        o.order_date,
        o.customer_id,
        o.product_id,
        c.region,
        p.category,
        p.product_name,
        o.quantity,
        p.unit_price,
        p.unit_cost,
        o.discount,
        (o.quantity * p.unit_price * (1 - o.discount)) AS revenue,
        (o.quantity * p.unit_price * (1 - o.discount)) - (o.quantity * p.unit_cost) AS profit
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id   -- JOIN #1
    JOIN products p  ON o.product_id  = p.product_id     -- JOIN #2
)
"""

# ---- Q1: Overall KPIs ----
kpi = run_query(ORDER_METRICS_CTE + """
SELECT
    ROUND(SUM(revenue), 2)  AS total_revenue,
    ROUND(SUM(profit), 2)   AS total_profit,
    ROUND(AVG(revenue), 2)  AS avg_order_value,
    COUNT(DISTINCT customer_id) AS unique_customers,
    COUNT(*) AS total_orders
FROM order_metrics;
""")
print("\n--- Overall KPIs ---")
print(kpi)

# ---- Q2: Monthly revenue trend + Month-over-Month growth % ----
# Uses a window function LAG() to compare each month to the previous
# month -- this is the exact "revenue growth" KPI mentioned on the resume.
monthly_trend = run_query(ORDER_METRICS_CTE + """
, monthly AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        SUM(revenue) AS monthly_revenue
    FROM order_metrics
    GROUP BY month
)
SELECT
    month,
    ROUND(monthly_revenue, 2) AS monthly_revenue,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY month))
        * 100.0 / LAG(monthly_revenue) OVER (ORDER BY month), 2
    ) AS mom_growth_pct
FROM monthly
ORDER BY month;
""")
print("\n--- Monthly Revenue Trend (last 6 months) ---")
print(monthly_trend.tail(6))

# ---- Q3: Top 10 products by revenue ----
top_products = run_query(ORDER_METRICS_CTE + """
SELECT
    product_name,
    category,
    ROUND(SUM(revenue), 2) AS total_revenue,
    COUNT(*) AS orders_count
FROM order_metrics
GROUP BY product_name, category
ORDER BY total_revenue DESC
LIMIT 10;
""")
print("\n--- Top 10 Products by Revenue ---")
print(top_products)

# ---- Q4: Regional performance with average order value per region ----
# window function AVG() OVER lets us show each region's AOV alongside
# total revenue in the same result set.
regional = run_query(ORDER_METRICS_CTE + """
SELECT DISTINCT
    region,
    ROUND(SUM(revenue) OVER (PARTITION BY region), 2) AS region_total_revenue,
    ROUND(AVG(revenue) OVER (PARTITION BY region), 2) AS region_avg_order_value
FROM order_metrics
ORDER BY region_total_revenue DESC;
""")
print("\n--- Regional Performance ---")
print(regional)

# ---- Q5: Customer segmentation (Bronze/Silver/Gold/Platinum) ----
# Step 1: total spend per customer (CTE)
# Step 2: NTILE(4) window function splits customers into 4 equal-sized
#         buckets by spend -- this is the "customer segmentation" KPI.
segmentation = run_query(ORDER_METRICS_CTE + """
, customer_spend AS (
    SELECT customer_id, SUM(revenue) AS total_spend
    FROM order_metrics
    GROUP BY customer_id
),
segmented AS (
    SELECT
        customer_id,
        total_spend,
        NTILE(4) OVER (ORDER BY total_spend) AS spend_quartile
    FROM customer_spend
)
SELECT
    CASE spend_quartile
        WHEN 1 THEN 'Bronze'
        WHEN 2 THEN 'Silver'
        WHEN 3 THEN 'Gold'
        WHEN 4 THEN 'Platinum'
    END AS segment,
    COUNT(*) AS num_customers,
    ROUND(AVG(total_spend), 2) AS avg_spend
FROM segmented
GROUP BY spend_quartile
ORDER BY spend_quartile;
""")
print("\n--- Customer Segmentation ---")
print(segmentation)

# -----------------------------------------------------------------
# 3. CHARTS
# -----------------------------------------------------------------
plt.figure(figsize=(9, 4))
plt.plot(monthly_trend["month"], monthly_trend["monthly_revenue"], marker="o", color="#1f77b4")
plt.title("Monthly Revenue Trend")
plt.xticks(rotation=60)
plt.ylabel("Revenue")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/01_monthly_revenue_trend.png")
plt.close()

plt.figure(figsize=(8, 5))
plt.barh(top_products["product_name"][::-1], top_products["total_revenue"][::-1], color="#2ca02c")
plt.title("Top 10 Products by Revenue")
plt.xlabel("Revenue")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/02_top_products.png")
plt.close()

plt.figure(figsize=(6, 4))
plt.bar(regional["region"], regional["region_total_revenue"], color="#ff7f0e")
plt.title("Total Revenue by Region")
plt.ylabel("Revenue")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/03_regional_revenue.png")
plt.close()

plt.figure(figsize=(6, 4))
plt.bar(segmentation["segment"], segmentation["num_customers"],
        color=["#cd7f32", "#c0c0c0", "#ffd700", "#b9f2ff"])
plt.title("Customer Segmentation (by total spend)")
plt.ylabel("Number of Customers")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/04_customer_segmentation.png")
plt.close()

# -----------------------------------------------------------------
# 4. EXPORT A POWER-BI-READY FLAT TABLE
# -----------------------------------------------------------------
# Power BI works best off a single flat table rather than raw
# normalized tables + separate SQL queries. This exports one CSV
# with everything already joined and calculated, ready to import
# straight into Power BI (Get Data -> Text/CSV) to build the
# dashboard visuals on top of.
flat_table = run_query(ORDER_METRICS_CTE + "SELECT * FROM order_metrics;")
flat_table.to_csv(f"{OUTPUT_DIR}/powerbi_sales_flat_table.csv", index=False)
print(f"\nExported Power BI-ready flat table -> {OUTPUT_DIR}/powerbi_sales_flat_table.csv "
      f"({len(flat_table)} rows)")

print(f"\nAll charts saved to '{OUTPUT_DIR}/'.")
conn.close()
