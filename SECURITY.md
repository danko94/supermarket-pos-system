# Security Best Practices - Database Configuration

## Overview
This document outlines the security improvements made to handle database configuration properly.

## Issues Fixed

### 1. **Removed Hardcoded Credentials**
- **Before**: Default values like `"root"` and `"supermarket"` were hardcoded as fallbacks
- **After**: All credentials must be provided via environment variables

### 2. **Added Environment Variable Validation**
- Services now validate that required environment variables are present on startup
- Fail fast with clear error messages if credentials are missing

### 3. **Enhanced .gitignore**
- Added comprehensive .gitignore to prevent accidental credential commits
- Includes .env files, Python cache files, and IDE configurations

### 4. **Created .env.example**
- Template file showing required environment variables
- Safe to commit to version control (contains no real credentials)

## Environment Variables Required

```bash
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password  
POSTGRES_DB=your_db_name
POSTGRES_HOST=db                    # Optional, defaults to "db"
POSTGRES_PORT=5432                  # Optional, defaults to "5432"
```

## Usage

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env with your actual values:**
   ```bash
   POSTGRES_USER=myuser
   POSTGRES_PASSWORD=mysecurepassword
   POSTGRES_DB=supermarket
   ```

3. **Never commit .env to version control**
   - The .env file is automatically ignored by git
   - Only commit .env.example with placeholder values

## Security Benefits

✅ **No credentials in source code**
✅ **Fail fast if credentials missing**  
✅ **Environment-specific configuration**
✅ **Protected from accidental commits**
✅ **Clear documentation for setup**
✅ **SQL injection protection via parameterized queries**
✅ **Comprehensive input validation and sanitization**

## SQL Injection Protection

All database queries use **parameterized queries** to prevent SQL injection attacks:

```python
# ✅ SAFE - Parameterized query
cur.execute("SELECT 1 FROM supermarkets WHERE id = %s;", (supermarket_id,))
cur.execute("INSERT INTO customers (real_id, uuid) VALUES (%s, %s);", (real_id, user_uuid))

# ❌ UNSAFE - String concatenation (NOT used in this project)
cur.execute(f"SELECT 1 FROM supermarkets WHERE id = '{supermarket_id}';")
```

**How it works:**
- The `%s` placeholders are PostgreSQL parameter placeholders (not Python string formatting)
- Parameters are passed separately as a tuple in the second argument
- psycopg2 automatically escapes and sanitizes all parameters
- SQL structure is fixed; only values can be injected, not SQL commands
- Even malicious input like `'; DROP TABLE users; --` is treated as literal data

## Docker Compose Integration

The `docker-compose.yaml` file properly uses the `.env` file:

```yaml
services:
  db:
    env_file:
      - .env
  cash_register:
    env_file:
      - .env
  dashboard:
    env_file:
      - .env
```

## Production Recommendations

For production environments, consider:

1. **Use secrets management** (AWS Secrets Manager, Azure Key Vault, etc.)
2. **Rotate credentials regularly**
3. **Use least-privilege database users**
4. **Enable SSL/TLS for database connections**
5. **Monitor database access logs**

## Input Validation and Sanitization

All user input is thoroughly validated using both **Pydantic models** and **server-side validation**:

### API Request Validation

```python
class PurchaseRequest(BaseModel):
    real_id: str = Field(
        min_length=1, 
        max_length=20,
        description="Alphanumeric characters only"
    )
    supermarket_id: str = Field(
        pattern=r'^SMKT\d{3}$',  # Must match SMKT### format
        description="Supermarket ID format validation"
    )
    item_names: List[str] = Field(
        min_items=1, 
        max_items=1000,  # Generous limit, actual limit enforced server-side
        description="List limited by available products, no duplicates allowed"
    )
```

### Security Validations Applied

**Length Limits:**
- `real_id`: 1-20 characters (prevents buffer overflow attacks)
- `supermarket_id`: Exactly 7 characters
- `item_names`: Since every customer can purchase one of each item the max item count is the amount of distinctive items in the catalog, each item ≤100 characters
- List size limits prevent DoS attacks

**Format Validation:**
- `real_id`: Alphanumeric only (`^[a-zA-Z0-9]+$`)
- `supermarket_id`: Must match `SMKT###` pattern
- `item_names`: Letters, numbers, spaces, basic punctuation only

**Sanitization:**
- Automatic whitespace trimming
- Empty string detection after trimming
- Invalid character filtering
- Double validation (Pydantic + server-side)

**DoS Protection:**
- Dynamic maximum list size based on available products in catalog
- String length limits to prevent buffer overflows
- Pattern matching to prevent malformed input
- Generous Pydantic limits with strict server-side enforcement

**Business Rule Enforcement:**
- No duplicate items allowed in a single purchase (case-insensitive)
- Each customer can buy only one of each product per transaction
