"""Migration: Add commissions, exchange rates, and seller fields.

This migration adds:
- New tables: commission_rates, commissions, exchange_rates
- New columns: crm_users.country, crm_leads.user_id, orders.user_id/paid_amount/payment_status
- New column: coffee_packaging_prices.currency
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

# Add apps/gestao to path for imports
gestao_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, gestao_root)

from src.db import init_engine, Base
from src.models import *  # noqa: F401,F403


def column_exists(engine: Engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(engine: Engine, table_name: str) -> bool:
    """Check if a table exists."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def run_migration(database_url: str | None = None) -> None:
    """Run the migration to add commissions and seller fields."""
    engine = init_engine(database_url)

    print("=" * 60)
    print("Migration: Add Commissions and Sellers")
    print("=" * 60)

    with engine.connect() as conn:
        # 1. Create new tables (commission_rates, commissions, exchange_rates)
        print("\n1. Creating new tables...")
        Base.metadata.create_all(engine)

        # Verify new tables were created
        for table in ['commission_rates', 'commissions', 'exchange_rates']:
            if table_exists(engine, table):
                print(f"   ✅ Table '{table}' exists")
            else:
                print(f"   ❌ Table '{table}' not created")

        # 2. Add new columns to crm_users
        print("\n2. Adding columns to crm_users...")
        if table_exists(engine, 'crm_users'):
            if not column_exists(engine, 'crm_users', 'country'):
                conn.execute(text("ALTER TABLE crm_users ADD COLUMN country VARCHAR(2)"))
                print("   ✅ Added crm_users.country")
            else:
                print("   ⏭️  crm_users.country already exists")

        # 3. Add new columns to crm_leads
        print("\n3. Adding columns to crm_leads...")
        if table_exists(engine, 'crm_leads'):
            if not column_exists(engine, 'crm_leads', 'user_id'):
                conn.execute(text("ALTER TABLE crm_leads ADD COLUMN user_id INTEGER REFERENCES crm_users(id)"))
                print("   ✅ Added crm_leads.user_id")
            else:
                print("   ⏭️  crm_leads.user_id already exists")

        # 4. Add new columns to orders
        print("\n4. Adding columns to orders...")
        if table_exists(engine, 'orders'):
            if not column_exists(engine, 'orders', 'user_id'):
                conn.execute(text("ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES crm_users(id)"))
                print("   ✅ Added orders.user_id")
            else:
                print("   ⏭️  orders.user_id already exists")

            if not column_exists(engine, 'orders', 'paid_amount'):
                conn.execute(text("ALTER TABLE orders ADD COLUMN paid_amount NUMERIC(15, 2) DEFAULT 0"))
                print("   ✅ Added orders.paid_amount")
            else:
                print("   ⏭️  orders.paid_amount already exists")

            if not column_exists(engine, 'orders', 'payment_status'):
                conn.execute(text("ALTER TABLE orders ADD COLUMN payment_status VARCHAR DEFAULT 'pending'"))
                print("   ✅ Added orders.payment_status")
            else:
                print("   ⏭️  orders.payment_status already exists")

        # 5. Add currency column to coffee_packaging_prices
        print("\n5. Adding columns to coffee_packaging_prices...")
        if table_exists(engine, 'coffee_packaging_prices'):
            if not column_exists(engine, 'coffee_packaging_prices', 'currency'):
                conn.execute(text("ALTER TABLE coffee_packaging_prices ADD COLUMN currency VARCHAR(3) DEFAULT 'BRL'"))
                # Update existing rows to have BRL currency
                conn.execute(text("UPDATE coffee_packaging_prices SET currency = 'BRL' WHERE currency IS NULL"))
                print("   ✅ Added coffee_packaging_prices.currency (default: BRL)")
            else:
                print("   ⏭️  coffee_packaging_prices.currency already exists")

        conn.commit()

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)

    # Show final table list
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nTables in database: {', '.join(sorted(tables))}")


if __name__ == '__main__':
    run_migration()
