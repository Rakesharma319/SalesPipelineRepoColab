
import pandas as pd
import os


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Silver layer — clean, fix types, add derived columns"""

    # 1. Remove duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"Silver: Removed {before - len(df)} duplicates")

    # 2. Fix missing values
    df['customer_name'] = df['customer_name'].fillna('Unknown')
    df['sales']         = df['sales'].fillna(df['sales'].median())

    # 3. Fix inconsistent casing
    df['region']   = df['region'].str.strip().str.title()
    df['category'] = df['category'].str.strip().str.title()

    # 4. Fix data types
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['sales']      = df['sales'].astype(float).round(2)
    df['profit']     = df['profit'].astype(float).round(2)

    # 5. Derived columns
    df['year']                  = df['order_date'].dt.year
    df['month']                 = df['order_date'].dt.month
    df['month_name']            = df['order_date'].dt.strftime('%b')
    df['quarter']               = 'Q' + df['order_date'].dt.quarter.astype(str)
    df['net_sales']             = (df['sales'] * (1 - df['discount'])).round(2)
    df['profit_margin_pct']     = (df['profit'] / df['sales'] * 100).round(2)

    os.makedirs('/content/sales-pipeline-dashboard/data/silver', exist_ok=True)
    df.to_parquet('/content/sales-pipeline-dashboard/data/silver/sales_silver.parquet', index=False)
    print(f"Silver: {len(df)} clean rows saved")
    return df


def load_silver():
    path = '/content/sales-pipeline-dashboard/data/silver/sales_silver.parquet'
    if not os.path.exists(path):
        # from pipeline.bronze import load_bronze
        return clean_data(load_bronze())
    return pd.read_parquet(path)
