

import duckdb
import pandas as pd
import os


def build_gold(silver_df: pd.DataFrame) -> dict:
    """Gold layer — business aggregations with DuckDB SQL"""

    os.makedirs('/content/sales-pipeline-dashboard/data/gold', exist_ok=True)
    os.makedirs('/content/sales-pipeline-dashboard/database', exist_ok=True)

    con = duckdb.connect('/content/sales-pipeline-dashboard/database/warehouse.duckdb')
    con.register('silver', silver_df)

    # --- Table 1: KPI Summary ---
    kpi = con.execute("""
        SELECT
            ROUND(SUM(sales), 2)                        AS total_revenue,
            ROUND(SUM(profit), 2)                       AS total_profit,
            ROUND(SUM(profit) / SUM(sales) * 100, 2)    AS profit_margin_pct,
            COUNT(DISTINCT customer_id)                 AS total_customers,
            COUNT(order_id)                             AS total_orders,
            ROUND(AVG(sales), 2)                        AS avg_order_value
        FROM silver
    """).df()

    # --- Table 2: Sales by Category + Month ---
    by_category = con.execute("""
        SELECT
            year, month, month_name, quarter,
            category,
            COUNT(order_id)              AS orders,
            ROUND(SUM(sales), 2)         AS total_sales,
            ROUND(SUM(profit), 2)        AS total_profit,
            ROUND(AVG(profit_margin_pct),2) AS avg_margin
        FROM silver
        GROUP BY year, month, month_name, quarter, category
        ORDER BY year, month
    """).df()

    # --- Table 3: Sales by Region ---
    by_region = con.execute("""
        SELECT
            region,
            segment,
            ROUND(SUM(sales), 2)            AS total_sales,
            ROUND(SUM(profit), 2)           AS total_profit,
            COUNT(DISTINCT customer_id)     AS customers,
            COUNT(order_id)                 AS orders
        FROM silver
        GROUP BY region, segment
        ORDER BY total_sales DESC
    """).df()

    # --- Table 4: Top 20 Products ---
    top_products = con.execute("""
        SELECT
            product_name, category, sub_category,
            COUNT(order_id)          AS times_ordered,
            ROUND(SUM(sales), 2)     AS total_sales,
            ROUND(SUM(profit), 2)    AS total_profit
        FROM silver
        GROUP BY product_name, category, sub_category
        ORDER BY total_sales DESC
        LIMIT 20
    """).df()

    # --- Table 5: Monthly Trend ---
    monthly_trend = con.execute("""
        SELECT
            year, month, month_name,
            ROUND(SUM(sales), 2)  AS total_sales,
            ROUND(SUM(profit), 2) AS total_profit,
            COUNT(order_id)        AS orders
        FROM silver
        GROUP BY year, month, month_name
        ORDER BY year, month
    """).df()

    con.close()

    # Save all
    tables = {
        'kpi':           kpi,
        'by_category':   by_category,
        'by_region':     by_region,
        'top_products':  top_products,
        'monthly_trend': monthly_trend,
    }
    for name, df in tables.items():
        df.to_parquet(f'/content/sales-pipeline-dashboard/data/gold/{name}.parquet', index=False)

    print(f"Gold: {len(tables)} tables built")
    return tables


def load_gold():
    path = '/content/sales-pipeline-dashboard/data/gold/kpi.parquet'
    if not os.path.exists(path):
        # from pipeline.silver import load_silver
        return build_gold(load_silver())
    return {
        name: pd.read_parquet(f'/content/sales-pipeline-dashboard/data/gold/{name}.parquet')
        for name in ['kpi', 'by_category', 'by_region', 'top_products', 'monthly_trend']
    }
