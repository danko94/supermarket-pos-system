# Supermarket Database System

A Docker-based supermarket database system with analytics dashboard built using FastAPI and PostgreSQL.

## Overview

This system consists of:
- **Cash Register Service**: Records customer purchases
- **Analytics Dashboard**: Provides insights on customer behavior and product performance
- **PostgreSQL Database**: Stores customer, product, and purchase data
- **Data Loading Services**: Populates initial data from CSV files

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

2. **Start the system:**
   ```bash
   docker-compose up -d
   ```

3. **Access the services:**
   - Cash Register API: http://localhost:8000
   - Analytics Dashboard: http://localhost:8001
   - Database: localhost:5432

## API Endpoints

### Cash Register (`localhost:8000`)
- `POST /purchase` - Record a new purchase

### Analytics Dashboard (`localhost:8001`)
- `GET /` - Service information
- `GET /health` - Health check
- `GET /unique-customers` - Count of unique customers
- `GET /loyal-customers` - Customers with 3+ purchases
- `GET /top-products` - Top 3 best-selling products

## Security

This system follows security best practices:
- ✅ No hardcoded credentials
- ✅ Environment variable validation
- ✅ Protected configuration files
- ✅ Comprehensive .gitignore

See `SECURITY.md` for detailed security documentation.

## Development

The system automatically loads sample data on startup from CSV files:
- `products_list.csv` - Product catalog
- `purchases.csv` - Historical purchase data
- `supermarkets.csv` - Supermarket IDs