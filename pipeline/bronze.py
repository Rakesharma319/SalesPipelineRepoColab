
import pandas as pd
import os
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

def generate_raw_data(n_rows=2000):
    """Generate sample dirty sales data"""
    random.seed(42)

    categories = ['Electronics', 'Furniture', 'Office Supplies', 'Clothing']
    sub_categories = {
        'Electronics': ['Phones', 'Laptops', 'Tablets', 'Accessories'],
        'Furniture':   ['Chairs', 'Tables', 'Shelves', 'Desks'],
        'Office Supplies': ['Paper', 'Pens', 'Binders', 'Envelopes'],
        'Clothing':    ['Shirts', 'Pants', 'Shoes', 'Accessories']
    }
    regions   = ['North', 'South', 'East', 'West', 'Central']
    segments  = ['Consumer', 'Corporate', 'Home Office']
    shipmodes = ['Standard', 'Express', 'Same Day', 'Economy']

    data = []
    start_date = datetime(2022, 1, 1)

    for i in range(n_rows):
        cat    = random.choice(categories)
        subcat = random.choice(sub_categories[cat])
        odate  = start_date + timedelta(days=random.randint(0, 730))
        sales  = round(random.uniform(10, 5000), 2)
        profit = round(random.uniform(-300, 2000), 2)

        row = {
            'order_id':      f'ORD-{1000 + i}',
            'order_date':    odate.strftime('%Y-%m-%d'),
            'customer_id':   f'CUST-{random.randint(100, 600)}',
            'customer_name': fake.name(),
            'segment':       random.choice(segments),
            'region':        random.choice(regions),
            'city':          fake.city(),
            'category':      cat,
            'sub_category':  subcat,
            'product_name':  f'{subcat} Model-{random.randint(1, 50)}',
            'ship_mode':     random.choice(shipmodes),
            'quantity':      random.randint(1, 20),
            'discount':      random.choice([0, 0.1, 0.2, 0.3, 0.5]),
            'sales':         sales,
            'profit':        profit,
        }

        # Introduce intentional dirty data (5%)
        if random.random() < 0.05:
            row['customer_name'] = None
        if random.random() < 0.03:
            row['sales'] = None
        if random.random() < 0.02:
            row['region'] = row['region'].lower()  # inconsistent casing

        data.append(row)

    os.makedirs('/content/sales-pipeline-dashboard/data/raw', exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv('/content/sales-pipeline-dashboard/data/raw/sales_raw.csv', index=False)
    print(f"Bronze: {len(df)} rows generated")
    return df


def load_bronze():
    path = '/content/sales-pipeline-dashboard/data/raw/sales_raw.csv'
    if not os.path.exists(path):
        return generate_raw_data()
    return pd.read_csv(path)
