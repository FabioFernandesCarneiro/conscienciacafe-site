#!/usr/bin/env python3
"""
Script para executar aprendizado histórico com arquivos específicos
Foca nos dois arquivos importantes: Nubank PJ e Cartão Mastercard
"""

import os
from dotenv import load_dotenv
from historical_learning_extrato import HistoricalLearningExtrato
from src.ofx_detector import comprehensive_ofx_analysis

def main():
    print("🎯 APRENDIZADO HISTÓRICO COM ARQUIVOS ESPECÍFICOS")
    print("=" * 70)
    
    try:
        # Inicializar sistema
        learning_system = HistoricalLearningExtrato()
        print("✅ Sistema inicializado")
        
        # Configurar arquivos específicos
        arquivos_especificos = [
            {
                "ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/NU_826344542_01MAI2025_14AGO2025.ofx", 
                "descricao": "Nubank PJ (período longo)"
            },
            {
                "ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/Nubank_2025-03-22 (1).ofx", 
                "descricao": "Cartão Mastercard Nubank"
            }
        ]
        
        # Detectar contas automaticamente e preparar configuração
        configs_finais = []
        
        for config in arquivos_especificos:
            ofx_file = config["ofx_file"]
            descricao = config["descricao"]
            
            if not os.path.exists(ofx_file):
                print(f"❌ Arquivo não encontrado: {os.path.basename(ofx_file)}")
                continue
                
            print(f"\n🔍 Analisando {descricao}...")
            
            # Detectar tipo automaticamente
            ofx_info = comprehensive_ofx_analysis(ofx_file)
            
            print(f"   📄 Arquivo: {ofx_info['filename']}")
            print(f"   🏦 Tipo: {ofx_info['detected_type']}")
            print(f"   📋 Descrição: {ofx_info['description']}")
            print(f"   🆔 ID Omie: {ofx_info['omie_account_id']}")
            print(f"   ✅ Validação: {ofx_info['validation']}")
            
            # Para conta corrente, usar o ID conhecido que funciona na conciliação
            if ofx_info['detected_type'] == 'checking':
                conta_id = "2103553430"  # ID que sabemos que funciona
                print(f"   🔧 Usando ID conhecido para conta corrente: {conta_id}")
            else:
                conta_id = str(ofx_info['omie_account_id'])
            
            configs_finais.append({
                "ofx_file": ofx_file,
                "conta_id": conta_id,
                "descricao": descricao
            })
        
        if not configs_finais:
            print("❌ Nenhum arquivo válido encontrado")
            return
        
        # Resetar dados existentes (opcional - perguntamos ao usuário via código)
        print(f"\n🗑️ Vamos adicionar aos dados existentes (não resetar)")
        print(f"   O modelo atual tem dados de treino que queremos manter")
        
        # Processar arquivos
        print(f"\n📋 Processando {len(configs_finais)} arquivo(s) específicos:")
        for config in configs_finais:
            print(f"   ✅ {config['descricao']} -> Conta ID: {config['conta_id']}")
        
        # Processar cada arquivo individualmente para melhor controle
        total_learned = 0
        total_matches = 0
        
        for config in configs_finais:
            print(f"\n{'='*70}")
            print(f"📄 PROCESSANDO: {config['descricao']}")
            print(f"{'='*70}")
            
            result = learning_system.process_historical_ofx(config['ofx_file'], config['conta_id'])
            
            if result['status'] == 'success':
                matches = result.get('matches_found', 0)
                learned = result.get('learned_transactions', 0)
                learning_rate = result.get('learning_rate', 0)
                
                print(f"✅ SUCESSO!")
                print(f"   📊 Matches encontrados: {matches}")
                print(f"   📚 Transações aprendidas: {learned}")
                print(f"   📈 Taxa de aprendizado: {learning_rate:.1f}%")
                
                total_matches += matches
                total_learned += learned
            else:
                print(f"❌ ERRO: {result['message']}")
        
        # Resumo final
        print(f"\n{'='*70}")
        print(f"🎉 PROCESSAMENTO CONCLUÍDO!")
        print(f"{'='*70}")
        print(f"📊 Total de matches: {total_matches}")
        print(f"📚 Total de dados aprendidos: {total_learned}")
        
        if total_matches > 0:
            taxa_geral = (total_learned / total_matches) * 100
            print(f"📈 Taxa de aprendizado geral: {taxa_geral:.1f}%")
        
        # Estatísticas finais do ML
        ml_stats = learning_system.ml_categorizer.get_learning_stats()
        print(f"\n🧠 ESTATÍSTICAS FINAIS DO MODELO ML:")
        print(f"   📚 Total de exemplos na base: {ml_stats['total_transactions']}")
        print(f"   🏷️ Com categoria: {ml_stats['categorized']}")
        print(f"   👥 Com cliente/fornecedor: {ml_stats['with_client_supplier']}")
        print(f"   🤖 Modelo treinado: {'Sim' if ml_stats['model_trained'] else 'Não'}")
        
        print(f"\n💡 O sistema agora tem dados de ambas as contas:")
        print(f"   🏦 Conta corrente Nubank PJ (transações bancárias)")
        print(f"   💳 Cartão Mastercard Nubank (despesas)")
        print(f"   🚀 Precisão das sugestões será ainda maior!")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()