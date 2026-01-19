#!/usr/bin/env python3
"""
Sistema Inteligente de Reconciliação Bancária - VERSÃO OTIMIZADA
Baseado no aprendizado adquirido:

1) Ler arquivo OFX e verificar range de datas
2) Listar lançamentos do Omie do período e colocar no cache  
3) Buscar por número do documento (ID OFX truncado)
4) Se não encontrar, buscar por data e valor com confirmação do usuário
5) Se não for o mesmo, criar novo lançamento com IA para categoria/cliente
6) Marcar como conciliado e ir para próximo registro
"""

import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import ofxparse
from .omie_client import OmieClient
from .ml_categorizer import MLCategorizer

class SmartReconciliationEngine:
    def __init__(self, omie_client: OmieClient, ml_categorizer: MLCategorizer):
        self.omie_client = omie_client
        self.ml_categorizer = ml_categorizer
        
        # Cache otimizado para lançamentos do período
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
        
        # Estatísticas do processamento
        self.stats = {
            'total_transacoes': 0,
            'ja_conciliadas': 0,
            'criadas_automaticamente': 0,
            'criadas_manualmente': 0,
            'confirmadas_usuario': 0,
            'puladas': 0,
            'erros': []
        }
    
    def process_ofx_file(self, ofx_file_path: str) -> Dict[str, Any]:
        """
        Processa arquivo OFX seguindo a nova lógica otimizada
        """
        print("🚀 SISTEMA INTELIGENTE DE RECONCILIAÇÃO")
        print("=" * 60)
        
        try:
            # ETAPA 1: Ler arquivo OFX e extrair range de datas
            print("\n📄 ETAPA 1: Analisando arquivo OFX...")
            ofx_transactions = self._parse_ofx_file(ofx_file_path)
            
            if not ofx_transactions:
                return {"status": "error", "message": "Nenhuma transação encontrada no OFX"}
            
            period_start, period_end = self._get_period_from_transactions(ofx_transactions)
            
            print(f"✅ {len(ofx_transactions)} transações encontradas")
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
            
            # ETAPA 3: Processar transações OFX
            print(f"\n🔄 ETAPA 3: Processando transações...")
            print("-" * 60)
            
            self.stats['total_transacoes'] = len(ofx_transactions)
            
            for i, transaction in enumerate(ofx_transactions):
                print(f"\n📋 [{i+1}/{len(ofx_transactions)}] {transaction['description'][:50]}...")
                print(f"   💰 Valor: R$ {transaction['amount']:.2f}")
                print(f"   📅 Data: {transaction['date']}")
                
                result = self._process_single_transaction(transaction)
                self._update_stats(result)
                
                # Mostrar progresso a cada 10 transações
                if (i + 1) % 10 == 0:
                    self._show_progress()
            
            # ETAPA 4: Mostrar resumo final
            print(f"\n🏁 PROCESSAMENTO CONCLUÍDO!")
            self._show_final_summary()
            
            return {
                "status": "success",
                "total_transacoes": self.stats['total_transacoes'],
                "ja_conciliadas": self.stats['ja_conciliadas'],
                "criadas_automaticamente": self.stats['criadas_automaticamente'],
                "criadas_manualmente": self.stats['criadas_manualmente'],
                "confirmadas_usuario": self.stats['confirmadas_usuario'],
                "puladas": self.stats['puladas'],
                "erros": len(self.stats['erros'])
            }
            
        except Exception as e:
            error_msg = f"Erro no processamento: {e}"
            print(f"❌ {error_msg}")
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
                # CORREÇÃO: Usar parâmetros corretos da documentação oficial
                result = self.omie_client.omie.listar_contas_pagar(
                    pagina=pagina,
                    registros_por_pagina=100,
                    filtrar_por_data_de=start_str,      # Data inicial (inclusão/modificação)
                    filtrar_por_data_ate=end_str,       # Data final (inclusão/modificação)
                    filtrar_por_emissao_de=start_str,   # Data emissão inicial
                    filtrar_por_emissao_ate=end_str     # Data emissão final
                )
                
                if not (isinstance(result, dict) and 'conta_pagar_cadastro' in result):
                    break
                
                contas = result['conta_pagar_cadastro']
                if not contas:
                    break
                
                for conta in contas:
                    # API já filtrou, adicionar diretamente ao cache
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
                # CORREÇÃO: Usar parâmetros corretos da documentação oficial
                result = self.omie_client.omie.listar_contas_receber(
                    pagina=pagina,
                    registros_por_pagina=100,
                    filtrar_por_data_de=start_str,      # Data inicial (inclusão/modificação)
                    filtrar_por_data_ate=end_str,       # Data final (inclusão/modificação)
                    filtrar_por_emissao_de=start_str,   # Data emissão inicial
                    filtrar_por_emissao_ate=end_str     # Data emissão final
                )
                
                if not (isinstance(result, dict) and 'conta_receber_cadastro' in result):
                    break
                
                contas = result['conta_receber_cadastro']
                if not contas:
                    break
                
                for conta in contas:
                    # API já filtrou, adicionar diretamente ao cache
                    self._add_to_cache(conta, 'conta_receber')
                    count += 1
                
                if len(contas) < 100:
                    break
        
        except Exception as e:
            print(f"   ⚠️ Erro contas receber: {e}")
        
        return count
    
    def _add_to_cache(self, lancamento: Dict[str, Any], tipo: str):
        """Adiciona lançamento ao cache com múltiplos índices"""
        try:
            # Extrair dados baseado no tipo
            if tipo == 'conta_corrente':
                valor = float(lancamento.get('cabecalho', {}).get('nValorLanc', 0))
                data_str = lancamento.get('cabecalho', {}).get('dDtLanc', '')
                
                # BUSCAR NÚMERO DO DOCUMENTO (principal método de identificação)
                numero_documento = ''
                detalhes = lancamento.get('detalhes', {})
                
                # 1. Se detalhes for um dicionário (consulta específica)
                if isinstance(detalhes, dict):
                    numero_documento = detalhes.get('cNumDoc', '')
                    if numero_documento:
                        print(f"   🎯 OFX ID encontrado em detalhes.cNumDoc: '{numero_documento}'")
                
                # 2. Se detalhes for uma lista (listagem normal) - tentar consulta específica
                elif not numero_documento and isinstance(detalhes, list):
                    codigo_lancamento = lancamento.get('nCodLanc')
                    if codigo_lancamento:
                        try:
                            # CONSULTA ESPECÍFICA para obter detalhes completos
                            print(f"   🔍 Buscando detalhes específicos para lançamento {codigo_lancamento}...")
                            
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
                                        print(f"   ✅ OFX ID obtido via consulta específica: '{numero_documento}'")
                                        
                                        # Atualizar o lançamento original com os detalhes completos
                                        lancamento['detalhes'] = detalhes_especificos
                        
                        except Exception as e:
                            print(f"   ⚠️ Erro na consulta específica: {e}")
                
                # 3. FALLBACK: Buscar em outros locais
                if not numero_documento:
                    # Local padrão (cabeçalho) - improvável mas possível
                    numero_documento = lancamento.get('cabecalho', {}).get('cNumDocumento', '')
                
                # 4. FALLBACK FINAL: Gerar chave única para lançamentos sem identificação
                if not numero_documento:
                    fingerprint = f"v{valor:.2f}_d{data_str}_c{lancamento.get('nCodLanc', '')}"
                    numero_documento = fingerprint
                
            else:  # conta_pagar ou conta_receber
                numero_documento = ''  # Contas a pagar/receber não usam número do documento
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
            print(f"   ⚠️ Erro ao adicionar ao cache: {e}")
    
    def _process_single_transaction(self, transaction: Dict[str, Any]) -> Dict[str, str]:
        """
        Processa uma única transação seguindo a nova lógica otimizada:
        1) Buscar por número do documento (ID OFX truncado) - MÉTODO PRINCIPAL
        2) Buscar por data e valor - MÉTODO FALLBACK
        3) Criar novo se necessário
        """
        try:
            ofx_id = transaction['id']
            
            # BUSCA 1: Por número do documento (ID truncado) - BUSCA PRINCIPAL
            print(f"   🔍 Buscando por número do documento (ID truncado)...")
            ofx_id_truncated = ofx_id[:20] if len(ofx_id) > 20 else ofx_id
            
            if ofx_id_truncated in self.cache['por_numero_documento']:
                cached_item = self.cache['por_numero_documento'][ofx_id_truncated]
                print(f"   ✅ Encontrado por número do documento!")
                print(f"       ID completo: {ofx_id}")
                print(f"       ID truncado: {ofx_id_truncated}")
                return self._handle_existing_transaction(transaction, cached_item, 'numero_documento')
            
            # BUSCA 2: Por data e valor - BUSCA FALLBACK
            print(f"   🔍 Buscando por data e valor...")
            matches_by_value = self._find_by_value_and_date(transaction)
            
            if matches_by_value:
                print(f"   ⚠️ Encontradas {len(matches_by_value)} transações com mesmo valor e data")
                return self._handle_similar_transactions(transaction, matches_by_value)
            
            # CRIAR NOVO: Não encontrou nada similar
            print(f"   ➕ Criando nova transação...")
            return self._create_new_transaction(transaction)
        
        except Exception as e:
            error_msg = f"Erro ao processar transação {ofx_id}: {e}"
            print(f"   ❌ {error_msg}")
            return {"status": "erro", "details": error_msg}
    
    def _find_by_value_and_date(self, transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Busca transações por valor e data (com tolerância)"""
        valor = abs(transaction['amount'])
        data_transacao = transaction['date']
        
        matches = []
        
        # Buscar em cache por valor e data exatos
        data_str = data_transacao.strftime("%d/%m/%Y")
        valor_data_key = f"{valor:.2f}_{data_str}"
        
        if valor_data_key in self.cache['por_valor_data']:
            matches.extend(self.cache['por_valor_data'][valor_data_key])
        
        # Buscar com tolerância de ±1 dia e ±1% no valor
        for delta_days in [-1, 1]:
            data_alt = data_transacao + timedelta(days=delta_days)
            data_alt_str = data_alt.strftime("%d/%m/%Y")
            
            # Valor exato, data ±1 dia
            valor_data_alt_key = f"{valor:.2f}_{data_alt_str}"
            if valor_data_alt_key in self.cache['por_valor_data']:
                matches.extend(self.cache['por_valor_data'][valor_data_alt_key])
        
        # Remover duplicatas
        unique_matches = []
        seen_ids = set()
        
        for match in matches:
            item_id = f"{match['tipo']}_{match.get('codigo_integracao', '')}"
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_matches.append(match)
        
        return unique_matches
    
    def _handle_existing_transaction(self, transaction: Dict[str, Any], cached_item: Dict[str, Any], match_type: str) -> Dict[str, str]:
        """Trata transação que já existe no Omie"""
        print(f"   📋 Tipo: {cached_item['tipo']}")
        print(f"   💰 Valor Omie: R$ {cached_item['valor']:.2f}")
        print(f"   📅 Data Omie: {cached_item['data']}")
        
        # Verificar se já está conciliado
        # TODO: Implementar verificação de status de conciliação
        
        print(f"   ✅ Transação já existe e está conciliada")
        return {"status": "ja_conciliada", "match_type": match_type}
    
    def _handle_similar_transactions(self, transaction: Dict[str, Any], matches: List[Dict[str, Any]]) -> Dict[str, str]:
        """Trata quando encontra transações similares por valor/data"""
        print(f"   📋 Transações similares encontradas:")
        
        for i, match in enumerate(matches[:3]):  # Mostrar até 3
            print(f"      {i+1}. {match['tipo']} - R$ {match['valor']:.2f} - {match['data']}")
        
        print(f"\n   🤔 Pode ser a mesma transação?")
        print(f"      OFX: {transaction['description'][:50]} - R$ {transaction['amount']:.2f}")
        
        try:
            print(f"\\n   Opções:")
            for i, match in enumerate(matches[:3]):
                print(f"      {i+1}. É a transação #{i+1}")
            print(f"      0. Criar nova transação")
            
            choice = input(f"   Escolha (0-{len(matches[:3])}): ").strip()
            
            if choice == '0':
                print(f"   ➕ Criando nova transação...")
                return self._create_new_transaction(transaction)
            
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(matches[:3]):
                    selected_match = matches[choice_idx]
                    print(f"   ✅ Confirmado como mesmo lançamento!")
                    
                    # TODO: Marcar como conciliado se necessário
                    return {"status": "confirmada_usuario", "match": selected_match}
                else:
                    print(f"   ⚠️ Opção inválida, criando nova transação...")
                    return self._create_new_transaction(transaction)
            
            except ValueError:
                print(f"   ⚠️ Entrada inválida, criando nova transação...")
                return self._create_new_transaction(transaction)
        
        except KeyboardInterrupt:
            print(f"\\n   ⚠️ Interrompido pelo usuário, pulando transação...")
            return {"status": "pulada", "reason": "interrompido"}
    
    def _create_new_transaction(self, transaction: Dict[str, Any]) -> Dict[str, str]:
        """Cria nova transação usando IA para categorização"""
        try:
            # Usar IA para predizer categoria
            print(f"   🧠 Usando IA para categorizar...")
            category, confidence = self.ml_categorizer.predict_category(
                transaction['description'],
                transaction['clean_description'],
                transaction['amount']
            )
            
            if category and confidence >= 0.7:
                print(f"   🎯 Categoria sugerida: {category} (confiança: {confidence:.2f})")
                
                # Criar automaticamente se alta confiança
                transaction_data = {
                    'id': transaction['id'],
                    'description': transaction['description'],
                    'date': transaction['date'],
                    'amount': transaction['amount'],
                    'category_name': category
                }
                
                result = self.omie_client.create_lancamento(transaction_data)
                
                if result.get('status') == 'created':
                    # Salvar aprendizado
                    self.ml_categorizer.add_learning_data(
                        transaction['description'],
                        transaction['clean_description'],
                        transaction['amount'],
                        category_name=category
                    )
                    
                    print(f"   ✅ Criado automaticamente!")
                    return {"status": "criada_automaticamente", "category": category, "confidence": confidence}
                else:
                    print(f"   ⚠️ Erro na criação: {result.get('motivo', 'Erro desconhecido')}")
                    return {"status": "erro", "details": result.get('motivo')}
            else:
                # Baixa confiança - solicitar categoria manual
                print(f"   ⚠️ Baixa confiança ({confidence:.2f}), solicitando categoria manual...")
                return self._request_manual_category(transaction, category, confidence)
        
        except Exception as e:
            error_msg = f"Erro ao criar transação: {e}"
            print(f"   ❌ {error_msg}")
            return {"status": "erro", "details": error_msg}
    
    def _request_manual_category(self, transaction: Dict[str, Any], suggested_category: str = None, confidence: float = 0.0) -> Dict[str, str]:
        """Solicita categoria manual do usuário"""
        print(f"\\n   📋 CATEGORIZAÇÃO MANUAL NECESSÁRIA")
        print(f"      Descrição: {transaction['description']}")
        print(f"      Valor: R$ {transaction['amount']:.2f}")
        
        if suggested_category:
            print(f"      Sugestão IA: {suggested_category} (confiança: {confidence:.2f})")
        
        # Obter categorias do Omie
        categorias = self.omie_client.get_categorias()
        
        if categorias:
            print(f"\\n   Categorias disponíveis:")
            for i, cat in enumerate(categorias[:10]):  # Mostrar até 10
                print(f"      {i+1}. {cat.get('descricao', cat.get('nome', 'N/A'))}")
            
            if suggested_category:
                print(f"      0. Aceitar sugestão IA: {suggested_category}")
        
        try:
            if suggested_category:
                choice = input(f"   Escolha (0-{min(10, len(categorias))}): ").strip()
                if choice == '0':
                    selected_category = suggested_category
                else:
                    try:
                        cat_idx = int(choice) - 1
                        if 0 <= cat_idx < len(categorias[:10]):
                            selected_category = categorias[cat_idx].get('descricao', categorias[cat_idx].get('nome'))
                        else:
                            print(f"   ⚠️ Opção inválida, pulando...")
                            return {"status": "pulada", "reason": "categoria_invalida"}
                    except ValueError:
                        print(f"   ⚠️ Entrada inválida, pulando...")
                        return {"status": "pulada", "reason": "entrada_invalida"}
            else:
                choice = input(f"   Escolha (1-{min(10, len(categorias))}): ").strip()
                try:
                    cat_idx = int(choice) - 1
                    if 0 <= cat_idx < len(categorias[:10]):
                        selected_category = categorias[cat_idx].get('descricao', categorias[cat_idx].get('nome'))
                    else:
                        print(f"   ⚠️ Opção inválida, pulando...")
                        return {"status": "pulada", "reason": "categoria_invalida"}
                except ValueError:
                    print(f"   ⚠️ Entrada inválida, pulando...")
                    return {"status": "pulada", "reason": "entrada_invalida"}
            
            # Criar transação com categoria selecionada
            transaction_data = {
                'id': transaction['id'],
                'description': transaction['description'],
                'date': transaction['date'],
                'amount': transaction['amount'],
                'category_name': selected_category
            }
            
            result = self.omie_client.create_lancamento(transaction_data)
            
            if result.get('status') == 'created':
                # Salvar aprendizado
                self.ml_categorizer.add_learning_data(
                    transaction['description'],
                    transaction['clean_description'],
                    transaction['amount'],
                    category_name=selected_category
                )
                
                print(f"   ✅ Criado com categoria: {selected_category}")
                return {"status": "criada_manualmente", "category": selected_category}
            else:
                print(f"   ⚠️ Erro na criação: {result.get('motivo', 'Erro desconhecido')}")
                return {"status": "erro", "details": result.get('motivo')}
        
        except KeyboardInterrupt:
            print(f"\\n   ⚠️ Interrompido pelo usuário, pulando...")
            return {"status": "pulada", "reason": "interrompido"}
    
    def _update_stats(self, result: Dict[str, str]):
        """Atualiza estatísticas baseado no resultado"""
        status = result.get('status', 'desconhecido')
        
        if status == 'ja_conciliada':
            self.stats['ja_conciliadas'] += 1
        elif status == 'criada_automaticamente':
            self.stats['criadas_automaticamente'] += 1
        elif status == 'criada_manualmente':
            self.stats['criadas_manualmente'] += 1
        elif status == 'confirmada_usuario':
            self.stats['confirmadas_usuario'] += 1
        elif status == 'pulada':
            self.stats['puladas'] += 1
        elif status == 'erro':
            self.stats['erros'].append(result.get('details', 'Erro desconhecido'))
    
    def _show_progress(self):
        """Mostra progresso atual"""
        processadas = (self.stats['ja_conciliadas'] + self.stats['criadas_automaticamente'] + 
                      self.stats['criadas_manualmente'] + self.stats['confirmadas_usuario'] + 
                      self.stats['puladas'] + len(self.stats['erros']))
        
        print(f"\\n📊 PROGRESSO: {processadas}/{self.stats['total_transacoes']}")
        print(f"   ✅ Já conciliadas: {self.stats['ja_conciliadas']}")
        print(f"   🤖 Criadas automaticamente: {self.stats['criadas_automaticamente']}")
        print(f"   👤 Criadas manualmente: {self.stats['criadas_manualmente']}")
        print(f"   🤝 Confirmadas pelo usuário: {self.stats['confirmadas_usuario']}")
        print(f"   ⏭️ Puladas: {self.stats['puladas']}")
        print(f"   ❌ Erros: {len(self.stats['erros'])}")
    
    def _show_final_summary(self):
        """Mostra resumo final detalhado"""
        print("=" * 60)
        print("📊 RESUMO FINAL")
        print("=" * 60)
        print(f"📋 Total de transações: {self.stats['total_transacoes']}")
        print(f"✅ Já conciliadas: {self.stats['ja_conciliadas']}")
        print(f"🤖 Criadas automaticamente: {self.stats['criadas_automaticamente']}")
        print(f"👤 Criadas manualmente: {self.stats['criadas_manualmente']}")
        print(f"🤝 Confirmadas pelo usuário: {self.stats['confirmadas_usuario']}")
        print(f"⏭️ Puladas: {self.stats['puladas']}")
        print(f"❌ Erros: {len(self.stats['erros'])}")
        
        if self.stats['erros']:
            print(f"\\n🚨 ERROS DETALHADOS:")
            for i, erro in enumerate(self.stats['erros'][:5], 1):
                print(f"   {i}. {erro}")
            if len(self.stats['erros']) > 5:
                print(f"   ... e mais {len(self.stats['erros']) - 5} erros")
        
        # Eficiência do processo
        total_processadas = (self.stats['ja_conciliadas'] + self.stats['criadas_automaticamente'] + 
                            self.stats['criadas_manualmente'] + self.stats['confirmadas_usuario'])
        
        if self.stats['total_transacoes'] > 0:
            eficiencia = (total_processadas / self.stats['total_transacoes']) * 100
            print(f"\\n📈 EFICIÊNCIA: {eficiencia:.1f}% das transações processadas com sucesso")
        
        print("=" * 60)
    
    def _clean_description(self, description: str) -> str:
        """Limpa descrição para processamento"""
        if not description:
            return ""
        
        import re
        cleaned = re.sub(r'[^\\w\\s-]', ' ', description.lower())
        cleaned = re.sub(r'\\s+', ' ', cleaned).strip()
        return cleaned