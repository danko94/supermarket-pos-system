from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any
import uuid
import psycopg2
import re
from datetime import datetime, timezone
from shared.db_config import validate_env_vars, get_db_config

app = FastAPI()

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Validate environment variables on startup
validate_env_vars()

DB_CONFIG = get_db_config()

# ----- Input model -----
class PurchaseRequest(BaseModel):
    real_id: str = Field(
        ..., 
        min_length=1, 
        max_length=20,
        description="Teudat Zehut / SSN - alphanumeric characters only"
    )
    supermarket_id: str = Field(
        ..., 
        min_length=7, 
        max_length=7,
        pattern=r'^SMKT\d{3}$',
        description="Supermarket ID in format SMKT### (e.g., SMKT001)"
    )
    item_names: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=1000,  # Generous limit, actual limit enforced server-side
        description="List of product names (max determined by available products)"
    )
    
    @validator('real_id')
    def validate_real_id(cls, v: str) -> str:
        # Remove any whitespace
        v = v.strip()
        
        # Check if empty after stripping
        if not v:
            raise ValueError('real_id cannot be empty')
        
        # Allow only alphanumeric characters (letters and numbers)
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('real_id must contain only alphanumeric characters')
        
        return v
    
    @validator('item_names')
    def validate_item_names(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError('item_names cannot be empty')
        
        validated_items = []
        seen_items = set()
        
        for item in v:
            # Strip whitespace
            item = item.strip()
            
            # Check if empty after stripping
            if not item:
                raise ValueError('Item names cannot be empty')
            
            # Length check for each item
            if len(item) > 100:
                raise ValueError('Item names cannot exceed 100 characters')
            
            # Allow only letters, numbers, spaces, hyphens, and basic punctuation
            if not re.match(r'^[a-zA-Z0-9\s\-\.\,\'\"]+$', item):
                raise ValueError('Item names contain invalid characters')
            
            # Check for duplicates (case-insensitive)
            item_lower = item.lower()
            if item_lower in seen_items:
                raise ValueError(f'Duplicate item not allowed: {item}')
            
            seen_items.add(item_lower)
            validated_items.append(item)
        
        return validated_items


# ----- Utility DB funcs -----
def connect() -> psycopg2.extensions.connection:
    return psycopg2.connect(**DB_CONFIG)

def get_max_items_count() -> int:
    """Get the maximum number of unique items a customer can purchase (total products in catalog)"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

def get_or_create_user_uuid(real_id: str) -> str:
    # Additional server-side validation
    real_id = real_id.strip()
    if not real_id:
        raise HTTPException(status_code=400, detail="real_id cannot be empty")
    
    if len(real_id) > 20:
        raise HTTPException(status_code=400, detail="real_id too long")
    
    if not re.match(r'^[a-zA-Z0-9]+$', real_id):
        raise HTTPException(status_code=400, detail="real_id contains invalid characters")
    
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
    if not item_names:
        raise HTTPException(status_code=400, detail="Item list cannot be empty")
    
    max_items = get_max_items_count()
    if len(item_names) > max_items:
        raise HTTPException(status_code=400, detail=f"Too many items (maximum {max_items} unique products available in catalog)")
    
    # Check for duplicates (case-insensitive)
    seen_items = set()
    normalized_items = []
    
    for name in item_names:
        # Additional server-side validation
        name = name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Item name cannot be empty")
        
        if len(name) > 100:
            raise HTTPException(status_code=400, detail="Item name too long")
        
        # Check for duplicates
        name_lower = name.lower()
        if name_lower in seen_items:
            raise HTTPException(status_code=400, detail=f"Duplicate item not allowed: {name}")
        
        seen_items.add(name_lower)
        normalized_items.append(name)
    
    conn = connect()
    cur = conn.cursor()
    total: float = 0.0
    
    for name in normalized_items:
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


# ----- UI Routes -----
def get_all_products():
    """Get all products from database for UI"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("SELECT name, price FROM products ORDER BY name")
    products = [{"name": row[0], "price": float(row[1])} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return products


def get_all_supermarkets():
    """Get all supermarket IDs for UI"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM supermarkets ORDER BY id")
    supermarkets = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return supermarkets


@app.get("/", response_class=HTMLResponse)
def select_supermarket(request: Request):
    """Serve the supermarket selection page"""
    supermarkets = get_all_supermarkets()
    
    return templates.TemplateResponse("select_supermarket.html", {
        "request": request,
        "supermarkets": supermarkets
    })

@app.get("/cash-register", response_class=HTMLResponse)
def cash_register_ui(request: Request, supermarket_id: str):
    """Serve the cash register UI for a specific supermarket"""
    products = get_all_products()
    supermarkets = get_all_supermarkets()
    
    # Validate that the supermarket_id exists
    if supermarket_id not in supermarkets:
        raise HTTPException(status_code=400, detail="Invalid supermarket ID")
    
    return templates.TemplateResponse("cash_register.html", {
        "request": request,
        "products": products,
        "supermarkets": supermarkets,
        "supermarket_id": supermarket_id
    })