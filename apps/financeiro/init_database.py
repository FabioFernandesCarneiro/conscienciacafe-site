#!/usr/bin/env python3
"""
Script para inicializar o banco de dados PostgreSQL com todas as tabelas
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("🔧 Inicializando banco de dados PostgreSQL...\n")

# Verificar DATABASE_URL
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("❌ DATABASE_URL não configurado no .env")
    sys.exit(1)

print(f"📋 Conectando ao banco: {db_url[:30]}...{db_url[-20:]}\n")

try:
    from src.db import init_engine, Base
    from src.models import (
        CoffeeProduct, CoffeePackagingPrice, Order, OrderItem,
        CRMUser, Account, Category, Client, Transaction,
        ImportBatch, MLTrainingData, CRMLead, CRMInteraction
    )

    # Inicializar engine
    engine = init_engine(db_url)
    print(f"✅ Engine criado: {engine.dialect.name}")

    # Listar modelos carregados
    print("\n📦 Modelos carregados:")
    models = [
        'CRMUser', 'Account', 'Category', 'Client', 'Transaction',
        'ImportBatch', 'MLTrainingData', 'CRMLead', 'CRMInteraction',
        'CoffeeProduct', 'CoffeePackagingPrice', 'Order', 'OrderItem'
    ]
    for model in models:
        print(f"   ✓ {model}")

    # Criar todas as tabelas
    print("\n🔨 Criando tabelas no banco de dados...")
    Base.metadata.create_all(engine)

    # Listar tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\n✅ Banco de dados inicializado com sucesso!")
    print(f"\n📊 Tabelas criadas ({len(tables)}):")
    for table in sorted(tables):
        columns = inspector.get_columns(table)
        print(f"   - {table} ({len(columns)} colunas)")

    print("\n" + "="*60)
    print("✅ BANCO DE DADOS PRONTO PARA USO!")
    print("="*60)

except Exception as e:
    print(f"\n❌ Erro ao inicializar banco: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
