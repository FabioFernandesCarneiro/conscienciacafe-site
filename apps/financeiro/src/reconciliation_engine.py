"""
Engine principal de conciliação bancária com aprendizado inteligente
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3
import os
from .omie_client import OmieClient
from .ml_categorizer import MLCategorizer

class ReconciliationEngine:
    def __init__(self, omie_client: OmieClient, ml_categorizer: MLCategorizer, confidence_threshold: float = 0.6):
        self.omie_client = omie_client
        self.ml_categorizer = ml_categorizer
        self.confidence_threshold = confidence_threshold  # Configurável - padrão mais agressivo
        
    def process_transactions(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processa lista de transações do OFX
        """
        results = {
            'total_transactions': len(transactions),
            'already_reconciled': 0,
            'auto_categorized': 0,
            'manual_review_needed': 0,
            'created': 0,
            'errors': []
        }
        
        print(f"Iniciando processamento de {len(transactions)} transações...")
        
        for i, transaction in enumerate(transactions):
            try:
                print(f"Processando transação {i+1}/{len(transactions)}: {transaction['description'][:50]}...")
                
                result = self._process_single_transaction(transaction)
                
                if result['status'] == 'already_reconciled':
                    results['already_reconciled'] += 1
                elif result['status'] == 'auto_categorized':
                    results['auto_categorized'] += 1
                elif result['status'] == 'manual_review':
                    results['manual_review_needed'] += 1
                elif result['status'] == 'created':
                    results['created'] += 1
                    
            except Exception as e:
                error_msg = f"Erro na transação {transaction.get('id', 'N/A')}: {str(e)}"
                results['errors'].append(error_msg)
                print(error_msg)
        
        self._print_summary(results)
        return results
    
    def _process_single_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma única transação
        """
        # 1. Verificar se já existe lançamento no Omie
        existing = self._find_existing_lancamento(transaction)
        
        if existing:
            # Determinar se é uma correspondência exata (por ID) ou similar (por descrição)
            is_exact_match = existing.get('tipo') in ['conta_receber', 'conta_pagar']
            
            if is_exact_match:
                # Correspondência exata por ID do OFX
                print(f"  🎯 CORRESPONDÊNCIA EXATA - Mesmo ID do OFX")
                
                # Verificar se precisa ser marcado como conciliado
                status = existing.get('status', '')
                if status.lower() not in ['liquidado', 'conciliado']:
                    try:
                        self.omie_client.mark_as_conciliated(existing['id'])
                        print(f"  ✅ Marcado como conciliado!")
                    except Exception as e:
                        print(f"  ⚠️ Erro ao marcar como conciliado: {e}")
                else:
                    print(f"  ℹ️ Já estava conciliado (Status: {status})")
                
                return {'status': 'already_reconciled', 'lancamento': existing, 'match_type': 'exact'}
            else:
                # Correspondência similar por descrição/valor
                print(f"  ⚠️ CORRESPONDÊNCIA SIMILAR - Mesma descrição/valor")
                print(f"  🤔 Pode ser duplicata ou transação diferente")
                
                # Solicitar confirmação do usuário
                return self._handle_similar_transaction(transaction, existing)
        
        # 2. Se não encontrou lançamento existente, usar ML para categorizar
        category, confidence = self.ml_categorizer.predict_category(
            transaction['description'],
            transaction['clean_description'], 
            transaction['amount']
        )
        
        # 3. Buscar sugestões de transações similares
        suggestions = self.ml_categorizer.suggest_similar_transactions(
            transaction['clean_description']
        )
        
        # 4. Lógica inteligente para categorização
        auto_process_result = self._smart_auto_categorization(
            transaction, category, confidence, suggestions
        )
        
        if auto_process_result:
            return auto_process_result
        else:
            # Solicitar revisão manual
            return self._request_manual_review(transaction, suggestions, category, confidence)
    
    def _find_existing_lancamento(self, transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Busca lançamento existente no Omie - PRIMEIRO por ID do OFX, depois por descrição
        """
        try:
            # 🎯 PRIMEIRO: Buscar por ID único do OFX
            ofx_id = transaction.get('id')
            if ofx_id:
                print(f"  🔍 Verificando se transação já foi importada...")
                existing = self.omie_client.search_lancamento_by_ofx_id(ofx_id)
                if existing:
                    print(f"  ✅ Transação JÁ EXISTE no Omie!")
                    print(f"      Tipo: {existing['tipo']}")
                    print(f"      Descrição: {existing['descricao']}")
                    print(f"      Valor: R$ {existing['valor']}")
                    print(f"      Status: {existing['status']}")
                    return existing
                else:
                    print(f"  ℹ️ Transação ainda não foi importada")
            
            # 🔍 SEGUNDO: Buscar por descrição, valor e data (método legado)
            print(f"  🔍 Buscando por descrição e valor...")
            date_str = transaction['date'].strftime('%d/%m/%Y') if hasattr(transaction['date'], 'strftime') else str(transaction['date'])
            
            existing = self.omie_client.search_lancamento_by_description(
                transaction['clean_description'],
                transaction['amount'],
                date_str
            )
            
            if existing:
                print(f"  ⚠️ Encontrado lançamento similar por descrição/valor")
            
            return existing
            
        except Exception as e:
            print(f"  ❌ Erro ao buscar lançamento existente: {e}")
            return None
    
    def _prepare_transaction_data(self, transaction: Dict[str, Any], category: str = None) -> Dict[str, Any]:
        """
        Prepara dados da transação para criar lançamento no Omie
        """
        return {
            'id': transaction['id'],
            'description': transaction['description'][:100],  # Limite de caracteres
            'date': transaction['date'],
            'amount': transaction['amount'],
            'category_name': category,
            'original_description': transaction['description']
        }
    
    def _request_manual_review(self, transaction: Dict[str, Any], suggestions: List[Dict], 
                             predicted_category: str = None, confidence: float = 0.0) -> Dict[str, Any]:
        """
        Solicita revisão manual da transação
        """
        print(f"\n  📋 REVISÃO MANUAL NECESSÁRIA")
        print(f"  Transação: {transaction['description']}")
        print(f"  Valor: R$ {transaction['amount']:.2f}")
        print(f"  Data: {transaction['date']}")
        
        if predicted_category:
            print(f"  Categoria sugerida pela IA: {predicted_category} (Confiança: {confidence:.2f})")
        
        if suggestions:
            print(f"  Transações similares encontradas:")
            for i, suggestion in enumerate(suggestions[:3]):
                print(f"    {i+1}. {suggestion['description']} -> {suggestion['category'] or suggestion['client_supplier']}")
        
        # Obter categorias e clientes do Omie
        categories = self.omie_client.get_categorias()
        clients_suppliers = self.omie_client.get_clientes_fornecedores()
        
        print(f"\n  Opções:")
        print(f"  1. Aceitar sugestão da IA: {predicted_category}" if predicted_category else "  1. Sem sugestão da IA")
        print(f"  2. Escolher categoria manualmente")
        print(f"  3. Verificar lançamentos similares no Omie")
        print(f"  4. Pular esta transação")
        
        try:
            choice = input("  Escolha (1-4): ").strip()
            
            if choice == '1' and predicted_category:
                # Aceitar sugestão da IA
                transaction_data = self._prepare_transaction_data(transaction, predicted_category)
                self.omie_client.create_lancamento(transaction_data)
                
                # Salvar para aprendizado
                self.ml_categorizer.add_learning_data(
                    transaction['description'],
                    transaction['clean_description'],
                    transaction['amount'],
                    category_name=predicted_category
                )
                
                print(f"  ✓ Lançamento criado com categoria: {predicted_category}")
                return {'status': 'created', 'category': predicted_category}
                
            elif choice == '2':
                # Escolher categoria manualmente
                selected_category = self._select_category_interactive(categories)
                
                if selected_category:
                    transaction_data = self._prepare_transaction_data(transaction, selected_category)
                    result = self.omie_client.create_lancamento(transaction_data)
                    
                    if result.get('status') != 'skipped':
                        # Salvar para aprendizado
                        self.ml_categorizer.add_learning_data(
                            transaction['description'],
                            transaction['clean_description'],
                            transaction['amount'],
                            category_name=selected_category
                        )
                        
                        print(f"  ✓ Lançamento criado com categoria: {selected_category}")
                        return {'status': 'created', 'category': selected_category}
                    else:
                        print(f"  ⚠ {result.get('motivo', 'Erro desconhecido')}")
                        return {'status': 'manual_review', 'reason': 'creation_failed'}
                else:
                    print("  ⚠ Categoria não selecionada, transação pulada")
                    return {'status': 'manual_review', 'reason': 'no_category'}
            
            elif choice == '3':
                # Verificar lançamentos similares no Omie
                return self._check_similar_lancamentos_omie(transaction)
                
            else:
                print("  ⏭ Transação pulada")
                return {'status': 'manual_review', 'reason': 'skipped'}
                
        except KeyboardInterrupt:
            print("\\n  ⚠ Processamento interrompido pelo usuário")
            return {'status': 'manual_review', 'reason': 'interrupted'}
        except Exception as e:
            print(f"  ⚠ Erro na revisão manual: {e}")
            return {'status': 'manual_review', 'reason': f'error: {e}'}
    
    def _select_category_interactive(self, categories: List[Dict]) -> str:
        """
        Permite seleção interativa de categoria com nomes legíveis
        """
        if not categories:
            print("  ⚠ Nenhuma categoria cadastrada no Omie")
            nova_categoria = input("  Digite o nome da nova categoria: ").strip()
            return nova_categoria if nova_categoria else None
        
        print(f"\n  📋 Categorias disponíveis ({len(categories)}):")
        for i, cat in enumerate(categories):
            nome = cat.get('descricao', cat.get('nome', f"Categoria {i+1}"))
            codigo = cat.get('codigo', cat.get('id', 'N/A'))
            print(f"    {i+1}. {nome} (ID: {codigo})")
        
        print(f"    0. Digite nova categoria")
        
        while True:
            try:
                cat_choice = input(f"  Escolha a categoria (0-{len(categories)}): ").strip()
                
                if cat_choice == '0':
                    nova_categoria = input("  Nome da nova categoria: ").strip()
                    return nova_categoria if nova_categoria else None
                
                try:
                    cat_index = int(cat_choice) - 1
                    if 0 <= cat_index < len(categories):
                        selected_category = categories[cat_index].get('descricao', categories[cat_index].get('nome'))
                        return selected_category
                    else:
                        print(f"  ❌ Número inválido. Digite entre 0 e {len(categories)}")
                except ValueError:
                    # Usuário digitou o nome da categoria diretamente
                    return cat_choice if cat_choice else None
                    
            except KeyboardInterrupt:
                return None
    
    def _check_similar_lancamentos_omie(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica lançamentos similares no Omie e permite ações
        """
        print(f"\n  🔍 Buscando lançamentos similares no Omie...")
        
        # Buscar por valor similar (±5%)
        valor_min = abs(transaction['amount']) * 0.95
        valor_max = abs(transaction['amount']) * 1.05
        
        # Buscar em contas a receber e pagar
        try:
            similares = []
            
            # Buscar contas a receber
            if transaction['amount'] > 0:
                contas_receber = self.omie_client.omie.listar_contas_receber(pagina=1, registros_por_pagina=20)
                if 'conta_receber_cadastro' in contas_receber:
                    for conta in contas_receber['conta_receber_cadastro']:
                        valor = float(conta.get('valor_documento', 0))
                        if valor_min <= valor <= valor_max:
                            similares.append({
                                'tipo': 'Conta a Receber',
                                'descricao': conta.get('descricao', ''),
                                'valor': valor,
                                'data': conta.get('data_vencimento', ''),
                                'status': conta.get('status_titulo', ''),
                                'id': conta.get('codigo_titulo', '')
                            })
            
            # Buscar contas a pagar  
            if transaction['amount'] < 0:
                contas_pagar = self.omie_client.omie.listar_contas_pagar(pagina=1, registros_por_pagina=20)
                if 'conta_pagar_cadastro' in contas_pagar:
                    for conta in contas_pagar['conta_pagar_cadastro']:
                        valor = float(conta.get('valor_documento', 0))
                        if valor_min <= valor <= valor_max:
                            similares.append({
                                'tipo': 'Conta a Pagar',
                                'descricao': conta.get('descricao', ''),
                                'valor': valor,
                                'data': conta.get('data_vencimento', ''),
                                'status': conta.get('status_titulo', ''),
                                'id': conta.get('codigo_titulo', '')
                            })
            
            if similares:
                print(f"  ✅ {len(similares)} lançamentos similares encontrados:")
                for i, similar in enumerate(similares[:5]):  # Mostrar até 5
                    print(f"    {i+1}. {similar['tipo']}: {similar['descricao']}")
                    print(f"       Valor: R$ {similar['valor']:.2f} | Data: {similar['data']} | Status: {similar['status']}")
                    print(f"       ID: {similar['id']}")
                    print()
                
                print(f"  Opções:")
                print(f"    1-{len(similares[:5])}. Marcar como conciliado")
                print(f"    0. Nenhum é igual - criar novo lançamento")
                
                escolha = input("  Escolha: ").strip()
                
                try:
                    if escolha == '0':
                        print("  ➡ Prosseguindo para criar novo lançamento...")
                        return {'status': 'manual_review', 'reason': 'no_match_create_new'}
                    
                    idx = int(escolha) - 1
                    if 0 <= idx < len(similares[:5]):
                        similar_selected = similares[idx]
                        print(f"  ✅ Marcando como conciliado: {similar_selected['descricao']}")
                        
                        # Simular marcação como conciliado
                        self.omie_client.mark_as_conciliated(similar_selected['id'])
                        
                        return {'status': 'already_reconciled', 'matched': similar_selected}
                    else:
                        print("  ❌ Opção inválida")
                        return {'status': 'manual_review', 'reason': 'invalid_choice'}
                        
                except ValueError:
                    print("  ❌ Digite apenas números")
                    return {'status': 'manual_review', 'reason': 'invalid_input'}
            else:
                print("  ⚠ Nenhum lançamento similar encontrado no Omie")
                print("  ➡ Prosseguindo para criar novo...")
                return {'status': 'manual_review', 'reason': 'no_similar_found'}
                
        except Exception as e:
            print(f"  ❌ Erro ao buscar similares: {e}")
            return {'status': 'manual_review', 'reason': f'search_error: {e}'}
    
    def _handle_similar_transaction(self, transaction: Dict[str, Any], existing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trata transações similares encontradas por descrição/valor
        """
        print(f"\n  ⚠️ TRANSAÇÃO SIMILAR ENCONTRADA")
        print(f"     OFX: {transaction['description']} - R$ {transaction['amount']:.2f}")
        print(f"     Omie: {existing.get('descricao', 'N/A')} - R$ {existing.get('valor_documento', 0):.2f}")
        
        print(f"\n  Opções:")
        print(f"    1. É a mesma transação - marcar como conciliado")
        print(f"    2. É transação diferente - criar nova")
        print(f"    3. Pular esta transação")
        
        try:
            choice = input("  Escolha (1-3): ").strip()
            
            if choice == '1':
                # É a mesma transação
                try:
                    lancamento_id = existing.get('codigo_titulo', existing.get('id', ''))
                    self.omie_client.mark_as_conciliated(lancamento_id)
                    print(f"  ✅ Marcado como conciliado!")
                    return {'status': 'already_reconciled', 'lancamento': existing, 'match_type': 'manual_confirmed'}
                except Exception as e:
                    print(f"  ❌ Erro ao marcar como conciliado: {e}")
                    return {'status': 'manual_review', 'reason': f'conciliation_error: {e}'}
            
            elif choice == '2':
                # É transação diferente - prosseguir para criar nova
                print(f"  ➡️ Prosseguindo para criar nova transação...")
                return None  # Retorna None para continuar fluxo normal
            
            else:
                print(f"  ⏭️ Transação pulada")
                return {'status': 'manual_review', 'reason': 'skipped'}
                
        except KeyboardInterrupt:
            print(f"\n  ⚠️ Operação cancelada")
            return {'status': 'manual_review', 'reason': 'interrupted'}
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            return {'status': 'manual_review', 'reason': f'error: {e}'}
    
    def _print_summary(self, results: Dict[str, Any]):
        """
        Imprime resumo do processamento
        """
        print(f"\\n{'='*50}")
        print(f"RESUMO DO PROCESSAMENTO")
        print(f"{'='*50}")
        print(f"Total de transações: {results['total_transactions']}")
        print(f"Já conciliadas: {results['already_reconciled']}")
        print(f"Categorizadas automaticamente: {results['auto_categorized']}")
        print(f"Criadas manualmente: {results['created']}")
        print(f"Precisam revisão: {results['manual_review_needed']}")
        
        if results['errors']:
            print(f"\\nERROS ({len(results['errors'])}):")
            for error in results['errors'][:5]:  # Mostrar apenas primeiros 5
                print(f"  - {error}")
            if len(results['errors']) > 5:
                print(f"  ... e mais {len(results['errors']) - 5} erros")
        
        # Estatísticas do modelo ML
        stats = self.ml_categorizer.get_learning_stats()
        print(f"\\nESTATÍSTICAS DO APRENDIZADO:")
        print(f"  Transações no histórico: {stats['total_transactions']}")
        print(f"  Com categoria: {stats['categorized']}")
        print(f"  Com cliente/fornecedor: {stats['with_client_supplier']}")
        print(f"  Modelo treinado: {'Sim' if stats['model_trained'] else 'Não'}")
        
        print(f"{'='*50}")
    
    def _smart_auto_categorization(self, transaction: Dict[str, Any], predicted_category: str, 
                                  confidence: float, suggestions: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Lógica inteligente para decisão automática de categorização
        """
        try:
            # Critério 1: Alta confiança na predição
            if confidence >= self.confidence_threshold and predicted_category:
                print(f"  🎯 ALTA CONFIANÇA: {predicted_category} ({confidence:.2f})")
                return self._create_automatic_transaction(transaction, predicted_category, confidence)
            
            # Critério 2: Transação similar com alta confiança
            if suggestions:
                strong_suggestions = [s for s in suggestions if s.get('similarity', 0) > 0.8]
                if strong_suggestions:
                    suggestion = strong_suggestions[0]
                    suggested_category = suggestion.get('category') or suggestion.get('client_supplier')
                    
                    if suggested_category:
                        print(f"  🔗 PADRÃO FORTE: {suggested_category} (similaridade: {suggestion.get('similarity', 0):.2f})")
                        return self._create_automatic_transaction(transaction, suggested_category, 0.85)
            
            # Critério 3: Padrões específicos (palavras-chave)
            smart_category = self._detect_smart_patterns(transaction)
            if smart_category:
                print(f"  🧠 PADRÃO DETECTADO: {smart_category}")
                return self._create_automatic_transaction(transaction, smart_category, 0.8)
            
            # Critério 4: Valor e contexto
            context_category = self._categorize_by_context(transaction)
            if context_category:
                print(f"  📊 CONTEXTO: {context_category}")
                return self._create_automatic_transaction(transaction, context_category, 0.75)
            
            return None  # Não conseguiu categorizar automaticamente
            
        except Exception as e:
            print(f"  ❌ Erro na categorização inteligente: {e}")
            return None
    
    def _create_automatic_transaction(self, transaction: Dict[str, Any], category: str, confidence: float) -> Dict[str, Any]:
        """
        Cria transação automaticamente
        """
        try:
            transaction_data = self._prepare_transaction_data(transaction, category)
            result = self.omie_client.create_lancamento(transaction_data)
            
            if result.get('status') == 'created':
                # Salvar para aprendizado
                self.ml_categorizer.add_learning_data(
                    transaction['description'],
                    transaction['clean_description'],
                    transaction['amount'],
                    category_name=category
                )
                
                print(f"  ✅ Criado automaticamente - Categoria: {category} (Confiança: {confidence:.2f})")
                return {'status': 'auto_categorized', 'category': category, 'confidence': confidence}
            else:
                print(f"  ⚠️ Falha na criação automática: {result.get('motivo', 'Erro desconhecido')}")
                return None
                
        except Exception as e:
            print(f"  ❌ Erro ao criar transação automática: {e}")
            return None
    
    def _detect_smart_patterns(self, transaction: Dict[str, Any]) -> Optional[str]:
        """
        Detecta padrões específicos na descrição para categorização automática
        """
        description = transaction['clean_description'].lower()
        amount = transaction['amount']
        
        # Padrões de receita
        receita_patterns = {
            'Vendas': ['pix recebido', 'ted recebido', 'transferencia recebida', 'pagamento recebido', 'venda'],
            'Cafe': ['consciencia cafe', 'conscienia cafe', 'cafe', 'coffee'],
            'Serviços': ['servico', 'consultoria', 'trabalho']
        }
        
        # Padrões de despesa
        despesa_patterns = {
            'Fornecedores': ['fornecedor', 'compra', 'mercadoria', 'estoque'],
            'Aluguel': ['aluguel', 'locacao', 'imobiliaria'],
            'Energia': ['energia', 'luz', 'eletrica', 'cemig', 'cpfl'],
            'Internet': ['internet', 'telecom', 'vivo', 'claro', 'oi'],
            'Combustível': ['posto', 'gasolina', 'etanol', 'combustivel', 'shell', 'petrobras'],
            'Alimentação': ['ifood', 'uber eats', 'mercado', 'supermercado', 'padaria'],
            'Banco': ['tarifa', 'anuidade', 'manutencao conta', 'juros']
        }
        
        # Verificar padrões de receita (valores positivos)
        if amount > 0:
            for categoria, patterns in receita_patterns.items():
                for pattern in patterns:
                    if pattern in description:
                        return categoria
        
        # Verificar padrões de despesa (valores negativos)
        if amount < 0:
            for categoria, patterns in despesa_patterns.items():
                for pattern in patterns:
                    if pattern in description:
                        return categoria
        
        return None
    
    def _categorize_by_context(self, transaction: Dict[str, Any]) -> Optional[str]:
        """
        Categorização baseada em contexto (valor, horário, etc.)
        """
        amount = abs(transaction['amount'])
        
        # Pequenos valores podem ser taxas
        if amount < 10 and transaction['amount'] < 0:
            return 'Taxas Bancárias'
        
        # Valores redondos grandes podem ser aluguéis ou salários
        if amount >= 1000 and amount % 100 == 0:
            if transaction['amount'] < 0:
                return 'Despesas Fixas'
            else:
                return 'Receitas Principais'
        
        # Valores típicos de refeições
        if 15 <= amount <= 80 and transaction['amount'] < 0:
            description = transaction['clean_description'].lower()
            food_keywords = ['lanche', 'restaurante', 'bar', 'cafe', 'pizza', 'hamburguer']
            if any(keyword in description for keyword in food_keywords):
                return 'Alimentação'
        
        return None