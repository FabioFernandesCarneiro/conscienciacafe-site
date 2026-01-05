#!/usr/bin/env python3
"""
Script para migrar dados do SQLite local para PostgreSQL do Railway
"""

import os
import sys
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("🔄 Migração SQLite → PostgreSQL")
print("=" * 60)

# Verificar DATABASE_URL
db_url = os.getenv('DATABASE_URL')
if not db_url or not db_url.startswith('postgresql'):
    print("❌ DATABASE_URL não configurado para PostgreSQL no .env")
    sys.exit(1)

# Configurar paths
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'local_financeiro.db')

if not os.path.exists(SQLITE_PATH):
    print(f"❌ Banco SQLite não encontrado: {SQLITE_PATH}")
    sys.exit(1)

print(f"📂 Origem: {SQLITE_PATH}")
print(f"🎯 Destino: {db_url[:30]}...{db_url[-20:]}\n")

# Importar SQLAlchemy e modelos
try:
    from src.db import init_engine, Base, session_scope
    from src.models import (
        CRMUser, Account, Category, Client, Transaction, ImportBatch,
        MLTrainingData, CRMLead, CRMInteraction, CoffeeProduct,
        CoffeePackagingPrice, Order, OrderItem
    )
    from sqlalchemy import text
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)

# Inicializar PostgreSQL
print("🔧 Inicializando PostgreSQL...")
engine = init_engine(db_url)

# Criar todas as tabelas
print("📦 Criando estrutura de tabelas...")
Base.metadata.create_all(engine)
print("✅ Tabelas criadas\n")

# Conectar ao SQLite
print("📖 Conectando ao SQLite...")
sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# Estatísticas
stats = {
    'crm_users': 0,
    'accounts': 0,
    'categories': 0,
    'clients': 0,
    'transactions': 0,
    'import_batches': 0,
    'ml_training_data': 0,
    'crm_leads': 0,
    'crm_interactions': 0,
    'coffee_products': 0,
    'coffee_packaging_prices': 0,
    'orders': 0,
    'order_items': 0,
    'errors': []
}

def migrate_table(table_name, model_class, transform_fn=None):
    """Migra uma tabela do SQLite para PostgreSQL"""
    print(f"📋 Migrando {table_name}...", end=" ")

    try:
        # Ler dados do SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()

        if not rows:
            print("(vazio)")
            return

        # Inserir no PostgreSQL
        with session_scope() as session:
            for row in rows:
                row_dict = dict(row)

                # Aplicar transformação se necessário
                if transform_fn:
                    row_dict = transform_fn(row_dict)

                # Criar objeto do modelo
                obj = model_class(**row_dict)
                session.add(obj)
                stats[table_name] += 1

        print(f"✅ {stats[table_name]} registros")

    except Exception as e:
        error_msg = f"❌ Erro em {table_name}: {e}"
        print(error_msg)
        stats['errors'].append(error_msg)

# Funções de transformação para ajustar dados
def transform_date_fields(row_dict):
    """Converte strings de data/datetime do SQLite"""
    for key, value in row_dict.items():
        if value and isinstance(value, str):
            # Tentar converter timestamps
            if 'created_at' in key or 'updated_at' in key or 'at' in key or 'date' in key:
                try:
                    if len(value) == 10:  # YYYY-MM-DD
                        from datetime import date
                        parts = value.split('-')
                        row_dict[key] = date(int(parts[0]), int(parts[1]), int(parts[2]))
                    else:  # Datetime completo
                        row_dict[key] = datetime.fromisoformat(value.replace(' ', 'T'))
                except:
                    pass
    return row_dict

# Migrar cada tabela na ordem correta (respeitando foreign keys)
print("\n🚀 Iniciando migração...\n")

# 1. Tabelas independentes (sem foreign keys)
migrate_table('crm_users', CRMUser, transform_date_fields)
migrate_table('accounts', Account, transform_date_fields)
migrate_table('categories', Category, transform_date_fields)
migrate_table('clients', Client, transform_date_fields)
migrate_table('import_batches', ImportBatch, transform_date_fields)
migrate_table('coffee_products', CoffeeProduct, transform_date_fields)

# 2. Tabelas dependentes
migrate_table('transactions', Transaction, transform_date_fields)
migrate_table('ml_training_data', MLTrainingData, transform_date_fields)
migrate_table('crm_leads', CRMLead, transform_date_fields)
migrate_table('crm_interactions', CRMInteraction, transform_date_fields)
migrate_table('coffee_packaging_prices', CoffeePackagingPrice, transform_date_fields)
migrate_table('orders', Order, transform_date_fields)
migrate_table('order_items', OrderItem, transform_date_fields)

# Fechar SQLite
sqlite_conn.close()

# Resumo
print("\n" + "=" * 60)
print("📊 RESUMO DA MIGRAÇÃO")
print("=" * 60)

total_migrated = 0
for table, count in stats.items():
    if table != 'errors' and count > 0:
        print(f"  ✅ {table:30} {count:6} registros")
        total_migrated += count

print(f"\n  📦 Total migrado: {total_migrated} registros")

if stats['errors']:
    print(f"\n  ⚠️  Erros encontrados ({len(stats['errors'])}):")
    for error in stats['errors']:
        print(f"     {error}")
else:
    print("\n  ✅ Migração concluída sem erros!")

print("=" * 60)

# Verificar usuários migrados
print("\n🔐 Verificando usuários migrados...")
try:
    with session_scope() as session:
        users = session.query(CRMUser).all()
        print(f"  Total de usuários: {len(users)}")
        for user in users:
            print(f"    - {user.username} ({user.role}) - {'ativo' if user.active else 'inativo'}")
except Exception as e:
    print(f"  ❌ Erro ao verificar usuários: {e}")

print("\n✅ Migração finalizada!")
print("   Você já pode fazer login no sistema usando o PostgreSQL do Railway")
