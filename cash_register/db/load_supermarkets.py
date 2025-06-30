import csv
import psycopg2

from shared.db_config import validate_env_vars, get_db_config

# Validate environment variables on startup
validate_env_vars()

DB_CONFIG = get_db_config()

def load_supermarkets(csv_path: str) -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            supermarket_id: str = row["id"].strip()
            
            # Insert supermarket record
            cur.execute("""
                INSERT INTO supermarkets (id)
                VALUES (%s)
                ON CONFLICT (id) DO NOTHING;
            """, (supermarket_id,))
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    load_supermarkets("/app/supermarkets.csv")
    print("✅ Supermarkets loaded.")
