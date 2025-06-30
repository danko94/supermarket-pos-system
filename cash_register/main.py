from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import psycopg2
from datetime import datetime, timezone
from shared.db_config import validate_env_vars, get_db_config

app = FastAPI()

# Validate environment variables on startup
validate_env_vars()

DB_CONFIG = get_db_config()

# ----- Input model -----
class PurchaseRequest(BaseModel):
    real_id: str                  # Teudat Zehut / SSN
    supermarket_id: str           # Must be one of SMKT001, etc.
    item_names: List[str]         # List of product names


# ----- Utility DB funcs -----
def connect() -> psycopg2.extensions.connection:
    return psycopg2.connect(**DB_CONFIG)

def get_or_create_user_uuid(real_id: str) -> str:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT uuid FROM customers WHERE real_id = %s;", (real_id,))
    row = cur.fetchone()

    if row:
        user_uuid: str = row[0]
    else:
        user_uuid: str = str(uuid.uuid4())
        cur.execute("INSERT INTO customers (real_id, uuid) VALUES (%s, %s);", (real_id, user_uuid))
        conn.commit()

    cur.close()
    conn.close()
    return user_uuid

def validate_supermarket(supermarket_id: str) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM supermarkets WHERE id = %s;", (supermarket_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=400, detail="Invalid supermarket ID")
    cur.close()
    conn.close()

def validate_and_price_items(item_names: List[str]) -> float:
    conn = connect()
    cur = conn.cursor()
    total: float = 0.0
    for name in item_names:
        cur.execute("SELECT price FROM products WHERE name = %s;", (name,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail=f"Invalid product: {name}")
        total += row[0]
    cur.close()
    conn.close()
    return total

def insert_purchase(store_id: str, user_uuid: str, item_names: List[str], total: float) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO purchases (supermarket_id, timestamp, user_id, item_list, total_amount)
        VALUES (%s, %s, %s, %s, %s);
    """, (
        store_id,
        datetime.now(timezone.utc),
        user_uuid,
        item_names,
        total
    ))
    conn.commit()
    cur.close()
    conn.close()


# ----- API endpoint -----
@app.post("/purchase")
def register_purchase(purchase: PurchaseRequest) -> Dict[str, Any]:
    # 1. Validate supermarket
    validate_supermarket(purchase.supermarket_id)

    # 2. Validate items and calculate total
    total: float = validate_and_price_items(purchase.item_names)

    # 3. Get or create UUID for user
    user_uuid: str = get_or_create_user_uuid(purchase.real_id)

    # 4. Record purchase
    insert_purchase(purchase.supermarket_id, user_uuid, purchase.item_names, total)

    return {
        "status": "success",
        "uuid": user_uuid,
        "total": total,
        "message": "Purchase recorded"
    }