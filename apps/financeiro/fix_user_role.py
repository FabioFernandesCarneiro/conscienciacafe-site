#!/usr/bin/env python3
"""Fix user role to admin."""
import os
import sys
from src.db import init_engine, session_scope
from src.models import CRMUser

# Initialize database
database_url = os.getenv('DATABASE_URL')
print(f"DATABASE_URL: {database_url[:30] if database_url else 'Not set'}...")

if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    print("✅ Converted postgres:// to postgresql+psycopg2://")

engine = init_engine(database_url)
print("✅ Database engine initialized")

try:
    with session_scope() as session:
        # Find user by email
        user = session.query(CRMUser).filter_by(
            email='fabiofernandescarneiro@gmail.com'
        ).first()

        if not user:
            # Try by username
            user = session.query(CRMUser).filter_by(
                username='fabiofernandescarneiro@gmail.com'
            ).first()

        if not user:
            print("❌ Usuário não encontrado!")
            print("\nUsuários existentes:")
            all_users = session.query(CRMUser).all()
            for u in all_users:
                print(f"  - ID: {u.id}, Username: {u.username}, Role: {u.role}")
            sys.exit(1)

        print(f"\n📋 Usuário encontrado:")
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Role atual: {user.role}")
        print(f"  Active: {user.active}")

        # Update role to admin
        if user.role != 'admin':
            user.role = 'admin'
            session.commit()
            print(f"\n✅ Role atualizado para 'admin' com sucesso!")
        else:
            print(f"\n✓ Usuário já é admin")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
