"""
Shared database configuration utilities for the supermarket system.
"""
import os
import psycopg2
from typing import Dict, Any


def validate_env_vars() -> None:
    """Validate that all required environment variables are set"""
    required_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def get_db_config() -> Dict[str, Any]:
    """Get database configuration from environment variables"""
    validate_env_vars()
    
    return {
        'dbname': os.getenv("POSTGRES_DB"),
        'user': os.getenv("POSTGRES_USER"),
        'password': os.getenv("POSTGRES_PASSWORD"),
        'host': os.getenv("POSTGRES_HOST", "db"),
        'port': os.getenv("POSTGRES_PORT", "5432")
    }


def get_db_connection() -> psycopg2.extensions.connection:
    """Get database connection using validated configuration"""
    config = get_db_config()
    return psycopg2.connect(**config)
