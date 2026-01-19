#!/usr/bin/env python3
"""
Sistema de Conciliação Inteligente usando API de Extrato
Versão atualizada que usa a API de Extrato do Omie ao invés das 3 APIs separadas
"""

import os
import sys
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import re
from src.omie_client import OmieClient
from src.ml_categorizer import MLCategorizer
from simple_ofx_extractor import SimpleOFXExtractor

class SmartReconciliationExtrato:
    def __init__(self):
        load_dotenv()
        self.omie_client = OmieClient(
            app_key=os.getenv('OMIE_APP_KEY'),
            app_secret=os.getenv('OMIE_APP_SECRET')
        )
        self.ofx_extractor = SimpleOFXExtractor()
        self.ml_categorizer = MLCategorizer()
        
        print("🤖 Carregando sistema de ML...")
        learning_stats = self.ml_categorizer.get_learning_stats()
        print(f"   📊 {learning_stats['total_transactions']} transações na base")
        print(f"   🏷️ {learning_stats['categorized']} categorizadas")
        print(f"   🤖 Modelo treinado: {'Sim' if learning_stats['model_trained'] else 'Não'}")
        
    def extrair_periodo_ofx(self, ofx_file_path):
        """
        Extrai o período de datas (min e max) do arquivo OFX
        """
        print(f"📅 Extraindo período de datas do arquivo OFX...")
        
        try:
            # Usar extrator simples
            data_inicio, data_fim, transacoes_ofx = self.ofx_extractor.extrair_periodo_e_transacoes(ofx_file_path)
            
            if not data_inicio or not data_fim or not transacoes_ofx:
                print("❌ Não foi possível extrair dados do arquivo OFX")
                return None, None
            
            print(f"✅ Período extraído do OFX: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
            print(f"   Total de transações OFX: {len(transacoes_ofx)}")
            
            return data_inicio, data_fim
            
        except Exception as e:
            print(f"❌ Erro ao extrair período do OFX: {e}")
            return None, None
    
    def buscar_movimentos_extrato(self, conta_id, data_inicio, data_fim):
        """
        Busca movimentos usando a API de Extrato do Omie
        """
        print(f"🔍 Buscando movimentos na API de Extrato...")
        print(f"   Conta ID: {conta_id}")
        print(f"   Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
        
        try:
            # Chamar API de Extrato
            result = self.omie_client.omie._chamar_api(
                call='ListarExtrato',
                endpoint='financas/extrato/',
                param={
                    'nCodCC': int(conta_id),
                    'dPeriodoInicial': data_inicio.strftime('%d/%m/%Y'),
                    'dPeriodoFinal': data_fim.strftime('%d/%m/%Y')
                }
            )
            
            if not isinstance(result, dict) or 'listaMovimentos' not in result:
                print("❌ Resposta inválida da API de Extrato")
                return []
            
            movimentos_raw = result['listaMovimentos']
            print(f"📦 {len(movimentos_raw)} movimentos brutos retornados pela API")
            
            # Processar e filtrar movimentos
            movimentos_processados = []
            data_inicio_obj = data_inicio
            data_fim_obj = data_fim
            
            for movimento in movimentos_raw:
                # Pular saldo anterior e registros de saldo inicial
                cliente = movimento.get('cDesCliente', '')
                if cliente == 'SALDO ANTERIOR' or cliente == 'SALDO INICIAL':
                    continue
                
                # Verificar data
                data_movimento_str = movimento.get('dDataLancamento', '')
                if not data_movimento_str:
                    continue
                
                try:
                    data_movimento_obj = datetime.strptime(data_movimento_str, '%d/%m/%Y').date()
                    
                    # Filtro rigoroso de data
                    if data_movimento_obj < data_inicio_obj or data_movimento_obj > data_fim_obj:
                        continue
                except ValueError:
                    continue
                
                # Verificar valor
                valor = float(movimento.get('nValorDocumento', 0))
                if valor == 0:
                    continue
                
                # Processar movimento
                movimento_processado = {
                    'data': data_movimento_str,
                    'data_obj': data_movimento_obj,
                    'valor': abs(valor),
                    'valor_original': valor,
                    'tipo': 'Crédito' if valor > 0 else 'Débito',
                    'descricao': movimento.get('cObservacoes', ''),
                    'cliente': movimento.get('cDesCliente', ''),
                    'categoria': movimento.get('cDesCategoria', 'Não Categorizado'),
                    'categoria_codigo': movimento.get('cCodCategoria', ''),
                    'documento': movimento.get('cNumero', ''),
                    'codigo_lancamento': movimento.get('nCodLancamento', ''),
                    'conciliado': movimento.get('cSituacao', '') == 'Conciliado',
                    'natureza': movimento.get('cNatureza', ''),
                    'tipo_documento': movimento.get('cTipoDocumento', ''),
                    'origem': movimento.get('cOrigem', ''),
                    
                    # Campos para conciliação
                    'numero_documento_truncado': self._truncar_numero_documento(movimento.get('cNumero', '')),
                    'fonte': 'extrato_api'
                }
                
                movimentos_processados.append(movimento_processado)
            
            print(f"✅ {len(movimentos_processados)} movimentos processados e válidos")
            
            # Estatísticas
            creditos = len([m for m in movimentos_processados if m['tipo'] == 'Crédito'])
            debitos = len([m for m in movimentos_processados if m['tipo'] == 'Débito'])
            conciliados = len([m for m in movimentos_processados if m['conciliado']])
            
            print(f"   📊 Créditos: {creditos}, Débitos: {debitos}")
            print(f"   📊 Já conciliados: {conciliados}")
            
            return movimentos_processados
            
        except Exception as e:
            print(f"❌ Erro ao buscar movimentos na API de Extrato: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _truncar_numero_documento(self, numero_documento):
        """
        Trunca número do documento para 20 caracteres (limite do Omie)
        """
        if not numero_documento:
            return ""
        
        # Remover caracteres especiais e espaços
        numero_limpo = re.sub(r'[^\w]', '', str(numero_documento))
        
        # Truncar para 20 caracteres
        return numero_limpo[:20] if len(numero_limpo) > 20 else numero_limpo
    
    def conciliar(self, ofx_file_path, conta_id):
        """
        Executa conciliação usando API de Extrato
        """
        print("🚀 INICIANDO CONCILIAÇÃO COM API DE EXTRATO")
        print("=" * 60)
        
        # 1. Extrair período do OFX
        data_inicio, data_fim = self.extrair_periodo_ofx(ofx_file_path)
        if not data_inicio or not data_fim:
            print("❌ Não foi possível extrair período do arquivo OFX")
            return None
        
        # 2. Processar transações OFX
        print(f"\n📄 Processando arquivo OFX...")
        _, _, transacoes_ofx = self.ofx_extractor.extrair_periodo_e_transacoes(ofx_file_path)
        if not transacoes_ofx:
            print("❌ Nenhuma transação encontrada no OFX")
            return None
        
        print(f"✅ {len(transacoes_ofx)} transações carregadas do OFX")
        
        # 3. Buscar movimentos na API de Extrato
        print(f"\n🔍 Buscando dados na API de Extrato...")
        movimentos_omie = self.buscar_movimentos_extrato(conta_id, data_inicio, data_fim)
        if not movimentos_omie:
            print("❌ Nenhum movimento encontrado na API de Extrato")
            return None
        
        # 4. Executar conciliação
        print(f"\n🔄 Executando conciliação...")
        resultados = self._executar_conciliacao(transacoes_ofx, movimentos_omie)
        
        # 5. Exibir resultados
        self._exibir_resultados(resultados)
        
        return resultados
    
    def _executar_conciliacao(self, transacoes_ofx, movimentos_omie):
        """
        Executa a lógica de conciliação entre OFX e movimentos da API
        """
        matches = []
        ofx_nao_conciliadas = []
        omie_nao_conciliadas = movimentos_omie.copy()
        
        print(f"🔄 Conciliando {len(transacoes_ofx)} transações OFX com {len(movimentos_omie)} movimentos Omie...")
        
        for transacao_ofx in transacoes_ofx:
            match_encontrado = False
            
            # Tentar diferentes critérios de matching
            for movimento_omie in movimentos_omie:
                if movimento_omie in omie_nao_conciliadas:  # Só considerar não conciliados
                    
                    # Critério 1: Número do documento (se ambos tiverem)
                    if (transacao_ofx.get('numero_documento') and 
                        movimento_omie.get('numero_documento_truncado') and
                        self._match_numero_documento(transacao_ofx, movimento_omie)):
                        
                        matches.append({
                            'ofx': transacao_ofx,
                            'omie': movimento_omie,
                            'criterio': 'numero_documento',
                            'confianca': 0.95
                        })
                        omie_nao_conciliadas.remove(movimento_omie)
                        match_encontrado = True
                        break
                    
                    # Critério 2: Valor e data próxima (±5 dias)
                    elif self._match_valor_data(transacao_ofx, movimento_omie):
                        matches.append({
                            'ofx': transacao_ofx,
                            'omie': movimento_omie,
                            'criterio': 'valor_data',
                            'confianca': 0.85
                        })
                        omie_nao_conciliadas.remove(movimento_omie)
                        match_encontrado = True
                        break
                    
                    # Critério 3: Valor exato e descrição parcial
                    elif self._match_valor_descricao(transacao_ofx, movimento_omie):
                        matches.append({
                            'ofx': transacao_ofx,
                            'omie': movimento_omie,
                            'criterio': 'valor_descricao',
                            'confianca': 0.75
                        })
                        omie_nao_conciliadas.remove(movimento_omie)
                        match_encontrado = True
                        break
            
            if not match_encontrado:
                # Adicionar sugestões inteligentes para transações não conciliadas
                transacao_com_sugestoes = self._adicionar_sugestoes_inteligentes(transacao_ofx)
                ofx_nao_conciliadas.append(transacao_com_sugestoes)
        
        return {
            'matches': matches,
            'ofx_nao_conciliadas': ofx_nao_conciliadas,
            'omie_nao_conciliadas': omie_nao_conciliadas,
            'total_ofx': len(transacoes_ofx),
            'total_omie': len(movimentos_omie)
        }
    
    def _match_numero_documento(self, transacao_ofx, movimento_omie):
        """
        Verifica match por número do documento
        """
        ofx_doc = self._truncar_numero_documento(transacao_ofx.get('numero_documento', ''))
        omie_doc = movimento_omie.get('numero_documento_truncado', '')
        
        if not ofx_doc or not omie_doc:
            return False
        
        return ofx_doc == omie_doc
    
    def _match_valor_data(self, transacao_ofx, movimento_omie, tolerancia_dias=5):
        """
        Verifica match por valor e data próxima
        """
        # Verificar valor com tolerância maior para conta corrente
        valor_ofx = abs(float(transacao_ofx.get('valor', 0)))
        valor_omie = abs(float(movimento_omie.get('valor', 0)))
        
        # Tolerância de valor: R$ 0.10 ou 0.1% do valor
        tolerancia_valor = max(0.10, valor_ofx * 0.001)
        if abs(valor_ofx - valor_omie) > tolerancia_valor:
            return False
        
        # Verificar data (tolerância maior para processos bancários)
        try:
            data_ofx = transacao_ofx.get('data_obj') or datetime.strptime(str(transacao_ofx.get('data')), '%Y-%m-%d').date()
            data_omie = movimento_omie.get('data_obj')
            
            if not data_omie:
                return False
            
            diferenca_dias = abs((data_ofx - data_omie).days)
            return diferenca_dias <= tolerancia_dias
            
        except Exception:
            return False
    
    def _match_valor_descricao(self, transacao_ofx, movimento_omie):
        """
        Verifica match por valor exato e similaridade na descrição
        """
        # Verificar valor (deve ser muito próximo)
        valor_ofx = abs(float(transacao_ofx.get('valor', 0)))
        valor_omie = abs(float(movimento_omie.get('valor', 0)))
        
        if abs(valor_ofx - valor_omie) > 0.05:  # Tolerância de 5 centavos
            return False
        
        # Verificar similaridade na descrição
        desc_ofx = str(transacao_ofx.get('descricao', '')).lower()
        desc_omie = str(movimento_omie.get('descricao', '')).lower()
        cliente_omie = str(movimento_omie.get('cliente', '')).lower()
        
        # Remover caracteres especiais e espaços extras
        desc_ofx = re.sub(r'[^\w\s]', ' ', desc_ofx)
        desc_omie = re.sub(r'[^\w\s]', ' ', desc_omie)
        cliente_omie = re.sub(r'[^\w\s]', ' ', cliente_omie)
        
        # Verificar palavras chave em comum
        palavras_ofx = set(word for word in desc_ofx.split() if len(word) > 3)
        palavras_omie = set(word for word in desc_omie.split() if len(word) > 3)
        palavras_cliente = set(word for word in cliente_omie.split() if len(word) > 3)
        
        # Combinar descrições do Omie
        todas_palavras_omie = palavras_omie.union(palavras_cliente)
        
        # Verificar interseção
        palavras_comuns = palavras_ofx.intersection(todas_palavras_omie)
        
        # Precisa ter pelo menos 1 palavra em comum ou similaridade alta
        if len(palavras_comuns) >= 1:
            return True
        
        # Verificar se uma descrição contém a outra (parcialmente)
        if (len(desc_ofx) > 5 and desc_ofx in desc_omie) or \
           (len(desc_omie) > 5 and desc_omie in desc_ofx) or \
           (len(desc_ofx) > 5 and desc_ofx in cliente_omie):
            return True
        
        return False
    
    def _adicionar_sugestoes_inteligentes(self, transacao_ofx):
        """
        Adiciona sugestões inteligentes de categoria e cliente usando ML
        """
        print(f"🤖 Gerando sugestão para: {transacao_ofx.get('descricao', '')[:50]}...")
        
        transacao_com_sugestoes = transacao_ofx.copy()
        
        descricao = transacao_ofx.get('descricao', '')
        valor = float(transacao_ofx.get('valor', 0))
        
        # Limpar descrição para ML
        clean_description = self._clean_description_for_ml(descricao)
        print(f"   📝 Descrição limpa: {clean_description}")
        
        # 1. Tentar predição com modelo ML
        try:
            categoria_ml, confianca_ml = self.ml_categorizer.predict_category(
                descricao, clean_description, abs(valor)
            )
            print(f"   🤖 Predição ML: {categoria_ml} (confiança: {confianca_ml:.2f})")
        except Exception as e:
            print(f"   ❌ Erro na predição ML: {e}")
            categoria_ml, confianca_ml = None, 0.0
        
        # 2. Buscar transações similares no histórico
        try:
            similares = self.ml_categorizer.suggest_similar_transactions(clean_description, limit=3)
            print(f"   📚 Transações similares encontradas: {len(similares)}")
            if similares:
                for sim in similares[:2]:  # Mostrar 2 primeiras
                    print(f"      - {sim.get('category', 'N/A')} | {sim.get('client_supplier', 'N/A')} (freq: {sim.get('frequency', 0)})")
        except Exception as e:
            print(f"   ❌ Erro ao buscar similares: {e}")
            similares = []
        
        # 3. Gerar sugestão final
        categoria_sugerida = ''
        cliente_sugerido = ''
        confianca_final = 0.0
        fonte_sugestao = 'fallback'
        
        # Usar ML se confiança for alta
        if categoria_ml and confianca_ml > 0.5:
            # Buscar código da categoria se o ML retornou um nome
            codigo_categoria_ml = self._buscar_codigo_categoria_por_nome(categoria_ml)
            categoria_sugerida = codigo_categoria_ml or categoria_ml
            confianca_final = confianca_ml
            fonte_sugestao = 'ml'
            print(f"   ✅ Usando ML: {categoria_ml} -> {categoria_sugerida} (confiança: {confianca_ml:.2f})")
        
        # Usar histórico se disponível
        if similares:
            melhor_similar = max(similares, key=lambda x: x['frequency'])
            if melhor_similar['category']:
                # Tentar encontrar o código da categoria pelo nome
                codigo_categoria = self._buscar_codigo_categoria_por_nome(melhor_similar['category'])
                if not categoria_sugerida:  # Só usar se ML não sugeriu
                    categoria_sugerida = codigo_categoria or melhor_similar['category']
                    confianca_final = max(confianca_final, 0.8)
                    fonte_sugestao = 'historico'
                    print(f"   ✅ Usando histórico para categoria: {melhor_similar['category']} -> {categoria_sugerida}")
            
            if melhor_similar['client_supplier']:
                cliente_sugerido = melhor_similar['client_supplier']
                confianca_final += 0.1
                print(f"   ✅ Usando histórico para cliente: {melhor_similar['client_supplier']}")
        
        # Fallback: extrair nome da descrição
        if not cliente_sugerido:
            cliente_extraido = self._extrair_nome_da_descricao(descricao)
            cliente_sugerido = cliente_extraido or 'A definir'
            if cliente_extraido:
                print(f"   ✅ Nome extraído da descrição: {cliente_extraido}")
            else:
                print(f"   ⚠️ Nenhum nome encontrado, usando 'A definir'")
        
        # 4. VALIDAÇÃO INTELIGENTE DE CLIENTES
        cliente_sugerido = self._validar_cliente_sugerido(cliente_sugerido, descricao)
        
        # Adicionar sugestões à transação
        transacao_com_sugestoes['sugestoes'] = {
            'categoria': categoria_sugerida,
            'cliente': cliente_sugerido,
            'confianca': min(confianca_final, 1.0),
            'fonte': fonte_sugestao
        }
        
        print(f"   🎯 Sugestão final: categoria='{categoria_sugerida}', cliente='{cliente_sugerido}', fonte='{fonte_sugestao}'")
        
        return transacao_com_sugestoes
    
    def _clean_description_for_ml(self, description):
        """Limpa descrição para uso no ML"""
        if not description:
            return ""
        
        # Converter para minúsculas e remover caracteres especiais
        clean = description.lower()
        clean = re.sub(r'[^\w\s]', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    
    def _extrair_nome_da_descricao(self, descricao):
        """Extrai nome de pessoa/empresa da descrição"""
        if not descricao:
            return None
        
        # Padrões comuns para extrair nomes
        patterns = [
            r'pix.*?-\s*([A-Z][A-Z\s]+[A-Z])',  # PIX - NOME PESSOA
            r'transferência.*?-\s*([A-Z][A-Z\s]+[A-Z])',  # Transferência - NOME
            r'recebida.*?-\s*([A-Z][A-Z\s]+[A-Z])',  # Recebida - NOME
            r'enviada.*?-\s*([A-Z][A-Z\s]+[A-Z])',  # Enviada - NOME
            r'para\s+([A-Z][A-Z\s]+[A-Z])',  # para NOME
            r'de\s+([A-Z][A-Z\s]+[A-Z])',  # de NOME
        ]
        
        for pattern in patterns:
            match = re.search(pattern, descricao, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                # Validar se parece um nome (pelo menos 2 palavras)
                if len(nome.split()) >= 2 and len(nome) > 5:
                    return nome.title()
        
        return None
    
    def _buscar_codigo_categoria_por_nome(self, nome_categoria):
        """Busca código da categoria pelo nome (similar ao sistema web)"""
        print(f"   🔍 Buscando código para categoria: '{nome_categoria}'")
        
        try:
            # Buscar categorias do Omie
            result = self.omie_client.omie._chamar_api(
                call='ListarCategorias',
                endpoint='geral/categorias/',
                param={'pagina': 1, 'registros_por_pagina': 100}
            )
            
            if isinstance(result, dict) and 'categoria_cadastro' in result:
                print(f"   📊 {len(result['categoria_cadastro'])} categorias encontradas no Omie")
                
                # Busca exata
                for cat in result['categoria_cadastro']:
                    if cat.get('descricao', '').lower() == nome_categoria.lower():
                        codigo = cat.get('codigo', '')
                        print(f"   ✅ Match exato encontrado: '{nome_categoria}' -> {codigo}")
                        return codigo
                        
                # Se não encontrou exato, tentar busca aproximada
                for cat in result['categoria_cadastro']:
                    desc = cat.get('descricao', '').lower()
                    nome_lower = nome_categoria.lower()
                    if nome_lower in desc or desc in nome_lower:
                        codigo = cat.get('codigo', '')
                        print(f"   📌 Match aproximado: '{nome_categoria}' -> '{cat.get('descricao', '')}' (código: {codigo})")
                        return codigo
                
                print(f"   ⚠️ Nenhuma categoria encontrada para: '{nome_categoria}'")
                print(f"   📝 Primeiras 3 categorias disponíveis:")
                for i, cat in enumerate(result['categoria_cadastro'][:3]):
                    print(f"      {i+1}. {cat.get('codigo', '')} - {cat.get('descricao', '')}")
                        
        except Exception as e:
            print(f"   ❌ Erro ao buscar categoria por nome: {e}")
        
        return None
    
    def _validar_cliente_sugerido(self, cliente_sugerido, descricao_original):
        """
        Valida se o cliente sugerido existe no Omie, se não sugere PIX para transações PIX
        """
        print(f"   🔍 Validando cliente sugerido: '{cliente_sugerido}'")
        
        # Se não temos cliente sugerido, usar PIX como fallback para transações PIX
        if not cliente_sugerido or cliente_sugerido in ['A definir', 'N/A']:
            if self._eh_transacao_pix(descricao_original):
                print(f"   🎯 Transação PIX sem cliente específico -> PIX")
                return 'PIX'
            return cliente_sugerido
        
        # Se o cliente já é PIX, manter
        if cliente_sugerido.upper() == 'PIX':
            print(f"   ✅ Cliente já é PIX, mantendo")
            return 'PIX'
        
        # Verificar se cliente existe no Omie
        try:
            clientes_omie = self._buscar_clientes_omie()
            cliente_existe = self._cliente_existe_no_omie(cliente_sugerido, clientes_omie)
            
            if cliente_existe:
                print(f"   ✅ Cliente encontrado no Omie: '{cliente_sugerido}'")
                return cliente_sugerido
            else:
                print(f"   ❌ Cliente '{cliente_sugerido}' não encontrado no Omie")
                
                # Se é transação PIX e cliente não existe, usar PIX
                if self._eh_transacao_pix(descricao_original):
                    print(f"   🎯 Transação PIX com cliente não cadastrado -> PIX")
                    return 'PIX'
                else:
                    print(f"   ⚠️ Transação não-PIX com cliente não cadastrado, mantendo sugestão")
                    return cliente_sugerido
                    
        except Exception as e:
            print(f"   ❌ Erro ao validar cliente: {e}")
            # Em caso de erro, manter sugestão original
            return cliente_sugerido
    
    def _eh_transacao_pix(self, descricao):
        """Verifica se é uma transação PIX pela descrição"""
        if not descricao:
            return False
        
        descricao_lower = descricao.lower()
        palavras_pix = ['pix', 'transferência', 'transferencia']
        
        return any(palavra in descricao_lower for palavra in palavras_pix)
    
    def _buscar_clientes_omie(self):
        """Busca lista de clientes/fornecedores do Omie (com cache)"""
        # Cache simples para evitar múltiplas chamadas à API
        if not hasattr(self, '_cache_clientes'):
            print(f"   📡 Buscando clientes do Omie...")
            
            try:
                # Usar mesmo método do app.py
                result = self.omie_client.omie._chamar_api(
                    call='ListarClientes',
                    endpoint='geral/clientes/',
                    param={'pagina': 1, 'registros_por_pagina': 500}
                )
                
                clientes = []
                if isinstance(result, dict) and 'clientes_cadastro' in result:
                    for cliente in result['clientes_cadastro']:
                        nome = cliente.get('nome_fantasia') or cliente.get('razao_social', '')
                        if nome:
                            clientes.append(nome.strip())
                
                # Buscar fornecedores também
                result_fornecedores = self.omie_client.omie._chamar_api(
                    call='ListarFornecedores', 
                    endpoint='geral/fornecedores/',
                    param={'pagina': 1, 'registros_por_pagina': 500}
                )
                
                if isinstance(result_fornecedores, dict) and 'fornecedor_cadastro' in result_fornecedores:
                    for fornecedor in result_fornecedores['fornecedor_cadastro']:
                        nome = fornecedor.get('nome_fantasia') or fornecedor.get('razao_social', '')
                        if nome:
                            clientes.append(nome.strip())
                
                # Adicionar PIX como cliente padrão se não existir
                if 'PIX' not in clientes:
                    clientes.append('PIX')
                
                self._cache_clientes = clientes
                print(f"   ✅ {len(clientes)} clientes/fornecedores carregados")
                
            except Exception as e:
                print(f"   ❌ Erro ao buscar clientes: {e}")
                self._cache_clientes = ['PIX']  # Fallback para PIX apenas
        
        return self._cache_clientes
    
    def _cliente_existe_no_omie(self, cliente_sugerido, clientes_omie):
        """Verifica se cliente existe na lista do Omie (busca flexível)"""
        if not cliente_sugerido or not clientes_omie:
            return False
        
        cliente_lower = cliente_sugerido.lower().strip()
        
        # Busca exata
        for cliente_omie in clientes_omie:
            if cliente_omie.lower().strip() == cliente_lower:
                return True
        
        # Busca parcial (cliente sugerido contém nome do Omie ou vice-versa)
        for cliente_omie in clientes_omie:
            cliente_omie_lower = cliente_omie.lower().strip()
            
            # Se um contém o outro (com pelo menos 5 caracteres para evitar falsos positivos)
            if len(cliente_lower) >= 5 and len(cliente_omie_lower) >= 5:
                if cliente_lower in cliente_omie_lower or cliente_omie_lower in cliente_lower:
                    print(f"   📌 Match parcial: '{cliente_sugerido}' ≈ '{cliente_omie}'")
                    return True
        
        return False
    
    def _exibir_resultados(self, resultados):
        """
        Exibe resultados da conciliação
        """
        print(f"\n" + "=" * 60)
        print("📊 RESULTADOS DA CONCILIAÇÃO")
        print("=" * 60)
        
        total_ofx = resultados['total_ofx']
        total_omie = resultados['total_omie']
        matches = resultados['matches']
        ofx_nao_conciliadas = resultados['ofx_nao_conciliadas']
        omie_nao_conciliadas = resultados['omie_nao_conciliadas']
        
        taxa_conciliacao = (len(matches) / total_ofx * 100) if total_ofx > 0 else 0
        
        print(f"📄 Total transações OFX: {total_ofx}")
        print(f"🏦 Total movimentos Omie: {total_omie}")
        print(f"✅ Matches encontrados: {len(matches)}")
        print(f"📊 Taxa de conciliação: {taxa_conciliacao:.1f}%")
        print(f"❌ OFX não conciliadas: {len(ofx_nao_conciliadas)}")
        print(f"❓ Omie não conciliadas: {len(omie_nao_conciliadas)}")
        
        # Detalhes dos matches
        if matches:
            print(f"\n✅ MATCHES ENCONTRADOS:")
            for i, match in enumerate(matches[:5], 1):  # Mostrar primeiros 5
                ofx = match['ofx']
                omie = match['omie']
                print(f"{i}. {match['criterio'].upper()} - Confiança: {match['confianca']:.0%}")
                print(f"   OFX: {ofx.get('data')} | R$ {ofx.get('valor', 0):.2f} | {ofx.get('descricao', '')[:50]}")
                print(f"   Omie: {omie.get('data')} | R$ {omie.get('valor', 0):.2f} | {omie.get('descricao', '')[:50]}")
                print()
            
            if len(matches) > 5:
                print(f"   ... e mais {len(matches) - 5} matches")
        
        # OFX não conciliadas
        if ofx_nao_conciliadas:
            print(f"\n❌ TRANSAÇÕES OFX NÃO CONCILIADAS:")
            for i, ofx in enumerate(ofx_nao_conciliadas[:3], 1):  # Mostrar primeiras 3
                print(f"{i}. {ofx.get('data')} | R$ {ofx.get('valor', 0):.2f} | {ofx.get('descricao', '')[:50]}")
            
            if len(ofx_nao_conciliadas) > 3:
                print(f"   ... e mais {len(ofx_nao_conciliadas) - 3} transações")


def main():
    """Função principal para testes"""
    if len(sys.argv) < 3:
        print("Uso: python smart_reconciliation_extrato.py <arquivo_ofx> <conta_id>")
        print("Exemplo: python smart_reconciliation_extrato.py extrato.ofx 2103553430")
        return
    
    ofx_file = sys.argv[1]
    conta_id = sys.argv[2]
    
    if not os.path.exists(ofx_file):
        print(f"❌ Arquivo OFX não encontrado: {ofx_file}")
        return
    
    reconciliation = SmartReconciliationExtrato()
    resultados = reconciliation.conciliar(ofx_file, conta_id)
    
    if resultados:
        print("✅ Conciliação finalizada!")
    else:
        print("❌ Erro na conciliação")


if __name__ == "__main__":
    main()