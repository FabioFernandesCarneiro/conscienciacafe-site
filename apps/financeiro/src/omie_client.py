"""
Cliente para integração com API do Omie ERP usando biblioteca oficial
"""

from omieapi import Omie
from typing import Dict, List, Any, Optional

class OmieClient:
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.omie = Omie(app_key, app_secret)
        self.current_account_id = 2103553430  # Padrão: Nubank PJ (antigo ID)
        
    def set_account_id(self, account_id: int):
        """
        Define qual conta usar nas operações
        account_id: 8 = Conta Corrente, 9 = Cartão de Crédito
        """
        # Mapear IDs do sistema para IDs reais do Omie
        account_mapping = {
            8: 2103553430,   # Conta Corrente Nubank PJ  
            9: 2103553430,   # Cartão Nubank PJ (mesmo ID da conta corrente)
            2103553430: 2103553430,  # Permitir usar ID direto também
            2103553431: 2103553431
        }
        
        if account_id in account_mapping:
            self.current_account_id = account_mapping[account_id]
            print(f"🔧 Conta configurada: ID {account_id} -> Omie ID {self.current_account_id}")
        else:
            print(f"⚠️ ID de conta {account_id} não reconhecido, mantendo padrão {self.current_account_id}")
    
    def get_current_account_id(self) -> int:
        """Retorna o ID da conta atualmente configurada"""
        return self.current_account_id
        
    def list_lancamentos(self, pagina: int = 1) -> Dict[str, Any]:
        """
        Lista lançamentos financeiros do Omie - usando método alternativo
        """
        try:
            # Como não temos acesso direto a conta corrente, vamos usar contas a pagar/receber
            result = self.omie.listar_contas_receber(pagina=pagina, registros_por_pagina=50)
            return result
        except Exception as e:
            print(f"Erro ao listar lançamentos: {e}")
            return {"lancamentos": []}
    
    def search_lancamento_by_ofx_id(self, ofx_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca lançamento no Omie pelo ID do OFX (codigo_lancamento_integracao)
        Agora incluindo busca em Lançamentos de Conta Corrente
        """
        try:
            print(f"  🔍 Buscando por ID OFX: {ofx_id}")
            
            # 1. NOVO: Buscar em lançamentos de conta corrente (módulo principal)
            found = self._search_in_conta_corrente(ofx_id)
            if found:
                return found
            
            # 2. Buscar em contas a receber
            response = self.omie.listar_contas_receber(pagina=1, registros_por_pagina=100)
            
            if "conta_receber_cadastro" in response:
                for lancamento in response["conta_receber_cadastro"]:
                    codigo_integracao = lancamento.get("codigo_lancamento_integracao", "")
                    if codigo_integracao == ofx_id:
                        print(f"  ✅ Encontrado em Contas a Receber!")
                        return {
                            'tipo': 'conta_receber',
                            'id': lancamento.get('codigo_titulo', ''),
                            'descricao': lancamento.get('descricao', ''),
                            'valor': lancamento.get('valor_documento', 0),
                            'status': lancamento.get('status_titulo', ''),
                            'data': lancamento.get('data_vencimento', ''),
                            'lancamento': lancamento
                        }
            
            # 3. Buscar em contas a pagar
            response = self.omie.listar_contas_pagar(pagina=1, registros_por_pagina=100)
            
            if "conta_pagar_cadastro" in response:
                for lancamento in response["conta_pagar_cadastro"]:
                    codigo_integracao = lancamento.get("codigo_lancamento_integracao", "")
                    if codigo_integracao == ofx_id:
                        print(f"  ✅ Encontrado em Contas a Pagar!")
                        return {
                            'tipo': 'conta_pagar',
                            'id': lancamento.get('codigo_titulo', ''),
                            'descricao': lancamento.get('descricao', ''),
                            'valor': lancamento.get('valor_documento', 0),
                            'status': lancamento.get('status_titulo', ''),
                            'data': lancamento.get('data_vencimento', ''),
                            'lancamento': lancamento
                        }
                        
        except Exception as e:
            print(f"  ❌ Erro ao buscar por ID OFX: {e}")
            
        return None
    
    def search_lancamento_by_description(self, description: str, amount: float, date: str) -> Optional[Dict[str, Any]]:
        """
        Busca lançamento no Omie por descrição, valor e data (método melhorado)
        """
        try:
            # Buscar por valor exato primeiro (mais preciso)
            found = self._search_by_exact_amount(amount)
            if found:
                return found
            
            # Buscar por valor aproximado (±1%)
            found = self._search_by_approximate_amount(amount, tolerance=0.01)
            if found:
                return found
            
            # Buscar por palavras-chave da descrição
            found = self._search_by_description_keywords(description, amount)
            if found:
                return found
                        
        except Exception as e:
            print(f"Erro ao buscar lançamento: {e}")
            
        return None
    
    def _search_by_exact_amount(self, amount: float) -> Optional[Dict[str, Any]]:
        """Busca por valor exato - AGORA INCLUINDO CONTA CORRENTE"""
        try:
            target_value = abs(amount)
            
            # 1. NOVO: Buscar em lançamentos de conta corrente primeiro
            found = self._search_conta_corrente_by_value(target_value)
            if found:
                return found
            
            # 2. Buscar em contas a receber se valor positivo
            if amount > 0:
                response = self.omie.listar_contas_receber(pagina=1, registros_por_pagina=100)
                if "conta_receber_cadastro" in response:
                    for lancamento in response["conta_receber_cadastro"]:
                        valor_doc = float(lancamento.get("valor_documento", 0))
                        if abs(valor_doc - target_value) < 0.01:  # Diferença menor que 1 centavo
                            print(f"  ✅ Match por valor exato: R$ {valor_doc}")
                            return {
                                'tipo': 'conta_receber',
                                'id': lancamento.get('codigo_lancamento_omie', ''),
                                'descricao': lancamento.get('descricao', ''),
                                'valor': valor_doc,
                                'status': lancamento.get('status_titulo', ''),
                                'data': lancamento.get('data_vencimento', ''),
                                'lancamento': lancamento
                            }
            
            # 3. Buscar em contas a pagar se valor negativo
            else:
                response = self.omie.listar_contas_pagar(pagina=1, registros_por_pagina=100)
                if "conta_pagar_cadastro" in response:
                    for lancamento in response["conta_pagar_cadastro"]:
                        valor_doc = float(lancamento.get("valor_documento", 0))
                        if abs(valor_doc - target_value) < 0.01:
                            print(f"  ✅ Match por valor exato: R$ {valor_doc}")
                            return {
                                'tipo': 'conta_pagar',
                                'id': lancamento.get('codigo_lancamento_omie', ''),
                                'descricao': lancamento.get('descricao', ''),
                                'valor': valor_doc,
                                'status': lancamento.get('status_titulo', ''),
                                'data': lancamento.get('data_vencimento', ''),
                                'lancamento': lancamento
                            }
            
            return None
            
        except Exception as e:
            print(f"  ❌ Erro na busca por valor exato: {e}")
            return None
    
    def _search_by_approximate_amount(self, amount: float, tolerance: float = 0.05) -> Optional[Dict[str, Any]]:
        """Busca por valor aproximado"""
        try:
            target_value = abs(amount)
            margin = target_value * tolerance  # Margem de erro
            
            search_functions = [
                (self.omie.listar_contas_receber, 'conta_receber_cadastro', 'conta_receber'),
                (self.omie.listar_contas_pagar, 'conta_pagar_cadastro', 'conta_pagar')
            ]
            
            for search_func, response_key, tipo in search_functions:
                if (amount > 0 and tipo == 'conta_pagar') or (amount < 0 and tipo == 'conta_receber'):
                    continue  # Pular tipo incompatível
                
                response = search_func(pagina=1, registros_por_pagina=100)
                if response_key in response:
                    for lancamento in response[response_key]:
                        valor_doc = float(lancamento.get("valor_documento", 0))
                        if abs(valor_doc - target_value) <= margin:
                            print(f"  ⚡ Match aproximado: R$ {valor_doc} (diferença: R$ {abs(valor_doc - target_value):.2f})")
                            return {
                                'tipo': tipo,
                                'id': lancamento.get('codigo_lancamento_omie', ''),
                                'descricao': lancamento.get('descricao', ''),
                                'valor': valor_doc,
                                'status': lancamento.get('status_titulo', ''),
                                'data': lancamento.get('data_vencimento', ''),
                                'lancamento': lancamento
                            }
            
            return None
            
        except Exception as e:
            print(f"  ❌ Erro na busca aproximada: {e}")
            return None
    
    def _search_by_description_keywords(self, description: str, amount: float) -> Optional[Dict[str, Any]]:
        """Busca por palavras-chave da descrição"""
        try:
            # Extrair palavras-chave (ignoring common words)
            stopwords = ['pix', 'ted', 'transferencia', 'recebido', 'enviado', 'pelo', 'da', 'do', 'de', 'para', 'em']
            words = [w.strip().lower() for w in description.lower().split() if len(w) > 3 and w not in stopwords]
            
            if not words:
                return None
            
            key_word = words[0]  # Primeira palavra significativa
            target_value = abs(amount)
            
            search_functions = [
                (self.omie.listar_contas_receber, 'conta_receber_cadastro', 'conta_receber'),
                (self.omie.listar_contas_pagar, 'conta_pagar_cadastro', 'conta_pagar')
            ]
            
            for search_func, response_key, tipo in search_functions:
                if (amount > 0 and tipo == 'conta_pagar') or (amount < 0 and tipo == 'conta_receber'):
                    continue
                
                response = search_func(pagina=1, registros_por_pagina=100)
                if response_key in response:
                    for lancamento in response[response_key]:
                        desc_omie = lancamento.get("descricao", "").lower()
                        valor_doc = float(lancamento.get("valor_documento", 0))
                        
                        # Buscar palavra-chave na descrição e valor similar (±10%)
                        if (key_word in desc_omie and 
                            abs(valor_doc - target_value) <= target_value * 0.1):
                            print(f"  🔍 Match por palavra-chave '{key_word}': {desc_omie[:50]}...")
                            return {
                                'tipo': tipo,
                                'id': lancamento.get('codigo_lancamento_omie', ''),
                                'descricao': lancamento.get('descricao', ''),
                                'valor': valor_doc,
                                'status': lancamento.get('status_titulo', ''),
                                'data': lancamento.get('data_vencimento', ''),
                                'lancamento': lancamento
                            }
            
            return None
            
        except Exception as e:
            print(f"  ❌ Erro na busca por palavras-chave: {e}")
            return None
    
    def create_lancamento(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria novo lançamento de conta corrente no Omie (CORRIGIDO!)
        Agora usa incluir_lanc_c_c ao invés de contas a pagar/receber
        """
        try:
            # NOVO: Criar lançamento de conta corrente diretamente
            return self._create_lancamento_conta_corrente(transaction_data)
                
        except Exception as e:
            print(f"Erro ao criar lançamento: {e}")
            return {"erro": str(e)}
    
    def _create_conta_receber(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria conta a receber com ID de integração"""
        try:
            # Dados básicos para conta a receber
            param = {
                "codigo_lancamento_integracao": transaction_data.get("id", ""),  # ID do OFX
                "codigo_cliente_fornecedor": 2055993283,  # Cliente padrão "Consumidor"
                "data_vencimento": transaction_data.get("date").strftime("%d/%m/%Y") if hasattr(transaction_data.get("date"), 'strftime') else transaction_data.get("date"),
                "valor_documento": abs(transaction_data.get("amount", 0)),
                "codigo_categoria": "1.01.01",  # Categoria padrão de receita
                "descricao": transaction_data.get("description", "")[:100],
                "observacao": f"Importado OFX - {transaction_data.get('original_description', '')}"[:500],
                "codigo_tipo_documento": "99"  # Outros
            }
            
            print(f"  💰 Criando conta a receber com ID integração: {param['codigo_lancamento_integracao']}")
            result = self.omie.incluir_conta_receber(param)
            
            print(f"  ✅ Conta a receber criada com sucesso!")
            return {"status": "created", "tipo": "conta_receber", "result": result}
            
        except Exception as e:
            print(f"  ❌ Erro ao criar conta a receber: {e}")
            return {"status": "error", "motivo": str(e)}
    
    def _create_conta_pagar(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria conta a pagar com ID de integração"""
        try:
            # Dados básicos para conta a pagar
            param = {
                "codigo_lancamento_integracao": transaction_data.get("id", ""),  # ID do OFX
                "codigo_cliente_fornecedor": 2055993283,  # Fornecedor padrão (mesmo que cliente consumidor)
                "data_vencimento": transaction_data.get("date").strftime("%d/%m/%Y") if hasattr(transaction_data.get("date"), 'strftime') else transaction_data.get("date"),
                "valor_documento": abs(transaction_data.get("amount", 0)),
                "codigo_categoria": "3.01.01",  # Categoria padrão de despesa
                "descricao": transaction_data.get("description", "")[:100],
                "observacao": f"Importado OFX - {transaction_data.get('original_description', '')}"[:500],
                "codigo_tipo_documento": "99"  # Outros
            }
            
            print(f"  💸 Criando conta a pagar com ID integração: {param['codigo_lancamento_integracao']}")
            result = self.omie.incluir_conta_pagar(param)
            
            print(f"  ✅ Conta a pagar criada com sucesso!")
            return {"status": "created", "tipo": "conta_pagar", "result": result}
            
        except Exception as e:
            print(f"  ❌ Erro ao criar conta a pagar: {e}")
            return {"status": "error", "motivo": str(e)}
    
    def mark_as_conciliated(self, lancamento_id: str) -> Dict[str, Any]:
        """
        Marca lançamento como conciliado
        """
        try:
            # Por enquanto, apenas informamos que foi "conciliado"
            # A marcação real dependeria do tipo de lançamento (conta a pagar/receber)
            print(f"✅ Lançamento {lancamento_id} marcado como conciliado (simulado)")
            return {"status": "conciliado", "id": lancamento_id}
        except Exception as e:
            print(f"Erro ao marcar como conciliado: {e}")
            return {"erro": str(e)}
    
    def get_categorias(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de categorias cadastradas
        """
        try:
            # Usar o método correto com parâmetros obrigatórios
            response = self.omie.listar_categorias(pagina=1, registros_por_pagina=100)
            
            # Verificar se houve erro
            if 'Error' in response:
                print(f"Erro na API de categorias: {response.get('Error', '')}")
                return []
            
            categorias = response.get("categoria_cadastro", [])
            
            # Normalizar estrutura das categorias
            normalized = []
            for cat in categorias:
                normalized.append({
                    'codigo': cat.get('codigo'),
                    'descricao': cat.get('descricao'),
                    'nome': cat.get('descricao'),  # Usar descrição como nome
                    'tipo': 'R' if cat.get('conta_receita') == 'S' else 'D',  # R=Receita, D=Despesa
                    'ativa': cat.get('conta_inativa', 'N') == 'N'
                })
            
            return normalized
            
        except Exception as e:
            print(f"Erro ao obter categorias: {e}")
            return []
    
    def get_categoria_by_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """
        Obtém categoria específica pelo código (método mais eficiente)
        """
        try:
            if not codigo:
                return None
                
            response = self.omie.consultar_categoria(codigo=codigo)
            
            if response and isinstance(response, dict):
                return {
                    'codigo': response.get('codigo'),
                    'descricao': response.get('descricao'),
                    'nome': response.get('descricao'),
                    'tipo': 'R' if response.get('conta_receita') == 'S' else 'D',
                    'natureza': response.get('natureza', '')
                }
            
            return None
            
        except Exception as e:
            print(f"Erro ao consultar categoria {codigo}: {e}")
            return None
    
    def get_clientes_fornecedores(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de clientes e fornecedores
        """
        try:
            result = []
            
            # Buscar clientes
            clientes = self.omie.listar_clientes(pagina=1, registros_por_pagina=100)
            if "clientes_cadastro" in clientes:
                for cliente in clientes["clientes_cadastro"]:
                    # Normalizar dados do cliente
                    normalized_client = {
                        "id": cliente.get("codigo_cliente_omie"),
                        "codigo_integracao": cliente.get("codigo_cliente_integracao"),
                        "nome": cliente.get("razao_social") or cliente.get("nome_fantasia") or "Cliente sem nome",
                        "razao_social": cliente.get("razao_social"),
                        "nome_fantasia": cliente.get("nome_fantasia"),
                        "tipo": "cliente",
                        "ativo": cliente.get("inativo", "N") == "N"
                    }
                    
                    if normalized_client["ativo"]:  # Só incluir clientes ativos
                        result.append(normalized_client)
            
            # Tentar buscar fornecedores se a API suportar
            try:
                fornecedores = self.omie.listar_fornecedores(pagina=1, registros_por_pagina=100)
                if "fornecedor_cadastro" in fornecedores:
                    for fornecedor in fornecedores["fornecedor_cadastro"]:
                        normalized_supplier = {
                            "id": fornecedor.get("codigo_fornecedor_omie"),
                            "codigo_integracao": fornecedor.get("codigo_fornecedor_integracao"),
                            "nome": fornecedor.get("razao_social") or fornecedor.get("nome_fantasia") or "Fornecedor sem nome",
                            "razao_social": fornecedor.get("razao_social"),
                            "nome_fantasia": fornecedor.get("nome_fantasia"),
                            "tipo": "fornecedor",
                            "ativo": fornecedor.get("inativo", "N") == "N"
                        }
                        
                        if normalized_supplier["ativo"]:  # Só incluir fornecedores ativos
                            result.append(normalized_supplier)
            except Exception:
                # API pode não ter método de fornecedores separado
                print("ℹ️ Método listar_fornecedores não disponível - usando apenas clientes")
                pass
                    
            return result
            
        except Exception as e:
            print(f"Erro ao obter clientes/fornecedores: {e}")
            return []
    
    def get_detailed_lancamento(self, tipo: str, codigo_titulo: str) -> Optional[Dict[str, Any]]:
        """
        Obtém dados detalhados de um lançamento específico
        """
        try:
            if tipo == 'conta_receber':
                # Consultar conta a receber específica
                response = self.omie.consultar_conta_receber(codigo_titulo=int(codigo_titulo))
                if response:
                    codigo_categoria = response.get('codigo_categoria')
                    codigo_cliente = response.get('codigo_cliente_fornecedor')
                    
                    return {
                        'tipo': 'conta_receber',
                        'lancamento': response,
                        'categoria_codigo': codigo_categoria,
                        'categoria_nome': self._get_categoria_nome(codigo_categoria),
                        'cliente_codigo': codigo_cliente,
                        'cliente_nome': self._get_cliente_nome(codigo_cliente)
                    }
            
            elif tipo == 'conta_pagar':
                # Consultar conta a pagar específica
                response = self.omie.consultar_conta_pagar(codigo_titulo=int(codigo_titulo))
                if response:
                    codigo_categoria = response.get('codigo_categoria')
                    codigo_fornecedor = response.get('codigo_cliente_fornecedor')
                    
                    return {
                        'tipo': 'conta_pagar',
                        'lancamento': response,
                        'categoria_codigo': codigo_categoria,
                        'categoria_nome': self._get_categoria_nome(codigo_categoria),
                        'fornecedor_codigo': codigo_fornecedor,
                        'fornecedor_nome': self._get_cliente_nome(codigo_fornecedor)
                    }
            
            return None
            
        except Exception as e:
            print(f"Erro ao obter detalhes do lançamento {codigo_titulo}: {e}")
            return None
    
    def _get_categoria_nome(self, codigo_categoria: str) -> Optional[str]:
        """
        Obtém nome da categoria pelo código (método otimizado)
        """
        if not codigo_categoria:
            return None
            
        try:
            # Usar método direto mais eficiente
            categoria = self.get_categoria_by_codigo(codigo_categoria)
            if categoria:
                return categoria.get('descricao') or categoria.get('nome')
            return None
        except Exception:
            return None
    
    def _get_cliente_nome(self, codigo_cliente: int) -> Optional[str]:
        """
        Obtém nome do cliente/fornecedor pelo código
        """
        if not codigo_cliente:
            return None
            
        try:
            clientes = self.get_clientes_fornecedores()
            for cliente in clientes:
                if cliente.get('id') == codigo_cliente:
                    return cliente.get('nome')
            return None
        except Exception:
            return None
    
    def listar_contas_correntes(self) -> List[Dict[str, Any]]:
        """
        Lista contas correntes cadastradas no Omie
        """
        try:
            # Usar a biblioteca oficial com parâmetros corretos
            result = self.omie.listar_contas_correntes(pagina=1, registros_por_pagina=50)
            
            if isinstance(result, dict) and 'ListarContasCorrentes' in result:
                contas = []
                for conta in result['ListarContasCorrentes']:
                    # Filtrar contas ativas
                    if conta.get('inativo', 'N') == 'N':
                        contas.append({
                            'id': conta.get('nCodCC'),
                            'codigo_omie': conta.get('nCodCC'),
                            'descricao': conta.get('descricao', ''),
                            'banco_codigo': conta.get('codigo_banco', ''),
                            'banco_nome': f"Banco {conta.get('codigo_banco', '')}",
                            'agencia': conta.get('codigo_agencia', ''),
                            'conta': conta.get('numero_conta_corrente', ''),
                            'tipo': conta.get('tipo_conta_corrente', 'CC'),
                            'saldo_inicial': conta.get('saldo_inicial', 0)
                        })
                return contas
            else:
                print("⚠️ Estrutura de resposta inesperada ou nenhuma conta encontrada")
                return []
                
        except Exception as e:
            print(f"Erro ao listar contas correntes: {e}")
            return []
    
    def _search_in_conta_corrente(self, ofx_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca lançamento nos Lançamentos de Conta Corrente pelo código de integração OFX
        """
        try:
            print(f"    🏦 Buscando em Lançamentos de Conta Corrente...")
            
            # Usar conta atualmente configurada
            current_account_str = str(self.current_account_id)
            
            # Buscar nas primeiras páginas
            for pagina in range(1, 6):  # Primeiras 5 páginas
                result = self.omie.listar_lanc_c_c(
                    nPagina=pagina,
                    nRegPorPagina=100
                )
                
                if not (isinstance(result, dict) and 'listaLancamentos' in result):
                    continue
                    
                lancamentos = result['listaLancamentos']
                if not lancamentos:
                    break  # Não há mais lançamentos
                
                for lanc in lancamentos:
                    # Verificar código de integração
                    codigo_integracao = lanc.get('cCodIntLanc', '')
                    
                    # NOVA BUSCA: Também verificar no número do documento (onde pode estar truncado)
                    numero_documento = ''
                    if 'cabecalho' in lanc:
                        numero_documento = lanc['cabecalho'].get('cNumDocumento', '')
                    
                    # Match por código de integração completo
                    if codigo_integracao == ofx_id:
                        if self._is_current_account_lancamento(lanc, current_account_str):
                            print(f"    ✅ Encontrado em Conta Corrente por código integração!")
                            return self._format_conta_corrente_result(lanc)
                    
                    # NOVA BUSCA: Match por número do documento (parcial)
                    elif numero_documento and ofx_id.startswith(numero_documento):
                        if self._is_current_account_lancamento(lanc, current_account_str):
                            print(f"    ✅ Encontrado em Conta Corrente por número documento (truncado)!")
                            print(f"        OFX ID: {ofx_id}")
                            print(f"        Num Doc: {numero_documento}")
                            return self._format_conta_corrente_result(lanc)
                
                # Se não encontrou nada e já passou da 3ª página, pode parar
                if pagina > 3 and not any(self._is_current_account_lancamento(l, current_account_str) for l in lancamentos):
                    break
            
            return None
            
        except Exception as e:
            print(f"    ❌ Erro na busca em conta corrente: {e}")
            return None
    
    def _is_current_account_lancamento(self, lancamento: Dict[str, Any], account_id_str: str) -> bool:
        """
        Verifica se o lançamento é da conta atualmente configurada
        """
        try:
            # Verificar no cabeçalho
            if 'cabecalho' in lancamento:
                conta_id = str(lancamento['cabecalho'].get('nCodCC', ''))
                if conta_id == account_id_str:
                    return True
            
            # Verificar nos detalhes
            if 'detalhes' in lancamento and isinstance(lancamento['detalhes'], list):
                for detalhe in lancamento['detalhes']:
                    if isinstance(detalhe, dict):
                        conta_id = str(detalhe.get('nCodCC', ''))
                        if conta_id == account_id_str:
                            return True
            
            return False
            
        except Exception:
            return False
    
    def _format_conta_corrente_result(self, lancamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formata resultado de lançamento de conta corrente no padrão esperado
        """
        try:
            # Extrair informações do cabeçalho
            cabecalho = lancamento.get('cabecalho', {})
            data_lancamento = cabecalho.get('dDtLanc', '')
            valor_lancamento = cabecalho.get('nValorLanc', 0)
            
            # Tentar obter descrição dos detalhes
            descricao = ""
            if 'detalhes' in lancamento and isinstance(lancamento['detalhes'], list):
                for detalhe in lancamento['detalhes']:
                    if isinstance(detalhe, dict):
                        if 'cHistorico' in detalhe and detalhe['cHistorico']:
                            descricao = detalhe['cHistorico']
                            break
                        elif 'cDescricao' in detalhe and detalhe['cDescricao']:
                            descricao = detalhe['cDescricao']
            
            if not descricao:
                descricao = f"Lançamento Conta Corrente {lancamento.get('nCodLanc', '')}"
            
            return {
                'tipo': 'conta_corrente',
                'id': lancamento.get('nCodLanc', ''),
                'codigo_integracao': lancamento.get('cCodIntLanc', ''),
                'descricao': descricao,
                'valor': valor_lancamento,
                'data': data_lancamento,
                'status': 'LANÇADO',  # Lançamentos de CC geralmente estão lançados
                'lancamento': lancamento
            }
            
        except Exception as e:
            print(f"    ❌ Erro ao formatar resultado: {e}")
            return {
                'tipo': 'conta_corrente',
                'id': lancamento.get('nCodLanc', ''),
                'codigo_integracao': lancamento.get('cCodIntLanc', ''),
                'descricao': 'Erro ao obter descrição',
                'valor': 0,
                'data': '',
                'status': 'ERRO',
                'lancamento': lancamento
            }
    
    def _search_conta_corrente_by_value(self, target_value: float, tolerance: float = 0.01) -> Optional[Dict[str, Any]]:
        """
        Busca lançamento em conta corrente por valor
        """
        try:
            print(f"    🏦 Buscando valor R$ {target_value:.2f} em Conta Corrente...")
            
            current_account_str = str(self.current_account_id)
            
            # Buscar com filtro de data mais recente primeiro (últimos 6 meses)
            import datetime
            data_final = datetime.date.today()
            data_inicial = data_final - datetime.timedelta(days=180)  # 6 meses
            
            try:
                result = self.omie.listar_lanc_c_c(
                    nPagina=1,
                    nRegPorPagina=100,
                    dtPagInicial=data_inicial.strftime("%d/%m/%Y"),
                    dtPagFinal=data_final.strftime("%d/%m/%Y")
                )
                
                if isinstance(result, dict) and 'listaLancamentos' in result:
                    lancamentos = result['listaLancamentos']
                    
                    for lanc in lancamentos:
                        # Verificar se é da conta configurada
                        if self._is_current_account_lancamento(lanc, current_account_str):
                            # Verificar valor no cabeçalho
                            if 'cabecalho' in lanc:
                                valor_lanc = float(lanc['cabecalho'].get('nValorLanc', 0))
                                if abs(valor_lanc - target_value) <= tolerance:
                                    print(f"    ✅ Match em Conta Corrente: R$ {valor_lanc:.2f}")
                                    return self._format_conta_corrente_result(lanc)
                            
                            # Também verificar valores nos detalhes
                            if 'detalhes' in lanc and isinstance(lanc['detalhes'], list):
                                for detalhe in lanc['detalhes']:
                                    if isinstance(detalhe, dict) and 'nValor' in detalhe:
                                        valor_det = abs(float(detalhe.get('nValor', 0)))
                                        if abs(valor_det - target_value) <= tolerance:
                                            print(f"    ✅ Match em Conta Corrente (detalhe): R$ {valor_det:.2f}")
                                            return self._format_conta_corrente_result(lanc)
            
            except Exception as e:
                print(f"    ⚠️ Busca com filtro de data falhou, tentando sem filtro: {e}")
                
                # Fallback: buscar sem filtro de data (só primeiras páginas)
                for pagina in range(1, 4):  # Primeiras 3 páginas
                    result = self.omie.listar_lanc_c_c(
                        nPagina=pagina,
                        nRegPorPagina=50
                    )
                    
                    if not (isinstance(result, dict) and 'listaLancamentos' in result):
                        continue
                        
                    lancamentos = result['listaLancamentos']
                    if not lancamentos:
                        break
                    
                    found_nubank = False
                    for lanc in lancamentos:
                        if self._is_current_account_lancamento(lanc, current_account_str):
                            found_nubank = True
                            
                            # Verificar valor
                            if 'cabecalho' in lanc:
                                valor_lanc = float(lanc['cabecalho'].get('nValorLanc', 0))
                                if abs(valor_lanc - target_value) <= tolerance:
                                    print(f"    ✅ Match em Conta Corrente (sem filtro): R$ {valor_lanc:.2f}")
                                    return self._format_conta_corrente_result(lanc)
                    
                    # Se não encontrou nenhum da Nubank nesta página, pode parar
                    if not found_nubank:
                        break
            
            return None
            
        except Exception as e:
            print(f"    ❌ Erro na busca por valor em conta corrente: {e}")
            return None
    
    def _create_lancamento_conta_corrente(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria lançamento de conta corrente no Omie (MÉTODO CORRETO!)
        Este é o método que deveria estar sendo usado desde o início
        """
        try:
            amount = transaction_data.get("amount", 0)
            date = transaction_data.get("date")
            description = transaction_data.get("description", "")
            ofx_id = transaction_data.get("id", "")
            
            # Formatar data
            if hasattr(date, 'strftime'):
                data_formatada = date.strftime("%d/%m/%Y")
            else:
                data_formatada = str(date)
            
            # ID da conta atualmente configurada
            current_account_id = self.current_account_id
            
            # PADRÃO IDENTIFICADO: OFX ID truncado deve ir no número do documento (método principal)
            # Manter padrão de truncar em 20 caracteres conforme encontrado nos dados históricos
            numero_documento_truncado = ofx_id[:20] if len(ofx_id) > 20 else ofx_id
            
            lancamento = {
                "cCodIntLanc": ofx_id,  # ID OFX completo como código de integração (para novos lançamentos)
                "cabecalho": {
                    "dDtLanc": data_formatada,
                    "nCodCC": current_account_id,
                    "nValorLanc": abs(amount),
                    "cNumDocumento": numero_documento_truncado  # PADRÃO: OFX ID TRUNCADO (método principal de busca)
                },
                "detalhes": [{
                    "nCodCC": current_account_id,
                    "nValor": amount,  # Manter sinal (+ crédito, - débito)
                    "cHistorico": f"Importado OFX - {description}"[:200],
                    "cCodCategoria": self._get_default_category_code(amount, description),
                    "nCodCli": self._get_default_client_code()
                }]
            }
            
            print(f"  🏦 Criando lançamento de conta corrente com ID: {ofx_id}")
            print(f"      Valor: R$ {amount:.2f} | Data: {data_formatada}")
            
            # Usar incluir_lanc_c_c (método correto!) - com keyword arguments
            result = self.omie.incluir_lanc_c_c(**lancamento)
            
            print(f"  ✅ Lançamento de conta corrente criado com sucesso!")
            return {
                "status": "created", 
                "tipo": "lancamento_conta_corrente", 
                "result": result,
                "codigo_integracao": ofx_id
            }
            
        except Exception as e:
            print(f"  ❌ Erro ao criar lançamento de conta corrente: {e}")
            return {"status": "error", "motivo": str(e)}
    
    def _get_default_category_code(self, amount: float, description: str) -> str:
        """
        Obtém código de categoria padrão baseado no valor e descrição
        """
        # Lógica simples baseada no que aprendemos
        desc_lower = description.lower()
        
        if amount > 0:  # Crédito/Entrada
            if "granito" in desc_lower or "deposito" in desc_lower:
                return "1.01.01"  # Receita de vendas
            elif "pix" in desc_lower or "transferencia" in desc_lower:
                return "1.01.02"  # Outras receitas
            else:
                return "1.01.01"  # Receita padrão
        else:  # Débito/Saída
            if "boleto" in desc_lower or "pagamento" in desc_lower:
                return "3.01.01"  # Despesas operacionais
            elif "pix" in desc_lower or "transferencia" in desc_lower:
                return "3.01.02"  # Outras despesas
            else:
                return "3.01.01"  # Despesa padrão
    
    def _get_default_client_code(self) -> int:
        """
        Obtém código de cliente/fornecedor padrão
        """
        return 2055993283  # Cliente/Fornecedor padrão "Consumidor"