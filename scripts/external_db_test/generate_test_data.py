#!/usr/bin/env python3
"""Generate test data for external database testing."""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.external_db.setup.schema_generator import create_schema
from tests.external_db.setup.data_generator import DataGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate test data for external database")
    parser.add_argument(
        "--database-url",
        default=os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pylight_test"),
        help="Database connection string"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.getenv("TEST_DATA_SEED", "42")),
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--records-per-table",
        type=int,
        default=int(os.getenv("RECORDS_PER_TABLE", "1000")),
        help="Number of records per table (for tables that use this value)"
    )
    parser.add_argument(
        "--skip-schema",
        action="store_true",
        help="Skip schema creation (assume schema already exists)"
    )
    
    args = parser.parse_args()
    
    print("=== Generating Test Data ===")
    print(f"Database: {args.database_url}")
    print(f"Seed: {args.seed}")
    print(f"Records per table: {args.records_per_table}")
    
    # Create schema if needed
    if not args.skip_schema:
        print("\nCreating database schema...")
        create_schema(args.database_url, drop_existing=True)
    
    # Generate test data
    print("\nGenerating test data...")
    generator = DataGenerator(args.database_url, seed=args.seed)
    
    # Calculate record counts based on requirements
    users = args.records_per_table
    categories = 50
    products = args.records_per_table
    orders = args.records_per_table * 2  # 2000 orders
    reviews = args.records_per_table * 3  # 3000 reviews
    
    generator.generate_all(
        users=users,
        categories=categories,
        products=products,
        orders=orders,
        reviews=reviews
    )
    
    print("\n✓ Test data generation complete")


if __name__ == "__main__":
    main()

