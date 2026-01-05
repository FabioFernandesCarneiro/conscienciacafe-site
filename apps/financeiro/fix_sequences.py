#!/usr/bin/env python3
"""Fix PostgreSQL sequences for tables with auto-increment primary keys."""

from __future__ import annotations

import sys
from sqlalchemy import text

from src.db import init_engine, get_session


def fix_sequence(table_name: str, column_name: str = 'id') -> None:
    """Fix a table's sequence by setting it to MAX(column) + 1."""

    engine = init_engine()
    dialect = engine.dialect.name

    if dialect != 'postgresql':
        print(f"⚠️  Este script é apenas para PostgreSQL. Banco atual: {dialect}")
        return

    sequence_name = f"{table_name}_{column_name}_seq"

    print(f"\n🔧 Corrigindo sequência para tabela '{table_name}'...")

    with engine.connect() as conn:
        # Get current max ID
        result = conn.execute(text(f"SELECT MAX({column_name}) FROM {table_name}"))
        max_id = result.scalar()

        if max_id is None:
            max_id = 0
            print(f"   ℹ️  Tabela vazia, definindo sequência para 1")
        else:
            print(f"   ℹ️  MAX({column_name}) atual: {max_id}")

        # Set sequence to max_id + 1
        next_val = max_id + 1
        conn.execute(text(f"SELECT setval('{sequence_name}', {next_val}, false)"))
        conn.commit()

        # Verify new sequence value
        result = conn.execute(text(f"SELECT last_value FROM {sequence_name}"))
        new_val = result.scalar()

        print(f"   ✅ Sequência '{sequence_name}' ajustada para: {new_val}")
        print(f"   ➡️  Próximo ID será: {new_val}")


def fix_all_sequences() -> None:
    """Fix sequences for all tables that need it."""

    tables = [
        'coffee_products',
        'coffee_packaging_prices',
        'orders',
        'order_items',
        'crm_users',
        'crm_leads',
        'crm_interactions',
        'accounts',
        'categories',
        'clients',
        'transactions',
        'import_batches',
        'ml_training_data',
    ]

    print("=" * 60)
    print("🔧 Correção de Sequências PostgreSQL")
    print("=" * 60)

    for table in tables:
        try:
            fix_sequence(table)
        except Exception as e:
            print(f"   ❌ Erro ao corrigir '{table}': {e}")

    print("\n" + "=" * 60)
    print("✅ Processo concluído!")
    print("=" * 60)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Fix specific table
        table_name = sys.argv[1]
        fix_sequence(table_name)
    else:
        # Fix all tables
        fix_all_sequences()
