from fastapi import FastAPI, HTTPException
import psycopg2
from typing import Dict, Any, List
from shared.db_config import validate_env_vars, get_db_config, get_db_connection

app = FastAPI(title="Supermarket Analytics Dashboard", version="1.0.0")

# Validate environment variables on startup
validate_env_vars()

DB_CONFIG = get_db_config()

def get_dashboard_db_connection() -> psycopg2.extensions.connection:
    """Get database connection with dashboard-specific error handling"""
    try:
        return get_db_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/")
def read_root() -> Dict[str, str]:
    """Dashboard home endpoint"""
    return {"message": "Supermarket Analytics Dashboard API", "version": "1.0.0"}

@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    try:
        conn = get_dashboard_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/unique-customers")
def get_unique_customers() -> Dict[str, Any]:
    """Get total count of unique customers in the chain"""
    try:
        conn = get_dashboard_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(DISTINCT user_id) FROM purchases;")
        count: int = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return {
            "unique_customers": count,
            "description": "Total number of unique customers who made purchases in the chain"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/loyal-customers")
def get_loyal_customers() -> Dict[str, Any]:
    """Get list of loyal customers (customers with at least 3 purchases)"""
    try:
        conn = get_dashboard_db_connection()
        cur = conn.cursor()
        
        query = """
        SELECT 
            c.real_id,
            c.uuid,
            COUNT(p.id) as purchase_count,
            SUM(p.total_amount) as total_spent
        FROM customers c
        JOIN purchases p ON c.uuid = p.user_id
        GROUP BY c.real_id, c.uuid
        HAVING COUNT(p.id) >= 3
        ORDER BY purchase_count DESC, total_spent DESC;
        """
        
        cur.execute(query)
        results = cur.fetchall()
        
        loyal_customers: List[Dict[str, Any]] = []
        for row in results:
            loyal_customers.append({
                "customer_id": row[0],
                "customer_uuid": str(row[1]),
                "purchase_count": row[2],
                "total_spent": float(row[3])
            })
        
        cur.close()
        conn.close()
        
        return {
            "loyal_customers": loyal_customers,
            "criteria": "Customers with 3+ purchases",
            "count": len(loyal_customers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/top-products")
def get_top_products() -> Dict[str, Any]:
    """Get top 3 best-selling products of all time (including ties)"""
    try:
        conn = get_dashboard_db_connection()
        cur = conn.cursor()
        
        # First, get the top 3 unique sales counts
        count_query = """
        WITH product_sales AS (
            SELECT 
                unnest(item_list) as product_name,
                COUNT(*) as sales_count
            FROM purchases 
            GROUP BY unnest(item_list)
        )
        SELECT DISTINCT sales_count
        FROM product_sales
        ORDER BY sales_count DESC
        LIMIT 3;
        """
        
        cur.execute(count_query)
        top_counts: List[int] = [row[0] for row in cur.fetchall()]
        
        # Now get all products that have sales counts in the top 3
        if top_counts:
            products_query = """
            WITH product_sales AS (
                SELECT 
                    unnest(item_list) as product_name,
                    COUNT(*) as sales_count
                FROM purchases 
                GROUP BY unnest(item_list)
            )
            SELECT 
                product_name,
                sales_count
            FROM product_sales
            WHERE sales_count = ANY(%s)
            ORDER BY sales_count DESC, product_name ASC;
            """
            
            cur.execute(products_query, (top_counts,))
            results = cur.fetchall()
            
            top_products: List[Dict[str, Any]] = []
            for row in results:
                top_products.append({
                    "product_name": row[0],
                    "sales_count": row[1]
                })
        else:
            top_products: List[Dict[str, Any]] = []
        
        cur.close()
        conn.close()
        
        return {
            "top_products": top_products,
            "description": "Top 3 best-selling products of all time (including ties in popularity)",
            "count": len(top_products)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))