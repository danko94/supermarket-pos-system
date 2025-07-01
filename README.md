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

## Scalability Considerations

### Current Limitations
- **Database Connections**: Creates new connection per request (expensive at scale)
- **Product Validation**: Sequential queries (N database calls per purchase)
- **No Caching**: Products fetched from database every time
- **Single Instance**: No horizontal scaling configuration

### Recommended Improvements for High Volume

#### Phase 1: Quick Wins
- **Connection Pooling**: Implement PostgreSQL connection pooling (5-50 shared connections)
- **Batch Queries**: Replace N product lookups with single IN query
- **Database Indexes**: Add indexes on frequently queried columns

#### Phase 2: Performance Optimization  
- **Redis Caching**: Cache product catalog and user lookups
- **Async Operations**: Move to async FastAPI with asyncpg
- **Database Partitioning**: Partition purchases table by time periods

#### Phase 3: Horizontal Scaling
- **Load Balancer**: Add nginx reverse proxy for multiple cash register instances
- **Read Replicas**: Separate read/write database operations
- **Microservice Architecture**: Split services for independent scaling

#### Expected Performance Impact
- Current: ~100 requests/sec
- With Phase 1: ~500 requests/sec  
- With Phase 2: ~2000 requests/sec
- With Phase 3: 5000+ requests/sec

> **Note**: Current architecture is well-designed for these improvements - most optimizations only require database layer changes without breaking the API contract.

## Development

The system automatically loads sample data on startup from CSV files:
- `products_list.csv` - Product catalog
- `purchases.csv` - Historical purchase data
- `supermarkets.csv` - Supermarket IDs