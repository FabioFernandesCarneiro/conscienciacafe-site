#!/usr/bin/env python3
"""
Sistema de aprendizado histórico para categorização automática
Processa OFX históricos e extrai dados do Omie para treinar o ML
"""

import os
import ofxparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from src.omie_client import OmieClient
from src.ml_categorizer import MLCategorizer

class HistoricalLearningSystem:
    def __init__(self, omie_client: OmieClient, ml_categorizer: MLCategorizer):
        self.omie_client = omie_client
        self.ml_categorizer = ml_categorizer
        self.processed_transactions = 0
        self.learned_transactions = 0
        self.errors = []
        
    def process_historical_ofx(self, ofx_path: str) -> Dict[str, Any]:
        """
        Processa um arquivo OFX histórico e extrai dados de aprendizado
        """
        print(f"📚 Processando arquivo histórico: {os.path.basename(ofx_path)}")
        
        if not os.path.exists(ofx_path):
            error = f"Arquivo não encontrado: {ofx_path}"
            self.errors.append(error)
            return {"status": "error", "message": error}
        
        try:
            # Parse do arquivo OFX
            transactions = self._parse_ofx_file(ofx_path)
            
            if not transactions:
                return {"status": "error", "message": "Nenhuma transação encontrada no arquivo"}
            
            print(f"📊 {len(transactions)} transações encontradas no arquivo")
            
            # Processar cada transação
            learned_count = 0
            for i, transaction in enumerate(transactions):
                try:
                    print(f"🔍 Processando transação {i+1}/{len(transactions)}: {transaction['description'][:50]}...")
                    
                    # Buscar transação no Omie pelo ID
                    omie_data = self._find_omie_transaction(transaction)
                    
                    if omie_data:
                        # Extrair dados de aprendizado
                        learning_data = self._extract_learning_data(transaction, omie_data)
                        
                        if learning_data:
                            # Salvar no sistema de ML
                            self._save_learning_data(learning_data)
                            learned_count += 1
                            print(f"  ✅ Dados extraídos: {learning_data['category'] or learning_data['client_supplier']}")
                        else:
                            print(f"  ⚠️ Dados insuficientes para aprendizado")
                    else:
                        print(f"  ℹ️ Transação não encontrada no Omie (ainda não foi importada)")
                    
                    self.processed_transactions += 1
                    
                except Exception as e:
                    error_msg = f"Erro na transação {transaction.get('id', 'N/A')}: {str(e)}"
                    self.errors.append(error_msg)
                    print(f"  ❌ {error_msg}")
            
            self.learned_transactions += learned_count
            
            return {
                "status": "success",
                "total_transactions": len(transactions),
                "learned_transactions": learned_count,
                "not_found": len(transactions) - learned_count
            }
            
        except Exception as e:
            error = f"Erro ao processar arquivo {ofx_path}: {str(e)}"
            self.errors.append(error)
            return {"status": "error", "message": error}
    
    def process_multiple_ofx_files(self, ofx_directory: str) -> Dict[str, Any]:
        """
        Processa múltiplos arquivos OFX em um diretório
        """
        print(f"🎯 SISTEMA DE APRENDIZADO HISTÓRICO")
        print(f"=" * 60)
        print(f"📂 Processando arquivos em: {ofx_directory}")
        
        if not os.path.exists(ofx_directory):
            return {"status": "error", "message": f"Diretório não encontrado: {ofx_directory}"}
        
        # Encontrar arquivos OFX
        ofx_files = []
        for file_name in os.listdir(ofx_directory):
            if file_name.lower().endswith('.ofx'):
                ofx_files.append(os.path.join(ofx_directory, file_name))
        
        if not ofx_files:
            return {"status": "error", "message": "Nenhum arquivo OFX encontrado no diretório"}
        
        print(f"📄 {len(ofx_files)} arquivo(s) OFX encontrado(s)")
        
        # Processar cada arquivo
        results = []
        for ofx_path in ofx_files:
            result = self.process_historical_ofx(ofx_path)
            results.append({
                "file": os.path.basename(ofx_path),
                "result": result
            })
        
        # Resumo final
        self._print_final_summary(results)
        
        return {
            "status": "success",
            "files_processed": len(ofx_files),
            "total_transactions": self.processed_transactions,
            "learned_transactions": self.learned_transactions,
            "errors": len(self.errors),
            "results": results
        }
    
    def _parse_ofx_file(self, ofx_path: str) -> List[Dict[str, Any]]:
        """
        Parse de arquivo OFX extraindo transações
        """
        transactions = []
        
        try:
            with open(ofx_path, 'r', encoding='latin-1') as file:
                ofx_data = ofxparse.OfxParser.parse(file)
                
                if hasattr(ofx_data, 'account'):
                    account = ofx_data.account
                    
                    for transaction in account.statement.transactions:
                        trans_data = {
                            'id': transaction.id,
                            'date': transaction.date,
                            'amount': float(transaction.amount),
                            'description': transaction.memo or transaction.payee or '',
                            'type': transaction.type,
                            'account_id': account.account_id,
                            'bank_id': account.routing_number,
                            'original_description': transaction.memo or transaction.payee or ''
                        }
                        
                        # Limpeza da descrição para ML
                        clean = trans_data['description'].strip().lower()
                        for char in ['*', '#', '/', '\\', '-', '_', '.', ',']:
                            clean = clean.replace(char, ' ')
                        while '  ' in clean:
                            clean = clean.replace('  ', ' ')
                        trans_data['clean_description'] = clean.strip()
                        
                        transactions.append(trans_data)
        
        except Exception as e:
            print(f"❌ Erro ao fazer parse do OFX: {e}")
            
        return transactions
    
    def _find_omie_transaction(self, transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Busca transação no Omie - primeiro por ID, depois por valor/descrição
        """
        try:
            ofx_id = transaction.get('id')
            
            # 1. Tentar busca por ID primeiro
            if ofx_id:
                existing = self.omie_client.search_lancamento_by_ofx_id(ofx_id)
                if existing:
                    print(f"  ✅ Encontrada por ID OFX!")
                    return existing
            
            # 2. Se não encontrou por ID, tentar busca melhorada por valor/descrição
            print(f"  🔍 Buscando por valor/descrição...")
            date_str = transaction['date'].strftime('%d/%m/%Y') if hasattr(transaction['date'], 'strftime') else str(transaction['date'])
            
            existing = self.omie_client.search_lancamento_by_description(
                transaction['clean_description'],
                transaction['amount'],
                date_str
            )
            
            if existing:
                print(f"  ✅ Encontrada por valor/descrição!")
                return existing
            else:
                print(f"  ℹ️ Transação não encontrada no Omie")
                return None
            
        except Exception as e:
            print(f"  ❌ Erro ao buscar no Omie: {e}")
            return None
    
    def _extract_learning_data(self, transaction: Dict[str, Any], omie_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extrai dados de aprendizado da transação e dados do Omie
        """
        try:
            # Usar novo método para obter dados detalhados
            enhanced_data = self._get_enhanced_omie_data(omie_data)
            
            if not enhanced_data:
                return None
            
            # Preparar dados para o ML
            learning_data = {
                'description': transaction['description'],
                'clean_description': transaction['clean_description'],
                'amount': transaction['amount'],
                'category': enhanced_data.get('categoria_nome'),
                'client_supplier': enhanced_data.get('cliente_fornecedor_nome'),
                'omie_type': omie_data['tipo'],
                'confidence': 1.0  # Máxima confiança para dados históricos reais
            }
            
            # Validar se temos informação útil
            if learning_data['category'] or learning_data['client_supplier']:
                return learning_data
            
            return None
            
        except Exception as e:
            print(f"  ❌ Erro ao extrair dados: {e}")
            return None
    
    def _get_enhanced_omie_data(self, omie_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Obtém dados completos do lançamento no Omie - método direto
        """
        try:
            # Usar dados do lançamento diretamente (já temos tudo que precisamos)
            lancamento_completo = omie_data.get('lancamento', {})
            
            enhanced = {
                'categoria_nome': None,
                'cliente_fornecedor_nome': None
            }
            
            # Extrair nome da categoria
            codigo_categoria = lancamento_completo.get('codigo_categoria')
            if codigo_categoria:
                categoria = self.omie_client.get_categoria_by_codigo(codigo_categoria)
                if categoria:
                    enhanced['categoria_nome'] = categoria.get('descricao')
                    print(f"  📚 Categoria: {enhanced['categoria_nome']}")
                else:
                    print(f"  ⚠️ Categoria {codigo_categoria} não encontrada")
            
            # Extrair nome do cliente/fornecedor
            codigo_cliente = lancamento_completo.get('codigo_cliente_fornecedor')
            if codigo_cliente:
                clientes = self.omie_client.get_clientes_fornecedores()
                for cliente in clientes:
                    if cliente.get('id') == codigo_cliente:
                        enhanced['cliente_fornecedor_nome'] = cliente.get('nome')
                        print(f"  👤 Cliente/Fornecedor: {enhanced['cliente_fornecedor_nome']}")
                        break
                else:
                    print(f"  ⚠️ Cliente {codigo_cliente} não encontrado")
            
            return enhanced
            
        except Exception as e:
            print(f"  ❌ Erro ao extrair dados: {e}")
            return None
    
    def _get_enhanced_omie_data_fallback(self, omie_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Método fallback para extrair dados do lançamento
        """
        try:
            lancamento_completo = omie_data.get('lancamento', {})
            
            enhanced = {
                'categoria_nome': None,
                'cliente_fornecedor_nome': None
            }
            
            # Extrair nome da categoria
            categoria_codigo = lancamento_completo.get('codigo_categoria')
            if categoria_codigo:
                # Buscar nome da categoria
                categorias = self.omie_client.get_categorias()
                for cat in categorias:
                    if str(cat.get('codigo')) == str(categoria_codigo):
                        enhanced['categoria_nome'] = cat.get('descricao', cat.get('nome'))
                        break
            
            # Extrair nome do cliente/fornecedor
            cliente_codigo = lancamento_completo.get('codigo_cliente_fornecedor')
            if cliente_codigo:
                # Buscar nome do cliente/fornecedor
                clientes = self.omie_client.get_clientes_fornecedores()
                for cliente in clientes:
                    if cliente.get('id') == cliente_codigo:
                        enhanced['cliente_fornecedor_nome'] = cliente.get('nome')
                        break
            
            return enhanced
            
        except Exception as e:
            print(f"  ❌ Erro no método fallback: {e}")
            return None
    
    def _save_learning_data(self, learning_data: Dict[str, Any]):
        """
        Salva dados no sistema de ML
        """
        try:
            self.ml_categorizer.add_learning_data(
                description=learning_data['description'],
                clean_description=learning_data['clean_description'],
                amount=learning_data['amount'],
                category_name=learning_data['category'],
                client_supplier_name=learning_data['client_supplier']
            )
        except Exception as e:
            print(f"  ❌ Erro ao salvar dados de aprendizado: {e}")
    
    def _print_final_summary(self, results: List[Dict]):
        """
        Imprime resumo final do processamento
        """
        print(f"\n{'='*60}")
        print(f"RESUMO DO APRENDIZADO HISTÓRICO")
        print(f"{'='*60}")
        
        for result in results:
            file_name = result['file']
            file_result = result['result']
            
            print(f"\n📄 {file_name}:")
            if file_result['status'] == 'success':
                print(f"   ✅ Total: {file_result['total_transactions']} transações")
                print(f"   📚 Aprendidas: {file_result['learned_transactions']}")
                print(f"   ⚠️ Não encontradas: {file_result['not_found']}")
            else:
                print(f"   ❌ Erro: {file_result['message']}")
        
        print(f"\n🎯 TOTAIS GERAIS:")
        print(f"   📊 Transações processadas: {self.processed_transactions}")
        print(f"   📚 Dados aprendidos: {self.learned_transactions}")
        print(f"   ❌ Erros: {len(self.errors)}")
        
        if self.learned_transactions > 0:
            learning_rate = (self.learned_transactions / self.processed_transactions) * 100
            print(f"   📈 Taxa de aprendizado: {learning_rate:.1f}%")
        
        # Estatísticas do ML após aprendizado
        ml_stats = self.ml_categorizer.get_learning_stats()
        print(f"\n🧠 ESTATÍSTICAS DO MODELO ML:")
        print(f"   📚 Total de exemplos: {ml_stats['total_transactions']}")
        print(f"   🏷️ Com categoria: {ml_stats['categorized']}")
        print(f"   👥 Com cliente/fornecedor: {ml_stats['with_client_supplier']}")
        print(f"   🤖 Modelo treinado: {'Sim' if ml_stats['model_trained'] else 'Não'}")
        
        if self.errors:
            print(f"\n❌ ERROS ({len(self.errors)}):")
            for error in self.errors[:5]:  # Mostrar até 5 erros
                print(f"   - {error}")
            if len(self.errors) > 5:
                print(f"   ... e mais {len(self.errors) - 5} erros")
        
        print(f"\n{'='*60}")
        print(f"💡 PRÓXIMOS PASSOS:")
        print(f"   1. O sistema agora tem mais dados históricos")
        print(f"   2. A categorização automática será mais precisa")
        print(f"   3. Execute o reconciliador com novos OFX para testar")
        print(f"{'='*60}")

def main():
    """
    Função principal para execução standalone
    """
    load_dotenv()
    
    print("🎯 SISTEMA DE APRENDIZADO HISTÓRICO")
    print("=" * 60)
    
    try:
        # Inicializar componentes
        omie_client = OmieClient(
            app_key=os.getenv('OMIE_APP_KEY'),
            app_secret=os.getenv('OMIE_APP_SECRET')
        )
        
        ml_categorizer = MLCategorizer()
        learning_system = HistoricalLearningSystem(omie_client, ml_categorizer)
        
        print("✅ Sistema inicializado")
        
        # Perguntar pelo diretório ou arquivo específico
        print("\nOpções:")
        print("1. Processar um arquivo OFX específico")
        print("2. Processar todos os OFX de um diretório")
        
        choice = input("Escolha (1-2): ").strip()
        
        if choice == "1":
            # Arquivo específico
            ofx_path = input("Caminho do arquivo OFX: ").strip()
            result = learning_system.process_historical_ofx(ofx_path)
            
            if result['status'] == 'success':
                print(f"✅ Processamento concluído!")
                print(f"   📚 {result['learned_transactions']}/{result['total_transactions']} transações aprendidas")
            else:
                print(f"❌ Erro: {result['message']}")
                
        elif choice == "2":
            # Diretório
            directory = input("Diretório com arquivos OFX: ").strip()
            if not directory:
                directory = "."  # Diretório atual
            
            result = learning_system.process_multiple_ofx_files(directory)
            
            if result['status'] == 'success':
                print(f"✅ Processamento de {result['files_processed']} arquivo(s) concluído!")
            else:
                print(f"❌ Erro: {result['message']}")
        else:
            print("❌ Opção inválida")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()