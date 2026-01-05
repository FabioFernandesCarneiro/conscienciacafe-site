#!/usr/bin/env python3
"""
Sistema de Aprendizado Histórico OTIMIZADO v2.0
Usa exatamente a mesma lógica do smart_reconciliation.py para busca otimizada
"""

import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import ofxparse
from src.omie_client import OmieClient
from src.ml_categorizer import MLCategorizer

class OptimizedHistoricalLearningV2:
    def __init__(self, omie_client: OmieClient, ml_categorizer: MLCategorizer):
        self.omie_client = omie_client
        self.ml_categorizer = ml_categorizer
        
        # Cache idêntico ao smart_reconciliation
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
    
    def process_historical_ofx(self, ofx_file_path: str) -> Dict[str, Any]:
        """Processamento de aprendizado histórico com busca otimizada"""
        try:
            print("🧠 APRENDIZADO HISTÓRICO OTIMIZADO v2.0")
            print("=" * 70)
            
            # ETAPA 1: Ler OFX e extrair período
            print("\n📄 ETAPA 1: Analisando arquivo OFX...")
            ofx_transactions = self._parse_ofx_file(ofx_file_path)
            
            if not ofx_transactions:
                return {"status": "error", "message": "Nenhuma transação encontrada no OFX"}
            
            period_start, period_end = self._get_period_from_transactions(ofx_transactions)
            
            print(f"✅ {len(ofx_transactions)} transações encontradas")
            print(f"📅 Período: {period_start} a {period_end}")
            
            # ETAPA 2: Carregar cache (idêntico ao smart_reconciliation)
            print(f"\n🗃️ ETAPA 2: Carregando cache do período...")
            cache_success = self._load_period_cache(period_start, period_end)
            
            if not cache_success:
                return {"status": "error", "message": "Erro ao carregar cache do período"}
            
            print(f"✅ Cache carregado:")
            print(f"   📊 Total: {self.cache['estatisticas']['total_carregados']} lançamentos")
            print(f"   🏦 Conta Corrente: {self.cache['estatisticas']['conta_corrente']}")
            print(f"   💸 Contas a Pagar: {self.cache['estatisticas']['contas_pagar']}")
            print(f"   💰 Contas a Receber: {self.cache['estatisticas']['contas_receber']}")
            print(f"   📄 Por número documento: {len(self.cache['por_numero_documento'])}")
            
            # ETAPA 3: Processar para aprendizado
            print(f"\n🧠 ETAPA 3: Processando para aprendizado...")
            print("-" * 70)
            
            categories_learned = {}
            clients_learned = {}
            found_matches = 0
            learned_count = 0
            
            for i, transaction in enumerate(ofx_transactions):
                if (i + 1) % 100 == 0:
                    print(f"📊 Progresso: {i+1}/{len(ofx_transactions)} ({found_matches} matches, {learned_count} aprendidas)")
                
                # Buscar usando método idêntico ao smart_reconciliation
                cached_item = self._find_transaction_in_cache(transaction)
                
                if cached_item:
                    found_matches += 1
                    
                    # Extrair categoria REAL do lançamento
                    learning_data = self._extract_learning_data(transaction, cached_item)
                    if learning_data:
                        self._add_to_learning(learning_data, categories_learned, clients_learned)
                        learned_count += 1
            
            # ETAPA 4: Salvar no modelo ML
            print(f"\n💾 ETAPA 4: Salvando no modelo ML...")
            saved_count = self._save_learning_data(categories_learned, clients_learned)
            
            # RESUMO FINAL
            print(f"\n🏁 APRENDIZADO CONCLUÍDO!")
            print("=" * 70)
            print(f"📊 Total transações OFX: {len(ofx_transactions)}")
            print(f"✅ Correspondências: {found_matches} ({(found_matches/len(ofx_transactions)*100):.1f}%)")
            print(f"🧠 Transações aprendidas: {learned_count}")
            print(f"🏷️ Categorias distintas: {len(categories_learned)}")
            print(f"👥 Clientes distintos: {len(clients_learned)}")
            print(f"💾 Salvos no ML: {saved_count}")
            
            if saved_count > 0:
                print(f"\n🎯 TOP 5 CATEGORIAS MAIS FREQUENTES:")
                top_categories = sorted(categories_learned.items(), key=lambda x: x[1], reverse=True)[:5]
                for cat, count in top_categories:
                    print(f"   {count:3d}x - {cat}")
            
            return {
                "status": "success",
                "total_transactions": len(ofx_transactions),
                "found_matches": found_matches,
                "learned_count": learned_count,
                "categories_count": len(categories_learned),
                "clients_count": len(clients_learned),
                "saved_count": saved_count
            }
            
        except Exception as e:
            error_msg = f"Erro no aprendizado: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": error_msg}
    
    # Métodos idênticos ao smart_reconciliation.py
    
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
    
    def _load_conta_corrente_cache(self, start_str: str, end_str: str) -> int:
        """Carrega lançamentos de conta corrente"""
        count = 0
        current_account_str = str(self.omie_client.current_account_id)
        
        try:
            for pagina in range(1, 20):  # Máximo 20 páginas
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
                    break
                
                for lanc in lancamentos:
                    if self.omie_client._is_current_account_lancamento(lanc, current_account_str):
                        self._add_to_cache(lanc, 'conta_corrente')
                        count += 1
                
                if len(lancamentos) < 100:
                    break
        
        except Exception as e:
            print(f"   ⚠️ Erro conta corrente: {e}")
        
        return count
    
    def _load_contas_pagar_cache(self, start_str: str, end_str: str) -> int:
        """Carrega contas a pagar com filtro de data correto da API"""
        count = 0
        
        try:
            for pagina in range(1, 10):
                result = self.omie_client.omie.listar_contas_pagar(
                    pagina=pagina,
                    registros_por_pagina=100,
                    filtrar_por_data_de=start_str,
                    filtrar_por_data_ate=end_str,
                    filtrar_por_emissao_de=start_str,
                    filtrar_por_emissao_ate=end_str
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
            print(f"   ⚠️ Erro contas pagar: {e}")
        
        return count
    
    def _load_contas_receber_cache(self, start_str: str, end_str: str) -> int:
        """Carrega contas a receber com filtro de data correto da API"""
        count = 0
        
        try:
            for pagina in range(1, 10):
                result = self.omie_client.omie.listar_contas_receber(
                    pagina=pagina,
                    registros_por_pagina=100,
                    filtrar_por_data_de=start_str,
                    filtrar_por_data_ate=end_str,
                    filtrar_por_emissao_de=start_str,
                    filtrar_por_emissao_ate=end_str
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
            print(f"   ⚠️ Erro contas receber: {e}")
        
        return count
    
    def _add_to_cache(self, lancamento: Dict[str, Any], tipo: str):
        """Adiciona lançamento ao cache usando a lógica melhorada de busca por número do documento"""
        try:
            # Extrair dados baseado no tipo
            if tipo == 'conta_corrente':
                valor = float(lancamento.get('cabecalho', {}).get('nValorLanc', 0))
                data_str = lancamento.get('cabecalho', {}).get('dDtLanc', '')
                
                # BUSCAR NÚMERO DO DOCUMENTO (método principal de identificação)
                numero_documento = ''
                detalhes = lancamento.get('detalhes', {})
                
                # 1. Se detalhes for um dicionário (consulta específica)
                if isinstance(detalhes, dict):
                    numero_documento = detalhes.get('cNumDoc', '')
                
                # 2. Se detalhes for uma lista (listagem normal) - tentar consulta específica
                elif not numero_documento and isinstance(detalhes, list):
                    codigo_lancamento = lancamento.get('nCodLanc')
                    if codigo_lancamento:
                        try:
                            # CONSULTA ESPECÍFICA para obter detalhes completos
                            lanc_detalhado = self.omie_client.omie._chamar_api(
                                call='ConsultaLancCC',
                                endpoint='financas/contacorrentelancamentos/',
                                param={'nCodLanc': int(codigo_lancamento)}
                            )
                            
                            if isinstance(lanc_detalhado, dict):
                                detalhes_especificos = lanc_detalhado.get('detalhes', {})
                                if isinstance(detalhes_especificos, dict):
                                    numero_documento = detalhes_especificos.get('cNumDoc', '')
                                    if numero_documento:
                                        # Atualizar o lançamento original
                                        lancamento['detalhes'] = detalhes_especificos
                        
                        except Exception as e:
                            pass  # Ignorar erros na consulta específica para não parar o processo
                
                # 3. FALLBACK: Buscar em outros locais
                if not numero_documento:
                    numero_documento = lancamento.get('cabecalho', {}).get('cNumDocumento', '')
                
                # 4. FALLBACK FINAL: Gerar chave única para lançamentos sem identificação
                if not numero_documento:
                    fingerprint = f"v{valor:.2f}_d{data_str}_c{lancamento.get('nCodLanc', '')}"
                    numero_documento = fingerprint
                
            else:  # conta_pagar ou conta_receber
                numero_documento = ''
                valor = float(lancamento.get('valor_documento', 0))
                data_str = lancamento.get('data_vencimento', '')
            
            cached_item = {
                'dados': lancamento,
                'tipo': tipo,
                'valor': valor,
                'data': data_str,
                'numero_documento': numero_documento
            }
            
            # ÍNDICE 1: Por número do documento (método principal de busca)
            if numero_documento:
                self.cache['por_numero_documento'][numero_documento] = cached_item
            
            # ÍNDICE 2: Por valor e data (método fallback)
            if valor and data_str:
                valor_data_key = f"{valor:.2f}_{data_str}"
                if valor_data_key not in self.cache['por_valor_data']:
                    self.cache['por_valor_data'][valor_data_key] = []
                self.cache['por_valor_data'][valor_data_key].append(cached_item)
        
        except Exception as e:
            pass  # Ignorar erros para não parar o processo de cache
    
    def _find_transaction_in_cache(self, transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca transação no cache usando método otimizado idêntico ao smart_reconciliation"""
        ofx_id = transaction['id']
        
        # BUSCA 1: Por número do documento (ID truncado) - BUSCA PRINCIPAL
        ofx_id_truncated = ofx_id[:20] if len(ofx_id) > 20 else ofx_id
        
        if ofx_id_truncated in self.cache['por_numero_documento']:
            return self.cache['por_numero_documento'][ofx_id_truncated]
        
        # BUSCA 2: Por valor e data - BUSCA FALLBACK
        valor = abs(transaction['amount'])
        data_transacao = transaction['date']
        data_str = data_transacao.strftime("%d/%m/%Y")
        valor_data_key = f"{valor:.2f}_{data_str}"
        
        if valor_data_key in self.cache['por_valor_data']:
            matches = self.cache['por_valor_data'][valor_data_key]
            if matches:
                return matches[0]  # Retornar o primeiro match
        
        return None
    
    def _extract_learning_data(self, transaction: Dict[str, Any], cached_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extrai dados REAIS para aprendizado do lançamento encontrado"""
        try:
            dados = cached_item['dados']
            tipo = cached_item['tipo']
            
            # Extrair categoria dependendo do tipo
            category_info = None
            client_info = None
            
            if tipo == 'conta_corrente':
                # Para conta corrente, categoria vem dos detalhes
                detalhes = dados.get('detalhes', {})
                if isinstance(detalhes, dict):
                    cod_categ = detalhes.get('cCodCateg', '')
                    if cod_categ:
                        # Buscar descrição da categoria
                        categorias = self.omie_client.get_categorias()
                        for cat in categorias:
                            if cat.get('codigo') == cod_categ:
                                category_info = cat.get('descricao', cat.get('nome'))
                                break
                        
                        if not category_info:
                            category_info = cod_categ  # Usar código se não encontrar descrição
                
                # Cliente do lançamento
                cod_cliente = detalhes.get('nCodCliente') if isinstance(detalhes, dict) else None
                if cod_cliente:
                    client_info = cod_cliente
            
            elif tipo == 'conta_pagar':
                # Para conta a pagar
                cod_categ = dados.get('codigo_categoria', '')
                if cod_categ:
                    category_info = cod_categ
                
                cod_fornecedor = dados.get('codigo_cliente_fornecedor')
                if cod_fornecedor:
                    client_info = cod_fornecedor
            
            elif tipo == 'conta_receber':
                # Para conta a receber
                cod_categ = dados.get('codigo_categoria', '')
                if cod_categ:
                    category_info = cod_categ
                
                cod_cliente = dados.get('codigo_cliente_fornecedor')
                if cod_cliente:
                    client_info = cod_cliente
            
            if category_info:
                return {
                    'description': transaction['description'],
                    'clean_description': transaction['clean_description'],
                    'amount': transaction['amount'],
                    'category_info': category_info,
                    'client_info': client_info,
                    'tipo': tipo
                }
        
        except Exception as e:
            pass
        
        return None
    
    def _add_to_learning(self, learning_data: Dict[str, Any], categories: Dict, clients: Dict):
        """Adiciona dados ao aprendizado"""
        description = learning_data['clean_description']
        category = learning_data['category_info']
        client = learning_data.get('client_info')
        
        # Registrar categoria
        if category:
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        # Registrar cliente
        if client:
            if client not in clients:
                clients[client] = 0
            clients[client] += 1
    
    def _save_learning_data(self, categories: Dict, clients: Dict) -> int:
        """Salva dados de aprendizado no modelo ML"""
        try:
            total_saved = 0
            
            # Para simplificar, vamos salvar por categoria mais frequente
            for category, count in categories.items():
                if count >= 2:  # Salvar apenas se tiver frequência mínima
                    # Criar um exemplo de aprendizado
                    self.ml_categorizer.add_learning_data(
                        description=category,
                        clean_description=category.lower(),
                        amount=0,  # Valor neutro
                        category_name=category
                    )
                    total_saved += 1
            
            print(f"   ✅ {total_saved} padrões salvos no modelo ML")
            return total_saved
            
        except Exception as e:
            print(f"   ❌ Erro ao salvar: {e}")
            return 0
    
    def _clean_description(self, description: str) -> str:
        """Limpa descrição para processamento"""
        if not description:
            return ""
        
        import re
        cleaned = re.sub(r'[^\\w\\s-]', ' ', description.lower())
        cleaned = re.sub(r'\\s+', ' ', cleaned).strip()
        return cleaned

def main():
    """Função principal"""
    load_dotenv()
    
    # Inicializar componentes
    omie_client = OmieClient(
        app_key=os.getenv('OMIE_APP_KEY'),
        app_secret=os.getenv('OMIE_APP_SECRET')
    )
    omie_client.set_account_id(8)  # Conta corrente
    
    ml_categorizer = MLCategorizer()
    
    # Inicializar aprendizado otimizado
    learner = OptimizedHistoricalLearningV2(omie_client, ml_categorizer)
    
    # Processar arquivo OFX grande
    ofx_file = "NU_826344542_01MAI2025_14AGO2025.ofx"
    
    if not os.path.exists(ofx_file):
        print(f"❌ Arquivo {ofx_file} não encontrado")
        return
    
    result = learner.process_historical_ofx(ofx_file)
    
    # Resultado final
    if result.get('status') == 'success':
        print(f"\n🎉 SUCESSO! Modelo ML atualizado com {result.get('saved_count', 0)} novos padrões")
    else:
        print(f"\n❌ ERRO: {result.get('message', 'Erro desconhecido')}")

if __name__ == "__main__":
    main()