#!/usr/bin/env python3
"""
Migração Completa desde 2023 - Todas as contas
Executa migração histórica completa de todas as contas descobertas
"""

import os
from datetime import date
from dotenv import load_dotenv
from omie_migration import OmieMigration
from src.database_manager import DEFAULT_DB_PATH
import time

def run_full_migration_2023():
    """Executa migração completa desde 2023"""
    print("🚀 MIGRAÇÃO COMPLETA DESDE 2023")
    print("=" * 60)

    try:
        migration = OmieMigration()

        # Definir período completo
        migration.start_date = date(2023, 1, 1)
        migration.end_date = date.today()

        print(f"📅 Período completo: {migration.start_date} até {migration.end_date}")
        print(f"🏦 Total de contas descobertas: {len(migration.discovered_accounts)}")

        # Confirmar com usuário
        print("\n⚠️ ATENÇÃO: Esta migração pode demorar vários minutos")
        print("   Processará todos os extratos desde Janeiro/2023")
        print("   Recomendado: Execute em horário de baixo uso")

        # Executar migração completa
        print(f"\n🔄 Iniciando migração completa...")
        start_time = time.time()

        migration.run_full_migration()

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n⏰ Tempo total de migração: {duration:.1f} segundos")
        print(f"📊 Migração de {len(migration.discovered_accounts)} contas concluída!")

        # Estatísticas finais
        stats = migration.db.get_statistics()
        print(f"\n📈 ESTATÍSTICAS FINAIS:")
        print(f"🏦 Contas ativas: {stats['total_accounts']}")
        print(f"🏷️ Categorias ativas: {stats['total_categories']}")
        print(f"👥 Clientes/Fornecedores: {stats['total_clients']}")
        print(f"💰 Total de transações: {stats['total_transactions']}")

        if stats['date_range']['start'] and stats['date_range']['end']:
            print(f"📅 Período dos dados: {stats['date_range']['start']} até {stats['date_range']['end']}")

        print(f"\n✅ MIGRAÇÃO COMPLETA FINALIZADA!")
        print(f"💾 Dados salvos em: {DEFAULT_DB_PATH}")
        print(f"🎯 Próximo passo: Adaptar aplicação web para usar dados locais")

    except KeyboardInterrupt:
        print(f"\n⚠️ Migração interrompida pelo usuário")
        print(f"💡 Progresso salvo no banco. Pode ser retomada posteriormente.")
    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        print(f"🔧 Verifique logs e configurações")

def show_migration_progress():
    """Mostra progresso da migração em andamento"""
    from src.database_manager import DatabaseManager

    db = DatabaseManager()
    stats = db.get_statistics()

    print(f"📊 PROGRESSO ATUAL:")
    print(f"🏦 Contas: {stats['total_accounts']}")
    print(f"💰 Transações: {stats['total_transactions']}")

    if stats['total_transactions'] > 0:
        print(f"📅 Dados de: {stats['date_range']['start']} até {stats['date_range']['end']}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_migration_progress()
    else:
        run_full_migration_2023()
