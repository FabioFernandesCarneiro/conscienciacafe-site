#!/usr/bin/env python3
"""
Sistema de Aprendizado Histórico OTIMIZADO v2.0
Usa a mesma lógica melhorada do smart_reconciliation.py:
- Busca por período de datas no OFX
- Cache otimizado com busca por número do documento 
- Extrai categorias REAIS dos lançamentos do Omie
"""

import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import ofxparse
from src.omie_client import OmieClient
from src.ml_categorizer import MLCategorizer

class OptimizedHistoricalLearning:
    def __init__(self, omie_client: OmieClient, ml_categorizer: MLCategorizer):
        self.omie_client = omie_client
        self.ml_categorizer = ml_categorizer
        self.processed_transactions = 0
        self.learned_transactions = 0
        self.errors = []
        
        # Cache otimizado usando a mesma estrutura do smart_reconciliation
        self.cache = {
            'periodo': None,
            'por_numero_documento': {}, # {numero_documento_truncado: dados} - MÉTODO PRINCIPAL
            'por_valor_data': {},       # {f"{valor}_{data}": [lista_dados]} - MÉTODO FALLBACK
            'estatisticas': {
                'total_carregados': 0,
                'conta_corrente': 0,
                'contas_pagar': 0,
                'contas_receber': 0
            }
        }
    
    def process_historical_ofx_optimized(self, ofx_file_path: str) -> Dict[str, Any]:
        """
        Processamento otimizado v2.0 usando lógica do smart_reconciliation
        """
        try:
            print("🧠 APRENDIZADO HISTÓRICO OTIMIZADO v2.0")
            print("=" * 60)
            
            # ETAPA 1: Ler arquivo OFX e extrair range de datas
            print("\n📄 ETAPA 1: Analisando arquivo OFX...")
            ofx_transactions = self._parse_ofx_file(ofx_file_path)
            
            if not ofx_transactions:
                return {"status": "error", "message": "Nenhuma transação encontrada no OFX"}
            
            period_start, period_end = self._get_period_from_transactions(ofx_transactions)
            
            self.processed_transactions = len(ofx_transactions)
            print(f"✅ {self.processed_transactions} transações encontradas")
            print(f"📅 Período: {period_start} a {period_end}")
            
            # ETAPA 2: Carregar lançamentos do Omie em cache
            print(f"\n🗃️ ETAPA 2: Carregando lançamentos do Omie em cache...")
            cache_success = self._load_period_cache(period_start, period_end)
            
            if not cache_success:
                return {"status": "error", "message": "Erro ao carregar cache do período"}
            
            print(f"✅ Cache carregado:")
            print(f"   📊 Total: {self.cache['estatisticas']['total_carregados']} lançamentos")
            print(f"   🏦 Conta Corrente: {self.cache['estatisticas']['conta_corrente']}")
            print(f"   💸 Contas a Pagar: {self.cache['estatisticas']['contas_pagar']}")
            print(f"   💰 Contas a Receber: {self.cache['estatisticas']['contas_receber']}")
            print(f"   📄 Por número documento: {len(self.cache['por_numero_documento'])}")
            print(f"   💰 Por valor+data: {len(self.cache['por_valor_data'])}")
            
            # ETAPA 3: Processar transações para aprendizado
            print(f"\n🧠 ETAPA 3: Processando transações para aprendizado...")
            print("-" * 60)
            
            categories_learned = {}
            clients_learned = {}
            found_matches = 0
            
            for i, transaction in enumerate(ofx_transactions):
                if (i + 1) % 100 == 0:  # Progresso a cada 100
                    print(f"📊 Progresso: {i+1}/{self.processed_transactions} ({found_matches} matches)")
                
                # Buscar transação usando método otimizado
                cached_item = self._find_transaction_in_cache(transaction)
                
                if cached_item:
                    found_matches += 1
                    
                    # Extrair dados para aprendizado
                    learning_data = self._extract_learning_data(transaction, cached_item)
                    if learning_data:
                        self._add_to_learning(learning_data, categories_learned, clients_learned)
                        self.learned_transactions += 1
            
            # ETAPA 4: Salvar aprendizado no modelo ML
            print(f"\n💾 ETAPA 4: Salvando aprendizado no modelo ML...")
            learning_saved = self._save_learning_data(categories_learned, clients_learned)
            
            # ETAPA 5: Mostrar resumo final
            print(f"\n🏁 APRENDIZADO CONCLUÍDO!")
            print("=" * 60)
            print(f"📊 Total de transações OFX: {self.processed_transactions}")
            print(f"✅ Correspondências encontradas: {found_matches} ({(found_matches/self.processed_transactions)*100:.1f}%)")
            print(f"🧠 Transações aprendidas: {self.learned_transactions}")
            print(f"🏷️ Categorias distintas: {len(categories_learned)}")
            print(f"👥 Clientes distintos: {len(clients_learned)}")
            print(f"💾 Dados salvos no ML: {'✅' if learning_saved else '❌'}")
            
            return {
                "status": "success",
                "processed": self.processed_transactions,
                "found_matches": found_matches,
                "learned": self.learned_transactions,
                "categories_count": len(categories_learned),
                "clients_count": len(clients_learned),
                "learning_saved": learning_saved,
                "details": {
                    "categories_learned": categories_learned,
                    "clients_learned": clients_learned
                }
            }
            
        except Exception as e:
            error_msg = f"Erro no processamento otimizado: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.errors.append(error_msg)
            return {"status": "error", "message": error_msg}
    
    def _parse_ofx_file(self, ofx_file_path: str) -> List[Dict[str, Any]]:
        """Extrai transações do arquivo OFX"""
        transactions = []
        
        with open(ofx_file_path, 'r', encoding='latin-1') as file:
            ofx_data = ofxparse.OfxParser.parse(file)
            
            if hasattr(ofx_data, 'account') and hasattr(ofx_data.account, 'statement'):
                for transaction in ofx_data.account.statement.transactions:
                    transactions.append({
                        'id': transaction.id,
                        'date': transaction.date.date() if hasattr(transaction.date, 'date') else transaction.date,
                        'amount': float(transaction.amount),
                        'description': transaction.memo,
                        'clean_description': self._clean_description(transaction.memo),
                        'type': transaction.type
                    })
        
        return transactions
    
    def _get_period_from_transactions(self, transactions: List[Dict[str, Any]]) -> Tuple[date, date]:
        """Determina período das transações com margem"""
        dates = [t['date'] for t in transactions if t['date']]
        
        if not dates:
            today = datetime.now().date()
            return today - timedelta(days=30), today
        
        start_date = min(dates)
        end_date = max(dates)
        
        # Adicionar margem de 7 dias para cada lado
        start_date = start_date - timedelta(days=7)
        end_date = end_date + timedelta(days=7)
        
        return start_date, end_date
    
    def _load_period_cache(self, start_date: date, end_date: date) -> bool:
        """Carrega todos os lançamentos do período em cache otimizado"""
        try:
            self.cache['periodo'] = (start_date, end_date)
            
            # Formatar datas para API
            start_str = start_date.strftime("%d/%m/%Y")
            end_str = end_date.strftime("%d/%m/%Y")
            
            # Carregar lançamentos de conta corrente
            cc_count = self._load_conta_corrente_cache(start_str, end_str)
            self.cache['estatisticas']['conta_corrente'] = cc_count
            
            # Carregar contas a pagar
            cp_count = self._load_contas_pagar_cache(start_str, end_str)
            self.cache['estatisticas']['contas_pagar'] = cp_count
            
            # Carregar contas a receber
            cr_count = self._load_contas_receber_cache(start_str, end_str)
            self.cache['estatisticas']['contas_receber'] = cr_count
            
            self.cache['estatisticas']['total_carregados'] = cc_count + cp_count + cr_count
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar cache: {e}")
            return False
            transactions = []
            
            with open(ofx_file_path, 'r', encoding='latin-1') as file:
                ofx_data = ofxparse.OfxParser.parse(file)
                
                if hasattr(ofx_data, 'account') and hasattr(ofx_data.account, 'statement'):
                    for transaction in ofx_data.account.statement.transactions:
                        transactions.append({
                            'id': transaction.id,
                            'date': transaction.date,
                            'amount': float(transaction.amount),
                            'description': transaction.memo,
                            'clean_description': self._clean_description(transaction.memo),
                            'type': transaction.type
                        })
            
            return transactions
            
        except Exception as e:
            self.errors.append(f"Erro ao parsear OFX: {e}")
            return []
    
    def _get_period_from_transactions(self, transactions: List[Dict[str, Any]]) -> tuple:
        """Determina período inicial e final das transações"""
        dates = [t['date'] for t in transactions if t['date']]
        
        if not dates:
            # Fallback para um período amplo
            today = datetime.now().date()
            return today - timedelta(days=365), today
        
        start_date = min(dates)
        end_date = max(dates)
        
        # Converter para date se necessário
        if hasattr(start_date, 'date'):
            start_date = start_date.date()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()
        
        # Adicionar margem de alguns dias
        start_date = start_date - timedelta(days=7)
        end_date = end_date + timedelta(days=7)
        
        return start_date, end_date
    
    def _load_period_cache(self, start_date, end_date) -> bool:
        """
        OTIMIZAÇÃO PRINCIPAL: Carrega TODOS os lançamentos do período em cache
        """
        try:
            print(f"📥 Carregando lançamentos em cache ({start_date} a {end_date})...")
            
            # Formatar datas para API Omie
            start_str = start_date.strftime("%d/%m/%Y")
            end_str = end_date.strftime("%d/%m/%Y")
            
            total_loaded = 0
            
            # Carregar lançamentos de conta corrente (método principal)
            print(f"   🏦 Carregando lançamentos de conta corrente...")
            cc_count = self._load_conta_corrente_cache(start_str, end_str)
            total_loaded += cc_count
            
            # Carregar contas a pagar (backup)
            print(f"   💸 Carregando contas a pagar...")
            cp_count = self._load_contas_pagar_cache(start_str, end_str)
            total_loaded += cp_count
            
            # Carregar contas a receber (backup)
            print(f"   💰 Carregando contas a receber...")
            cr_count = self._load_contas_receber_cache(start_str, end_str)
            total_loaded += cr_count
            
            print(f"✅ Cache carregado: {total_loaded} lançamentos")
            print(f"   📋 {len(self.lancamentos_cache['conta_corrente'])} por ID OFX")
            print(f"   💰 {len(self.lancamentos_cache['valor_index'])} valores únicos")
            
            self.lancamentos_cache['periodo'] = (start_date, end_date)
            return True
            
        except Exception as e:
            self.errors.append(f"Erro ao carregar cache: {e}")
            return False
    
    def _load_conta_corrente_cache(self, start_str: str, end_str: str) -> int:
        """Carrega lançamentos de conta corrente"""
        count = 0
        current_account_str = str(self.omie_client.current_account_id)
        
        try:
            # Buscar com filtro de data
            for pagina in range(1, 20):  # Máximo 20 páginas
                try:
                    result = self.omie_client.omie.listar_lanc_c_c(
                        nPagina=pagina,
                        nRegPorPagina=100,
                        dtPagInicial=start_str,
                        dtPagFinal=end_str
                    )
                    
                    if not (isinstance(result, dict) and 'listaLancamentos' in result):
                        break
                        
                    lancamentos = result['listaLancamentos']
                    if not lancamentos:
                        break  # Sem mais dados
                    
                    for lanc in lancamentos:
                        # Verificar se é da conta configurada
                        if self.omie_client._is_current_account_lancamento(lanc, current_account_str):
                            self._add_to_cache(lanc, 'conta_corrente')
                            count += 1
                    
                    if len(lancamentos) < 100:  # Última página
                        break
                        
                except Exception as e:
                    print(f"     ⚠️ Erro na página {pagina}: {e}")
                    break
            
        except Exception as e:
            print(f"     ❌ Erro geral conta corrente: {e}")
        
        return count
    
    def _load_contas_pagar_cache(self, start_str: str, end_str: str) -> int:
        """Carrega contas a pagar"""
        count = 0
        
        try:
            for pagina in range(1, 10):  # Máximo 10 páginas
                try:
                    result = self.omie_client.omie.listar_contas_pagar(
                        pagina=pagina,
                        registros_por_pagina=100
                    )
                    
                    if not (isinstance(result, dict) and 'conta_pagar_cadastro' in result):
                        break
                        
                    contas = result['conta_pagar_cadastro']
                    if not contas:
                        break
                    
                    for conta in contas:
                        self._add_to_cache(conta, 'conta_pagar')
                        count += 1
                    
                    if len(contas) < 100:
                        break
                        
                except Exception as e:
                    print(f"     ⚠️ Erro contas pagar página {pagina}: {e}")
                    break
            
        except Exception as e:
            print(f"     ❌ Erro geral contas pagar: {e}")
        
        return count
    
    def _load_contas_receber_cache(self, start_str: str, end_str: str) -> int:
        """Carrega contas a receber"""
        count = 0
        
        try:
            for pagina in range(1, 10):  # Máximo 10 páginas
                try:
                    result = self.omie_client.omie.listar_contas_receber(
                        pagina=pagina,
                        registros_por_pagina=100
                    )
                    
                    if not (isinstance(result, dict) and 'conta_receber_cadastro' in result):
                        break
                        
                    contas = result['conta_receber_cadastro']
                    if not contas:
                        break
                    
                    for conta in contas:
                        self._add_to_cache(conta, 'conta_receber')
                        count += 1
                    
                    if len(contas) < 100:
                        break
                        
                except Exception as e:
                    print(f"     ⚠️ Erro contas receber página {pagina}: {e}")
                    break
            
        except Exception as e:
            print(f"     ❌ Erro geral contas receber: {e}")
        
        return count
    
    def _add_to_cache(self, lancamento: Dict[str, Any], tipo: str):
        """Adiciona lançamento ao cache com múltiplos índices"""
        try:
            # Extrair dados baseado no tipo
            if tipo == 'conta_corrente':
                codigo_integracao = lancamento.get('cCodIntLanc', '')
                valor = float(lancamento.get('cabecalho', {}).get('nValorLanc', 0))
                # CORREÇÃO: Também indexar por número do documento (onde o OFX ID pode estar truncado)
                numero_documento = lancamento.get('cabecalho', {}).get('cNumDocumento', '')
            else:  # conta_pagar ou conta_receber
                codigo_integracao = lancamento.get('codigo_lancamento_integracao', '')
                valor = float(lancamento.get('valor_documento', 0))
                numero_documento = ''
            
            cached_item = {
                'dados': lancamento,
                'tipo': tipo,
                'valor': valor
            }
            
            # Índice por ID OFX (código de integração)
            if codigo_integracao:
                self.lancamentos_cache['conta_corrente'][codigo_integracao] = cached_item
            
            # NOVA INDEXAÇÃO: Também indexar por número do documento (truncado)
            if numero_documento:
                self.lancamentos_cache['conta_corrente'][numero_documento] = cached_item
            
            # Índice por valor (para busca por valor)
            valor_key = f"{valor:.2f}"
            if valor_key not in self.lancamentos_cache['valor_index']:
                self.lancamentos_cache['valor_index'][valor_key] = []
            
            self.lancamentos_cache['valor_index'][valor_key].append({
                'dados': lancamento,
                'tipo': tipo,
                'valor': valor,
                'codigo_integracao': codigo_integracao
            })
            
        except Exception as e:
            self.errors.append(f"Erro ao adicionar ao cache: {e}")
    
    def _process_transaction_with_cache(self, transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processa transação usando cache (MUITO MAIS RÁPIDO!)
        """
        try:
            ofx_id = transaction['id']
            valor = abs(transaction['amount'])
            
            # 1. BUSCA DIRETA POR ID OFX COMPLETO (mais rápida)
            if ofx_id in self.lancamentos_cache['conta_corrente']:
                cached_item = self.lancamentos_cache['conta_corrente'][ofx_id]
                return self._extract_learning_data(cached_item, transaction)
            
            # 1.1. NOVA BUSCA: Por ID truncado (primeiros 20 caracteres)
            ofx_id_truncated = ofx_id[:20] if len(ofx_id) > 20 else ofx_id
            if ofx_id_truncated != ofx_id and ofx_id_truncated in self.lancamentos_cache['conta_corrente']:
                cached_item = self.lancamentos_cache['conta_corrente'][ofx_id_truncated]
                print(f"  🔍 Encontrado por ID truncado: {ofx_id_truncated}")
                return self._extract_learning_data(cached_item, transaction)
            
            # 2. BUSCA POR VALOR (usando índice)
            valor_key = f"{valor:.2f}"
            if valor_key in self.lancamentos_cache['valor_index']:
                # Buscar correspondência por valor
                for cached_item in self.lancamentos_cache['valor_index'][valor_key]:
                    if abs(cached_item['valor'] - valor) < 0.01:  # Match exato
                        return self._extract_learning_data(cached_item, transaction)
            
            # 3. BUSCA APROXIMADA POR VALOR (±1%)
            tolerance = valor * 0.01
            for cached_valor_str, cached_items in self.lancamentos_cache['valor_index'].items():
                cached_valor = float(cached_valor_str)
                if abs(cached_valor - valor) <= tolerance:
                    for cached_item in cached_items:
                        return self._extract_learning_data(cached_item, transaction)
            
            return None  # Não encontrado
            
        except Exception as e:
            self.errors.append(f"Erro ao processar transação {transaction.get('id', 'N/A')}: {e}")
            return None
    
    def _extract_learning_data(self, cached_item: Dict[str, Any], transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extrai dados de aprendizado do item cached"""
        try:
            dados = cached_item['dados']
            tipo = cached_item['tipo']
            
            if tipo == 'conta_corrente':
                # Extrair categoria e cliente de conta corrente
                detalhes = dados.get('detalhes', [])
                if detalhes and isinstance(detalhes, list):
                    primeiro_detalhe = detalhes[0]
                    categoria_codigo = primeiro_detalhe.get('cCodCategoria', '')
                    cliente_codigo = primeiro_detalhe.get('nCodCli', '')
                    
                    # Buscar nomes
                    categoria_nome = self.omie_client._get_categoria_nome(categoria_codigo) if categoria_codigo else None
                    cliente_nome = self.omie_client._get_cliente_nome(cliente_codigo) if cliente_codigo else None
                    
                    if categoria_nome:
                        return {
                            'categoria': categoria_nome,
                            'cliente_nome': cliente_nome,
                            'tipo': tipo
                        }
            
            else:  # conta_pagar ou conta_receber
                categoria_codigo = dados.get('codigo_categoria', '')
                cliente_codigo = dados.get('codigo_cliente_fornecedor', '')
                
                categoria_nome = self.omie_client._get_categoria_nome(categoria_codigo) if categoria_codigo else None
                cliente_nome = self.omie_client._get_cliente_nome(cliente_codigo) if cliente_codigo else None
                
                if categoria_nome:
                    return {
                        'categoria': categoria_nome,
                        'cliente_nome': cliente_nome,
                        'tipo': tipo
                    }
            
            return None
            
        except Exception as e:
            self.errors.append(f"Erro ao extrair dados: {e}")
            return None
    
    def _clean_description(self, description: str) -> str:
        """Limpa descrição para ML"""
        if not description:
            return ""
        
        import re
        # Remove caracteres especiais e normaliza
        cleaned = re.sub(r'[^\w\s-]', ' ', description.lower())
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

def main():
    """Função principal para teste"""
    load_dotenv()
    
    print("💳 SISTEMA DE APRENDIZADO HISTÓRICO OTIMIZADO - CARTÃO DE CRÉDITO")
    print("=" * 70)
    
    # Inicializar clientes para CARTÃO DE CRÉDITO
    omie_client = OmieClient(
        app_key=os.getenv('OMIE_APP_KEY'),
        app_secret=os.getenv('OMIE_APP_SECRET')
    )
    
    # 🔧 CONFIGURAR PARA CARTÃO DE CRÉDITO (ID 9)
    omie_client.set_account_id(9)
    
    ml_categorizer = MLCategorizer()
    optimized_learning = OptimizedHistoricalLearning(omie_client, ml_categorizer)
    
    # Arquivo de teste - CARTÃO DE CRÉDITO
    ofx_file = "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/Nubank_2025-03-22 (1).ofx"
    
    if not os.path.exists(ofx_file):
        print("❌ Arquivo OFX não encontrado")
        return
    
    print(f"💳 Processando CARTÃO: {os.path.basename(ofx_file)}")
    print(f"🏦 Conta configurada: ID 9 (Cartão Nubank PJ)")
    
    # Executar processamento otimizado
    result = optimized_learning.process_historical_ofx_optimized(ofx_file)
    
    print(f"\n📊 RESULTADO:")
    print(f"Status: {result.get('status')}")
    print(f"Processadas: {result.get('processed', 0)}")
    print(f"Aprendidas: {result.get('learned', 0)}")
    
    if result.get('details'):
        categories = result['details'].get('categories_learned', {})
        print(f"\n💳 CATEGORIAS DE CARTÃO APRENDIDAS ({len(categories)}):")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   💸 {cat}: {count} transações")
        
        clients = result['details'].get('clients_learned', {})
        if clients:
            print(f"\n🏪 ESTABELECIMENTOS APRENDIDOS ({len(clients)}):")
            for client, count in sorted(clients.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   🏪 {client}: {count} transações")

if __name__ == "__main__":
    main()