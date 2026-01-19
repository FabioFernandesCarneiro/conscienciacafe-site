#!/usr/bin/env python3
"""
Sistema Inteligente de Conciliação Bancária - VERSÃO PRINCIPAL OTIMIZADA
Consciência Café - Integração com Omie ERP

Nova lógica baseada no aprendizado:
1) Ler arquivo OFX e verificar range de datas  
2) Listar lançamentos do Omie no período e carregar em cache
3) Buscar por número do documento (ID OFX truncado)
4) Se não encontrar, buscar por data e valor com confirmação
5) Se não for o mesmo, criar novo com IA para categoria/cliente
6) Marcar como conciliado e próximo registro
"""

import os
from dotenv import load_dotenv
from src.omie_client import OmieClient
from src.ml_categorizer import MLCategorizer
from src.smart_reconciliation import SmartReconciliationEngine
from src.ofx_detector import comprehensive_ofx_analysis

def main():
    """Função principal do sistema inteligente"""
    load_dotenv()
    
    print("🚀 SISTEMA INTELIGENTE DE CONCILIAÇÃO BANCÁRIA")
    print("💼 Consciência Café - Integração Omie ERP")
    print("=" * 70)
    
    try:
        # Inicializar componentes
        print("\\n🔧 INICIALIZANDO SISTEMA...")
        
        omie_client = OmieClient(
            app_key=os.getenv('OMIE_APP_KEY'),
            app_secret=os.getenv('OMIE_APP_SECRET')
        )
        
        ml_categorizer = MLCategorizer()
        
        # Carregar dados de aprendizado existentes
        print("📚 Carregando base de conhecimento...")
        learning_stats = ml_categorizer.get_learning_stats()
        print(f"   📊 {learning_stats['total_transactions']} transações na base")
        print(f"   🏷️ {learning_stats['categorized']} categorizadas")
        print(f"   🤖 Modelo treinado: {'Sim' if learning_stats['model_trained'] else 'Não'}")
        
        smart_engine = SmartReconciliationEngine(omie_client, ml_categorizer)
        
        print("✅ Sistema inicializado com sucesso!")
        
        # Solicitar arquivo OFX
        print("\\n📄 SELEÇÃO DE ARQUIVO OFX")
        print("-" * 70)
        
        # Opção de usar arquivo padrão para teste ou solicitar caminho
        test_files = [
            "NU_826344542_12JUL2025_13JUL2025.ofx",
            "NU_826344542_01JUL2025_02JUL2025.ofx", 
            "NU_826344542_01MAI2025_14AGO2025.ofx",
            "Nubank_2025-03-22 (1).ofx"
        ]
        
        print("Arquivos OFX disponíveis:")
        for i, filename in enumerate(test_files, 1):
            file_path = f"/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/{filename}"
            exists = "✅" if os.path.exists(file_path) else "❌"
            print(f"   {i}. {exists} {filename}")
        
        print(f"   0. Digitar caminho customizado")
        
        try:
            choice = input("\\nEscolha o arquivo (0-4): ").strip()
            
            if choice == '0':
                ofx_file = input("Caminho do arquivo OFX: ").strip()
            else:
                try:
                    file_idx = int(choice) - 1
                    if 0 <= file_idx < len(test_files):
                        ofx_file = f"/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/{test_files[file_idx]}"
                    else:
                        print("❌ Opção inválida!")
                        return
                except ValueError:
                    print("❌ Digite apenas números!")
                    return
            
        except KeyboardInterrupt:
            print("\\n⚠️ Operação cancelada pelo usuário")
            return
        
        if not os.path.exists(ofx_file):
            print(f"❌ Arquivo OFX não encontrado: {ofx_file}")
            return
        
        # 🔍 DETECTAR TIPO DE CONTA AUTOMATICAMENTE
        print(f"\\n🔍 ANALISANDO ARQUIVO OFX...")
        ofx_info = comprehensive_ofx_analysis(ofx_file)
        
        print(f"📄 Arquivo: {ofx_info['filename']}")
        print(f"🏦 Tipo detectado: {ofx_info['detected_type']}")
        print(f"📋 Descrição: {ofx_info['description']}")
        print(f"🆔 ID Omie: {ofx_info['omie_account_id']}")
        print(f"🔗 ID da conta: {ofx_info['account_id']}")
        print(f"✅ Validação: {ofx_info['validation']}")
        print(f"🎯 Confiança: {ofx_info['confidence']}")
        
        # Verificar inconsistências
        if ofx_info['validation'] == 'inconsistent':
            print(f"\\n⚠️ INCONSISTÊNCIA DETECTADA!")
            print(f"   Cabeçalho indica: {ofx_info['detected_type']}")
            print(f"   Nome do arquivo indica: {ofx_info['filename_pattern']}")
            
            choice = input("\\nContinuar mesmo assim? (s/N): ").lower()
            if choice != 's':
                print("Operação cancelada.")
                return
        
        # Configurar cliente Omie com a conta correta
        print(f"\\n🔧 CONFIGURANDO CONTA: ID {ofx_info['omie_account_id']}")
        omie_client.set_account_id(ofx_info['omie_account_id'])
        
        # Confirmar configuração
        print(f"✅ Conta configurada:")
        print(f"   🏦 Tipo: {ofx_info['description']}")
        print(f"   🔢 ID Omie: {omie_client.get_current_account_id()}")
        
        # Confirmar processamento
        print(f"\\n🚀 INICIAR PROCESSAMENTO INTELIGENTE?")
        print(f"   📄 Arquivo: {os.path.basename(ofx_file)}")
        print(f"   🏦 Conta: {ofx_info['description']}")
        print(f"\\n   O sistema irá:")
        print(f"   1️⃣ Extrair transações do OFX e determinar período")
        print(f"   2️⃣ Carregar lançamentos do Omie em cache otimizado")  
        print(f"   3️⃣ Processar cada transação com busca inteligente")
        print(f"   4️⃣ Usar IA para categorização automática")
        print(f"   5️⃣ Solicitar confirmação quando necessário")
        
        confirm = input("\\nContinuar? (S/n): ").lower()
        if confirm == 'n':
            print("Operação cancelada.")
            return
        
        # 🚀 EXECUTAR PROCESSAMENTO INTELIGENTE
        print(f"\\n" + "=" * 70)
        print("🚀 INICIANDO PROCESSAMENTO INTELIGENTE")
        print("=" * 70)
        
        result = smart_engine.process_ofx_file(ofx_file)
        
        # Mostrar resultado final
        if result.get('status') == 'success':
            print(f"\\n🎉 PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
            print(f"\\n📊 ESTATÍSTICAS FINAIS:")
            print(f"   📋 Total de transações: {result['total_transacoes']}")
            print(f"   ✅ Já conciliadas: {result['ja_conciliadas']}")
            print(f"   🤖 Criadas automaticamente: {result['criadas_automaticamente']}")
            print(f"   👤 Criadas manualmente: {result['criadas_manualmente']}")
            print(f"   🤝 Confirmadas pelo usuário: {result['confirmadas_usuario']}")
            print(f"   ⏭️ Puladas: {result['puladas']}")
            print(f"   ❌ Erros: {result['erros']}")
            
            # Calcular eficiência
            total_processadas = (result['ja_conciliadas'] + result['criadas_automaticamente'] + 
                               result['criadas_manualmente'] + result['confirmadas_usuario'])
            
            if result['total_transacoes'] > 0:
                eficiencia = (total_processadas / result['total_transacoes']) * 100
                print(f"\\n📈 EFICIÊNCIA GERAL: {eficiencia:.1f}%")
                
                # Nível de automação
                automaticas = result['ja_conciliadas'] + result['criadas_automaticamente']
                if total_processadas > 0:
                    automacao = (automaticas / total_processadas) * 100
                    print(f"🤖 NÍVEL DE AUTOMAÇÃO: {automacao:.1f}%")
            
            # Verificar se o modelo ML melhorou
            new_stats = ml_categorizer.get_learning_stats()
            if new_stats['total_transactions'] > learning_stats['total_transactions']:
                novos_aprendizados = new_stats['total_transactions'] - learning_stats['total_transactions']
                print(f"\\n🧠 APRENDIZADO EXPANDIDO:")
                print(f"   📚 +{novos_aprendizados} novas transações aprendidas")
                print(f"   🎯 Total na base: {new_stats['total_transactions']}")
                print(f"   🚀 O sistema ficou mais inteligente!")
            
        else:
            print(f"\\n❌ ERRO NO PROCESSAMENTO:")
            print(f"   {result.get('message', 'Erro desconhecido')}")
        
        print(f"\\n" + "=" * 70)
        print("🏁 SISTEMA FINALIZADO")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print(f"\\n\\n⚠️ OPERAÇÃO INTERROMPIDA PELO USUÁRIO")
        print("   O processamento foi cancelado.")
        
    except Exception as e:
        print(f"\\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()