#!/usr/bin/env python3
"""
Script para executar o aprendizado histórico automaticamente
"""

import os
from dotenv import load_dotenv
from historical_learning_extrato import HistoricalLearningExtrato

def main():
    print("🎯 EXECUTANDO APRENDIZADO HISTÓRICO AUTOMÁTICO")
    print("=" * 60)
    
    try:
        # Inicializar sistema
        learning_system = HistoricalLearningExtrato()
        print("✅ Sistema inicializado")
        
        # Resetar dados existentes
        print("\n🗑️ Resetando dados de aprendizado...")
        learning_system.reset_learning_database()
        
        # Configurar arquivos de exemplo
        arquivos_exemplo = [
            {"ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/NU_826344542_12JUL2025_13JUL2025.ofx", "conta_id": "2103553430"},
            {"ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/NU_826344542_01JUL2025_02JUL2025.ofx", "conta_id": "2103553430"},
            {"ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/NU_826344542_01MAI2025_14AGO2025.ofx", "conta_id": "2103553430"},
            {"ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/Nubank_2025-03-22 (1).ofx", "conta_id": "2103553430"}
        ]
        
        # Filtrar apenas arquivos que existem
        arquivos_validos = [
            config for config in arquivos_exemplo 
            if os.path.exists(config['ofx_file'])
        ]
        
        if not arquivos_validos:
            print("❌ Nenhum arquivo de exemplo encontrado")
            return
        
        print(f"\n📋 Processando {len(arquivos_validos)} arquivo(s):")
        for config in arquivos_validos:
            print(f"   ✅ {os.path.basename(config['ofx_file'])}")
        
        # Processar arquivos
        result = learning_system.process_multiple_ofx_files(arquivos_validos)
        
        if result['status'] == 'success':
            print(f"\n🎉 APRENDIZADO CONCLUÍDO COM SUCESSO!")
            print(f"   📄 Arquivos processados: {result['files_processed']}")
            print(f"   📊 Total de matches: {result['total_transactions']}")
            print(f"   📚 Dados aprendidos: {result['learned_transactions']}")
            
            if result['learned_transactions'] > 0:
                taxa = (result['learned_transactions'] / result['total_transactions']) * 100
                print(f"   📈 Taxa de aprendizado: {taxa:.1f}%")
        else:
            print(f"\n❌ Erro no processamento: {result.get('message', 'Erro desconhecido')}")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()