#!/usr/bin/env python3
"""Quick migration script for Railway PostgreSQL."""
import psycopg2

conn = psycopg2.connect(
    host='ballast.proxy.rlwy.net',
    port=47481,
    database='railway',
    user='postgres',
    password='lJUarwKLjmYxJVpRDnxcZWtjXdrJboKv',
    connect_timeout=10
)
conn.autocommit = True
cur = conn.cursor()

print("=" * 60)
print("Migration: Add Commissions and Sellers")
print("=" * 60)

def column_exists(table, column):
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s AND column_name = %s", (table, column))
    return cur.fetchone() is not None

def table_exists(table):
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name = %s", (table,))
    return cur.fetchone() is not None

# 1. commission_rates
print("\n1. commission_rates...")
if not table_exists('commission_rates'):
    cur.execute("CREATE TABLE commission_rates (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES crm_users(id), rate NUMERIC(5,2) NOT NULL, start_date DATE NOT NULL, end_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by INTEGER REFERENCES crm_users(id))")
    print("   Created")
else:
    print("   Exists")

# 2. commissions
print("2. commissions...")
if not table_exists('commissions'):
    cur.execute("CREATE TABLE commissions (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES crm_users(id), order_id INTEGER NOT NULL REFERENCES orders(id), amount NUMERIC(15,2) NOT NULL, amount_brl NUMERIC(15,2), rate_applied NUMERIC(5,2) NOT NULL, status VARCHAR DEFAULT 'pending', payment_date DATE, payment_reference VARCHAR, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    print("   Created")
else:
    print("   Exists")

# 3. exchange_rates
print("3. exchange_rates...")
if not table_exists('exchange_rates'):
    cur.execute("CREATE TABLE exchange_rates (id SERIAL PRIMARY KEY, from_currency VARCHAR(3) NOT NULL, to_currency VARCHAR(3) NOT NULL, rate NUMERIC(15,6) NOT NULL, effective_date DATE NOT NULL, created_by INTEGER REFERENCES crm_users(id), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    print("   Created")
else:
    print("   Exists")

# 4. crm_users.country
print("4. crm_users.country...")
if not column_exists('crm_users', 'country'):
    cur.execute("ALTER TABLE crm_users ADD COLUMN country VARCHAR(2)")
    print("   Added")
else:
    print("   Exists")

# 5. crm_leads.user_id
print("5. crm_leads.user_id...")
if not column_exists('crm_leads', 'user_id'):
    cur.execute("ALTER TABLE crm_leads ADD COLUMN user_id INTEGER REFERENCES crm_users(id)")
    print("   Added")
else:
    print("   Exists")

# 6. orders columns
print("6. orders.user_id...")
if not column_exists('orders', 'user_id'):
    cur.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES crm_users(id)")
    print("   Added")
else:
    print("   Exists")

print("7. orders.paid_amount...")
if not column_exists('orders', 'paid_amount'):
    cur.execute("ALTER TABLE orders ADD COLUMN paid_amount NUMERIC(15,2) DEFAULT 0")
    print("   Added")
else:
    print("   Exists")

print("8. orders.payment_status...")
if not column_exists('orders', 'payment_status'):
    cur.execute("ALTER TABLE orders ADD COLUMN payment_status VARCHAR DEFAULT 'pending'")
    print("   Added")
else:
    print("   Exists")

# 9. coffee_packaging_prices.currency
print("9. coffee_packaging_prices.currency...")
if not column_exists('coffee_packaging_prices', 'currency'):
    cur.execute("ALTER TABLE coffee_packaging_prices ADD COLUMN currency VARCHAR(3) DEFAULT 'BRL'")
    cur.execute("UPDATE coffee_packaging_prices SET currency = 'BRL' WHERE currency IS NULL")
    print("   Added")
else:
    print("   Exists")

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)
conn.close()
