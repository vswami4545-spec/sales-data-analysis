# Sales Performance Dashboard

Analyzes 55,000+ sales records across customers, products, and orders using **Python, SQL (SQLite), and Power BI**.

## Data model
Three relational tables (mirrors a real sales database, not one flat file):
- `customers.csv` — 2,000 customers with region and signup date
- `products.csv` — 200 products across 5 categories with price and cost
- `orders.csv` — 55,000+ orders (2023–2024), linked to customers and products by ID

## What this project answers
1. Overall KPIs: total revenue, total profit, average order value, unique customers
2. Monthly revenue trend + month-over-month growth %
3. Top 10 products by revenue
4. Regional performance (total revenue + average order value per region)
5. Customer segmentation into Bronze/Silver/Gold/Platinum by total spend

## SQL techniques used (per the resume)
- **JOINs**: `orders` joined to `customers` and `products` to compute revenue/profit per order
- **CTEs**: a reusable `order_metrics` CTE computes revenue/profit once and is reused by every downstream query
- **Window functions**:
  - `LAG()` for month-over-month revenue growth %
  - `AVG() OVER (PARTITION BY region)` for regional average order value
  - `NTILE(4) OVER (ORDER BY total_spend)` for customer segmentation

## How to run
```bash
pip install -r requirements.txt
python generate_data.py    # creates data/customers.csv, products.csv, orders.csv
python analysis.py         # runs all SQL queries, prints KPIs, saves charts
```

## Power BI dashboard
`analysis.py` exports `output/powerbi_sales_flat_table.csv` — a single flat table with every order's revenue, profit, region, and category already calculated. Import this directly into Power BI (**Get Data → Text/CSV**) and build visuals on top of it: a revenue trend line, a regional map/bar chart, a top-products bar chart, and a customer segmentation donut chart.

## Key insights (from the generated data)
- Revenue shows a clear seasonal spike in November/December (holiday season).
- Electronics products dominate the top-10 revenue list due to high unit price.
- The North region generates the highest total revenue.
- Customer spend splits cleanly into 4 equal-sized segments (500 customers each) — Platinum customers spend roughly 2.5x what Bronze customers spend.
