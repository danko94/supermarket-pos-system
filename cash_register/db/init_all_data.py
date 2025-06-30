#!/usr/bin/env python3
"""
Unified data initialization script that loads all data in the correct order.
This replaces the separate load_supermarkets, load_products, and load_purchases services.
"""

import sys
from typing import NoReturn

from db.load_supermarkets import load_supermarkets
from db.load_products import load_products
from db.load_purchases import load_purchases


def main() -> None:
    """Load all data in the correct dependency order."""
    try:
        print("🚀 Starting data initialization...")
        print()
        
        # Step 1: Load supermarkets (no dependencies)
        print("📍 Loading supermarkets...")
        load_supermarkets("/app/supermarkets.csv")
        print("✅ Supermarkets loaded successfully!")
        print()
        
        # Step 2: Load products (depends on supermarkets existing)
        print("🛒 Loading products...")
        load_products("/app/products_list.csv")
        print("✅ Products loaded successfully!")
        print()
        
        # Step 3: Load purchases (depends on supermarkets and products)
        print("💳 Loading purchases...")
        load_purchases("/app/purchases.csv")
        print("✅ Purchases loaded successfully!")
        print()
        
        print("🎉 All data loaded successfully! Database is ready.")
        
    except Exception as e:
        print(f"❌ Error during data initialization: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
