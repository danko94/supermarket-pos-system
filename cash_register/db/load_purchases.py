import csv
import psycopg2
from typing import Set, List

from shared.db_config import validate_env_vars, get_db_config

# Validate environment variables on startup
validate_env_vars()

DB_CONFIG = get_db_config()

def load_purchases(csv_path: str) -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Keep track of UUIDs we've seen to create unique customer records
    seen_uuids: Set[str] = set()
    customer_counter: int = 1
    
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            supermarket_id: str = row["supermarket_id"].strip()
            timestamp: str = row["timestamp"].strip()
            user_uuid: str = row["user_id"].strip()
            items_list: str = row["items_list"].strip()
            total_amount: float = float(row["total_amount"])
            
            # Convert comma-separated items to PostgreSQL array format
            items_array: List[str] = [item.strip() for item in items_list.split(',')]
            
            # Insert customer record if we haven't seen this UUID before
            if user_uuid not in seen_uuids:
                real_id: str = f"customer_{customer_counter:06d}"
                cur.execute("""
                    INSERT INTO customers (real_id, uuid)
                    VALUES (%s, %s)
                    ON CONFLICT (uuid) DO NOTHING;
                """, (real_id, user_uuid))
                seen_uuids.add(user_uuid)
                customer_counter += 1
            
            # Insert the purchase
            cur.execute("""
                INSERT INTO purchases (supermarket_id, timestamp, user_id, item_list, total_amount)
                VALUES (%s, %s, %s, %s, %s);
            """, (supermarket_id, timestamp, user_uuid, items_array, total_amount))
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    load_purchases("/app/purchases.csv")
    print("✅ Purchases loaded.")
