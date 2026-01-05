#!/usr/bin/env python3
"""
Roda aprendizado histórico automaticamente com arquivo de julho
"""

import os
from dotenv import load_dotenv
from src.omie_client import OmieClient
from src.ml_categorizer import MLCategorizer
from historical_learning import HistoricalLearningSystem

def run_automatic_learning():
    load_dotenv()
    
    print("🎯 APRENDIZADO HISTÓRICO AUTOMÁTICO")
    print("=" * 60)
    
    try:
        # Inicializar sistemas
        omie_client = OmieClient(
            app_key=os.getenv('OMIE_APP_KEY'),
            app_secret=os.getenv('OMIE_APP_SECRET')
        )
        
        ml_categorizer = MLCategorizer()
        learning_system = HistoricalLearningSystem(omie_client, ml_categorizer)
        
        print("✅ Sistemas inicializados")
        
        # Arquivo OFX de julho que sabemos ter 100% de correspondência
        ofx_path = "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/NU_826344542_01JUL2025_02JUL2025.ofx"
        
        if not os.path.exists(ofx_path):
            print("❌ Arquivo OFX não encontrado")
            return
        
        print(f"📄 Processando: {os.path.basename(ofx_path)}")
        
        # Processar arquivo histórico
        result = learning_system.process_historical_ofx(ofx_path)
        
        # Mostrar resultado
        print(f"\n📊 RESULTADO DO APRENDIZADO:")
        print("-" * 60)
        
        if result.get("status") == "success":
            print(f"✅ Processamento concluído com sucesso!")
            print(f"📚 Transações processadas: {learning_system.processed_transactions}")
            print(f"🧠 Dados de aprendizado extraídos: {learning_system.learned_transactions}")
            print(f"📈 Taxa de aprendizado: {(learning_system.learned_transactions/learning_system.processed_transactions*100):.1f}%")
            
            if learning_system.learned_transactions > 0:
                print(f"\n🚀 DADOS ENVIADOS PARA TREINAMENTO DO ML!")
                print(f"💡 Sistema pode agora categorizar automaticamente transações similares")
            
            # Mostrar estatísticas detalhadas se disponíveis
            if "details" in result:
                details = result["details"]
                if "categories_learned" in details:
                    print(f"\n📋 CATEGORIAS APRENDIDAS:")
                    for categoria, count in details["categories_learned"].items():
                        print(f"   {categoria}: {count} transações")
                
                if "clients_learned" in details:
                    print(f"\n👥 CLIENTES/FORNECEDORES APRENDIDOS:")
                    for cliente, count in details["clients_learned"].items():
                        print(f"   {cliente}: {count} transações")
        
        else:
            print(f"❌ Erro no processamento: {result.get('message', 'Erro desconhecido')}")
        
        # Mostrar erros se houver
        if learning_system.errors:
            print(f"\n⚠️ ERROS ENCONTRADOS ({len(learning_system.errors)}):")
            for i, error in enumerate(learning_system.errors[:5], 1):
                print(f"   {i}. {error}")
            if len(learning_system.errors) > 5:
                print(f"   ... e mais {len(learning_system.errors) - 5} erros")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_automatic_learning()