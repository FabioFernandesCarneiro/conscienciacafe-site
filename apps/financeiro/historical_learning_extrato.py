#!/usr/bin/env python3
"""
Sistema de aprendizado histórico usando API de Extrato - NOVA VERSÃO
Processa OFX históricos e extrai dados do extrato para treinar o ML
"""

import os
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from src.omie_client import OmieClient
from src.ml_categorizer import MLCategorizer
from simple_ofx_extractor import SimpleOFXExtractor

class HistoricalLearningExtrato:
    def __init__(self):
        load_dotenv()
        self.omie_client = OmieClient(
            app_key=os.getenv('OMIE_APP_KEY'),
            app_secret=os.getenv('OMIE_APP_SECRET')
        )
        self.ml_categorizer = MLCategorizer()
        self.ofx_extractor = SimpleOFXExtractor()
        
        self.processed_transactions = 0
        self.learned_transactions = 0
        self.errors = []
        
        print("🤖 Sistema de Aprendizado com API de Extrato inicializado")
        
    def reset_learning_database(self):
        """
        Reseta completamente o banco de dados de aprendizado
        """
        print("🗑️ Resetando banco de dados de aprendizado...")
        
        try:
            if os.path.exists(self.ml_categorizer.db_path):
                os.remove(self.ml_categorizer.db_path)
                print("   ✅ Banco de dados removido")
            
            if os.path.exists(self.ml_categorizer.model_path):
                os.remove(self.ml_categorizer.model_path)
                print("   ✅ Modelo removido")
            
            # Recriar estrutura
            self.ml_categorizer._init_database()
            print("   ✅ Nova estrutura criada")
            
        except Exception as e:
            print(f"   ❌ Erro ao resetar: {e}")
    
    def process_historical_ofx(self, ofx_path: str, conta_id: str) -> Dict[str, Any]:
        """
        Processa um arquivo OFX histórico usando API de Extrato
        """
        print(f"\n📚 Processando arquivo histórico: {os.path.basename(ofx_path)}")
        print(f"🏦 Conta ID: {conta_id}")
        
        if not os.path.exists(ofx_path):
            error = f"Arquivo não encontrado: {ofx_path}"
            self.errors.append(error)
            return {"status": "error", "message": error}
        
        try:
            # 1. Extrair período e transações do OFX
            print("📅 Extraindo dados do OFX...")
            data_inicio, data_fim, transacoes_ofx = self.ofx_extractor.extrair_periodo_e_transacoes(ofx_path)
            
            if not data_inicio or not data_fim or not transacoes_ofx:
                return {"status": "error", "message": "Não foi possível extrair dados do OFX"}
            
            print(f"   📊 Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
            print(f"   📊 {len(transacoes_ofx)} transações no OFX")
            
            # 2. Buscar movimentos na API de Extrato
            print("🔍 Buscando movimentos na API de Extrato...")
            movimentos_extrato = self._buscar_movimentos_extrato(conta_id, data_inicio, data_fim)
            
            if not movimentos_extrato:
                return {"status": "error", "message": "Nenhum movimento encontrado na API de Extrato"}
            
            print(f"   📊 {len(movimentos_extrato)} movimentos no extrato")
            
            # 3. Fazer matching entre OFX e extrato
            print("🔄 Fazendo matching entre OFX e extrato...")
            matches = self._fazer_matching(transacoes_ofx, movimentos_extrato)
            
            print(f"   ✅ {len(matches)} matches encontrados")
            
            # 4. Extrair dados de aprendizado dos matches
            print("📚 Extraindo dados de aprendizado...")
            learned_count = 0
            
            for i, match in enumerate(matches):
                try:
                    print(f"🔍 Processando match {i+1}/{len(matches)}")
                    
                    learning_data = self._extract_learning_data(match['ofx'], match['extrato'])
                    
                    if learning_data:
                        self._save_learning_data(learning_data)
                        learned_count += 1
                        print(f"   ✅ Aprendido: categoria='{learning_data['category'] or 'N/A'}', cliente='{learning_data['client_supplier'] or 'N/A'}'")
                    else:
                        print(f"   ⚠️ Dados insuficientes para aprendizado")
                        
                except Exception as e:
                    error_msg = f"Erro no match {i}: {str(e)}"
                    self.errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
            
            self.processed_transactions += len(matches)
            self.learned_transactions += learned_count
            
            return {
                "status": "success",
                "total_ofx_transactions": len(transacoes_ofx),
                "total_extrato_movements": len(movimentos_extrato),
                "matches_found": len(matches),
                "learned_transactions": learned_count,
                "learning_rate": (learned_count / len(matches) * 100) if matches else 0
            }
            
        except Exception as e:
            error = f"Erro ao processar arquivo {ofx_path}: {str(e)}"
            self.errors.append(error)
            return {"status": "error", "message": error}
    
    def _buscar_movimentos_extrato(self, conta_id: str, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """
        Busca movimentos usando a API de Extrato (mesmo método do smart_reconciliation_extrato.py)
        """
        try:
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
            print(f"   📦 {len(movimentos_raw)} movimentos brutos retornados")
            
            # Processar e filtrar movimentos
            movimentos_processados = []
            
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
                    if data_movimento_obj < data_inicio or data_movimento_obj > data_fim:
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
                    'categoria': movimento.get('cDesCategoria', ''),
                    'categoria_codigo': movimento.get('cCodCategoria', ''),
                    'documento': movimento.get('cNumero', ''),
                    'codigo_lancamento': movimento.get('nCodLancamento', ''),
                    'conciliado': movimento.get('cSituacao', '') == 'Conciliado',
                    'natureza': movimento.get('cNatureza', ''),
                    'tipo_documento': movimento.get('cTipoDocumento', ''),
                    'origem': movimento.get('cOrigem', ''),
                    'numero_documento_truncado': self._truncar_numero_documento(movimento.get('cNumero', '')),
                    'fonte': 'extrato_api'
                }
                
                movimentos_processados.append(movimento_processado)
            
            print(f"   ✅ {len(movimentos_processados)} movimentos válidos processados")
            return movimentos_processados
            
        except Exception as e:
            print(f"❌ Erro ao buscar movimentos na API de Extrato: {e}")
            return []
    
    def _truncar_numero_documento(self, numero_documento):
        """
        Trunca número do documento para 20 caracteres (mesmo método do smart_reconciliation_extrato.py)
        """
        if not numero_documento:
            return ""
        
        import re
        numero_limpo = re.sub(r'[^\w]', '', str(numero_documento))
        return numero_limpo[:20] if len(numero_limpo) > 20 else numero_limpo
    
    def _fazer_matching(self, transacoes_ofx: List[Dict], movimentos_extrato: List[Dict]) -> List[Dict]:
        """
        Faz matching entre transações OFX e movimentos do extrato (mesma lógica do smart_reconciliation_extrato.py)
        """
        matches = []
        extrato_nao_usados = movimentos_extrato.copy()
        
        for transacao_ofx in transacoes_ofx:
            match_encontrado = False
            
            for movimento_extrato in movimentos_extrato:
                if movimento_extrato in extrato_nao_usados:
                    
                    # Critério 1: Número do documento
                    if (transacao_ofx.get('numero_documento') and 
                        movimento_extrato.get('numero_documento_truncado') and
                        self._match_numero_documento(transacao_ofx, movimento_extrato)):
                        
                        matches.append({
                            'ofx': transacao_ofx,
                            'extrato': movimento_extrato,
                            'criterio': 'numero_documento',
                            'confianca': 0.95
                        })
                        extrato_nao_usados.remove(movimento_extrato)
                        match_encontrado = True
                        break
                    
                    # Critério 2: Valor e data próxima (±5 dias)
                    elif self._match_valor_data(transacao_ofx, movimento_extrato):
                        matches.append({
                            'ofx': transacao_ofx,
                            'extrato': movimento_extrato,
                            'criterio': 'valor_data',
                            'confianca': 0.85
                        })
                        extrato_nao_usados.remove(movimento_extrato)
                        match_encontrado = True
                        break
                    
                    # Critério 3: Valor exato e descrição parcial
                    elif self._match_valor_descricao(transacao_ofx, movimento_extrato):
                        matches.append({
                            'ofx': transacao_ofx,
                            'extrato': movimento_extrato,
                            'criterio': 'valor_descricao',
                            'confianca': 0.75
                        })
                        extrato_nao_usados.remove(movimento_extrato)
                        match_encontrado = True
                        break
        
        return matches
    
    def _match_numero_documento(self, transacao_ofx, movimento_extrato):
        """Verifica match por número do documento"""
        ofx_doc = self._truncar_numero_documento(transacao_ofx.get('numero_documento', ''))
        extrato_doc = movimento_extrato.get('numero_documento_truncado', '')
        
        if not ofx_doc or not extrato_doc:
            return False
        
        return ofx_doc == extrato_doc
    
    def _match_valor_data(self, transacao_ofx, movimento_extrato, tolerancia_dias=5):
        """Verifica match por valor e data próxima"""
        # Verificar valor
        valor_ofx = abs(float(transacao_ofx.get('valor', 0)))
        valor_extrato = abs(float(movimento_extrato.get('valor', 0)))
        
        tolerancia_valor = max(0.10, valor_ofx * 0.001)
        if abs(valor_ofx - valor_extrato) > tolerancia_valor:
            return False
        
        # Verificar data
        try:
            data_ofx = transacao_ofx.get('data_obj') or datetime.strptime(str(transacao_ofx.get('data')), '%Y-%m-%d').date()
            data_extrato = movimento_extrato.get('data_obj')
            
            if not data_extrato:
                return False
            
            diferenca_dias = abs((data_ofx - data_extrato).days)
            return diferenca_dias <= tolerancia_dias
            
        except Exception:
            return False
    
    def _match_valor_descricao(self, transacao_ofx, movimento_extrato):
        """Verifica match por valor exato e similaridade na descrição"""
        # Verificar valor
        valor_ofx = abs(float(transacao_ofx.get('valor', 0)))
        valor_extrato = abs(float(movimento_extrato.get('valor', 0)))
        
        if abs(valor_ofx - valor_extrato) > 0.05:
            return False
        
        # Verificar similaridade na descrição
        import re
        
        desc_ofx = str(transacao_ofx.get('descricao', '')).lower()
        desc_extrato = str(movimento_extrato.get('descricao', '')).lower()
        cliente_extrato = str(movimento_extrato.get('cliente', '')).lower()
        
        # Remover caracteres especiais
        desc_ofx = re.sub(r'[^\w\s]', ' ', desc_ofx)
        desc_extrato = re.sub(r'[^\w\s]', ' ', desc_extrato)
        cliente_extrato = re.sub(r'[^\w\s]', ' ', cliente_extrato)
        
        # Verificar palavras chave em comum
        palavras_ofx = set(word for word in desc_ofx.split() if len(word) > 3)
        palavras_extrato = set(word for word in desc_extrato.split() if len(word) > 3)
        palavras_cliente = set(word for word in cliente_extrato.split() if len(word) > 3)
        
        todas_palavras_extrato = palavras_extrato.union(palavras_cliente)
        palavras_comuns = palavras_ofx.intersection(todas_palavras_extrato)
        
        if len(palavras_comuns) >= 1:
            return True
        
        # Verificar se uma descrição contém a outra
        if (len(desc_ofx) > 5 and desc_ofx in desc_extrato) or \
           (len(desc_extrato) > 5 and desc_extrato in desc_ofx) or \
           (len(desc_ofx) > 5 and desc_ofx in cliente_extrato):
            return True
        
        return False
    
    def _extract_learning_data(self, transacao_ofx: Dict, movimento_extrato: Dict) -> Optional[Dict[str, Any]]:
        """
        Extrai dados de aprendizado do match entre OFX e extrato
        """
        try:
            # Verificar se temos categoria e/ou cliente válidos no extrato
            categoria_nome = movimento_extrato.get('categoria', '').strip()
            cliente_nome = movimento_extrato.get('cliente', '').strip()
            
            # Filtrar categorias e clientes inválidos
            categorias_invalidas = ['', 'Não Categorizado', 'Outros', 'N/A', 'null', 'None']
            clientes_invalidos = ['', 'SALDO ANTERIOR', 'SALDO INICIAL', 'N/A', 'null', 'None']
            
            if categoria_nome in categorias_invalidas:
                categoria_nome = None
                
            if cliente_nome in clientes_invalidos:
                cliente_nome = None
            
            # Se não temos nem categoria nem cliente útil, não vale a pena aprender
            if not categoria_nome and not cliente_nome:
                return None
            
            # Preparar descrição limpa para ML
            descricao = transacao_ofx.get('descricao', '')
            clean_description = self._clean_description_for_ml(descricao)
            
            learning_data = {
                'description': descricao,
                'clean_description': clean_description,
                'amount': abs(float(transacao_ofx.get('valor', 0))),
                'category': categoria_nome,
                'client_supplier': cliente_nome,
                'confidence': 1.0  # Máxima confiança para dados históricos reais do extrato
            }
            
            return learning_data
            
        except Exception as e:
            print(f"   ❌ Erro ao extrair dados: {e}")
            return None
    
    def _clean_description_for_ml(self, description):
        """Limpa descrição para uso no ML (mesmo método do smart_reconciliation_extrato.py)"""
        if not description:
            return ""
        
        import re
        clean = description.lower()
        clean = re.sub(r'[^\w\s]', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    
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
            print(f"   ❌ Erro ao salvar dados de aprendizado: {e}")
    
    def process_multiple_ofx_files(self, conta_configs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Processa múltiplos arquivos OFX com suas respectivas contas
        conta_configs: [{'ofx_file': 'path/file.ofx', 'conta_id': '123456'}, ...]
        """
        print(f"\n🎯 SISTEMA DE APRENDIZADO HISTÓRICO COM API DE EXTRATO")
        print(f"=" * 70)
        print(f"📂 Processando {len(conta_configs)} arquivos...")
        
        results = []
        
        for i, config in enumerate(conta_configs, 1):
            ofx_file = config['ofx_file']
            conta_id = config['conta_id']
            
            print(f"\n📄 [{i}/{len(conta_configs)}] {os.path.basename(ofx_file)} (conta: {conta_id})")
            
            if not os.path.exists(ofx_file):
                error = f"Arquivo não encontrado: {ofx_file}"
                results.append({
                    "file": os.path.basename(ofx_file),
                    "conta_id": conta_id,
                    "result": {"status": "error", "message": error}
                })
                continue
            
            result = self.process_historical_ofx(ofx_file, conta_id)
            results.append({
                "file": os.path.basename(ofx_file),
                "conta_id": conta_id,
                "result": result
            })
        
        # Resumo final
        self._print_final_summary(results)
        
        return {
            "status": "success",
            "files_processed": len(conta_configs),
            "total_transactions": self.processed_transactions,
            "learned_transactions": self.learned_transactions,
            "errors": len(self.errors),
            "results": results
        }
    
    def _print_final_summary(self, results: List[Dict]):
        """
        Imprime resumo final do processamento
        """
        print(f"\n{'='*70}")
        print(f"📊 RESUMO DO APRENDIZADO HISTÓRICO COM API DE EXTRATO")
        print(f"{'='*70}")
        
        total_matches = 0
        total_learned = 0
        
        for result in results:
            file_name = result['file']
            conta_id = result['conta_id']
            file_result = result['result']
            
            print(f"\n📄 {file_name} (conta: {conta_id}):")
            if file_result['status'] == 'success':
                matches = file_result['matches_found']
                learned = file_result['learned_transactions']
                learning_rate = file_result['learning_rate']
                
                print(f"   ✅ Matches: {matches}")
                print(f"   📚 Aprendidas: {learned}")
                print(f"   📈 Taxa de aprendizado: {learning_rate:.1f}%")
                
                total_matches += matches
                total_learned += learned
            else:
                print(f"   ❌ Erro: {file_result['message']}")
        
        print(f"\n🎯 TOTAIS GERAIS:")
        print(f"   📊 Total de matches: {total_matches}")
        print(f"   📚 Total aprendido: {total_learned}")
        print(f"   ❌ Erros: {len(self.errors)}")
        
        if total_matches > 0:
            learning_rate_geral = (total_learned / total_matches) * 100
            print(f"   📈 Taxa de aprendizado geral: {learning_rate_geral:.1f}%")
        
        # Estatísticas do ML após aprendizado
        ml_stats = self.ml_categorizer.get_learning_stats()
        print(f"\n🧠 ESTATÍSTICAS DO MODELO ML:")
        print(f"   📚 Total de exemplos: {ml_stats['total_transactions']}")
        print(f"   🏷️ Com categoria: {ml_stats['categorized']}")
        print(f"   👥 Com cliente/fornecedor: {ml_stats['with_client_supplier']}")
        print(f"   🤖 Modelo treinado: {'Sim' if ml_stats['model_trained'] else 'Não'}")
        
        if self.errors:
            print(f"\n❌ ERROS ({len(self.errors)}):")
            for error in self.errors[:5]:
                print(f"   - {error}")
            if len(self.errors) > 5:
                print(f"   ... e mais {len(self.errors) - 5} erros")
        
        print(f"\n{'='*70}")
        print(f"💡 PRÓXIMOS PASSOS:")
        print(f"   1. ✅ Sistema agora tem dados reais do extrato Omie")
        print(f"   2. 🎯 Categorização será muito mais precisa")
        print(f"   3. 🚀 Execute o reconciliador web para testar")
        print(f"{'='*70}")


def main():
    """
    Função principal para execução standalone
    """
    load_dotenv()
    
    print("🎯 SISTEMA DE APRENDIZADO HISTÓRICO COM API DE EXTRATO")
    print("=" * 70)
    
    try:
        learning_system = HistoricalLearningExtrato()
        print("✅ Sistema inicializado")
        
        # Opção de resetar dados
        print("\n⚠️ ATENÇÃO: Este sistema substituirá os dados de aprendizado atuais")
        print("   Os dados serão extraídos do extrato real do Omie (mais precisos)")
        
        reset_choice = input("\nResetar dados de aprendizado existentes? (S/n): ").lower()
        if reset_choice != 'n':
            learning_system.reset_learning_database()
        
        # Configuração de arquivos e contas
        print("\n📂 CONFIGURAÇÃO DE ARQUIVOS:")
        
        # Arquivos de exemplo disponíveis
        arquivos_exemplo = [
            {"ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/NU_826344542_12JUL2025_13JUL2025.ofx", "conta_id": "2103553430"},
            {"ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/NU_826344542_01JUL2025_02JUL2025.ofx", "conta_id": "2103553430"},
            {"ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/NU_826344542_01MAI2025_14AGO2025.ofx", "conta_id": "2103553430"},
            {"ofx_file": "/Users/fabiocarneiro/Development/Financeiro/Consciencia_Cafe/Nubank_2025-03-22 (1).ofx", "conta_id": "2103553430"}
        ]
        
        print("Opções:")
        print("1. Processar arquivos de exemplo (Nubank)")
        print("2. Configurar arquivo específico")
        print("3. Configurar múltiplos arquivos manualmente")
        
        choice = input("\nEscolha (1-3): ").strip()
        
        if choice == "1":
            # Filtrar apenas arquivos que existem
            arquivos_validos = [
                config for config in arquivos_exemplo 
                if os.path.exists(config['ofx_file'])
            ]
            
            if arquivos_validos:
                print(f"\n📋 {len(arquivos_validos)} arquivo(s) de exemplo encontrado(s):")
                for config in arquivos_validos:
                    print(f"   ✅ {os.path.basename(config['ofx_file'])}")
                
                result = learning_system.process_multiple_ofx_files(arquivos_validos)
                
                if result['status'] == 'success':
                    print(f"\n🎉 Processamento concluído com sucesso!")
                else:
                    print(f"\n❌ Erro no processamento: {result.get('message', 'Erro desconhecido')}")
            else:
                print("\n❌ Nenhum arquivo de exemplo encontrado")
                
        elif choice == "2":
            # Arquivo específico
            ofx_path = input("Caminho do arquivo OFX: ").strip()
            conta_id = input("ID da conta no Omie: ").strip()
            
            result = learning_system.process_historical_ofx(ofx_path, conta_id)
            
            if result['status'] == 'success':
                print(f"\n✅ Processamento concluído!")
                print(f"   📚 {result['learned_transactions']}/{result['matches_found']} transações aprendidas")
            else:
                print(f"\n❌ Erro: {result['message']}")
                
        elif choice == "3":
            # Múltiplos arquivos manuais
            configs = []
            
            print("\nDigite os arquivos (deixe em branco para finalizar):")
            while True:
                ofx_path = input(f"Arquivo OFX #{len(configs)+1}: ").strip()
                if not ofx_path:
                    break
                
                conta_id = input(f"ID da conta para este arquivo: ").strip()
                if not conta_id:
                    print("ID da conta é obrigatório!")
                    continue
                
                configs.append({"ofx_file": ofx_path, "conta_id": conta_id})
            
            if configs:
                result = learning_system.process_multiple_ofx_files(configs)
                
                if result['status'] == 'success':
                    print(f"\n🎉 Processamento de {result['files_processed']} arquivo(s) concluído!")
                else:
                    print(f"\n❌ Erro: {result['message']}")
            else:
                print("❌ Nenhum arquivo configurado")
        else:
            print("❌ Opção inválida")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()