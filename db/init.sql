-- 1. Customers table: maps real IDs (SSN/Teudat Zehut) to UUIDs
CREATE TABLE IF NOT EXISTS customers (
    real_id VARCHAR PRIMARY KEY,
    uuid UUID NOT NULL UNIQUE
);

-- 2. Supermarkets table: predefined list of store IDs
CREATE TABLE IF NOT EXISTS supermarkets (
    id VARCHAR PRIMARY KEY
);

-- 3. Products table: loaded from CSV
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    price FLOAT NOT NULL
);

-- 4. Purchases table
CREATE TABLE IF NOT EXISTS purchases (
    id SERIAL PRIMARY KEY,
    supermarket_id VARCHAR NOT NULL REFERENCES supermarkets(id),
    timestamp TIMESTAMP NOT NULL,
    user_id UUID NOT NULL REFERENCES customers(uuid),
    item_list TEXT[] NOT NULL,
    total_amount FLOAT NOT NULL
);