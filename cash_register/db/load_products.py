import csv
import psycopg2

from shared.db_config import validate_env_vars, get_db_config

# Validate environment variables on startup
validate_env_vars()

DB_CONFIG = get_db_config()

def load_products(csv_path: str) -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name: str = row["product_name"].strip()
            price: float = float(row["unit_price"])
            cur.execute("""
                INSERT INTO products (name, price)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING;
            """, (name, price))

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    load_products("products_list.csv")
    print("✅ Products loaded.")