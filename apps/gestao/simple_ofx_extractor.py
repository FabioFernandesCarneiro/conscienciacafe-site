#!/usr/bin/env python3
"""
Extrator simples de dados OFX sem interação
"""

import ofxparse
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional

class SimpleOFXExtractor:
    @staticmethod
    def extrair_periodo_e_transacoes(ofx_file_path: str) -> Tuple[Optional[date], Optional[date], List[Dict]]:
        """
        Extrai período e transações do arquivo OFX sem interação
        Retorna: (data_inicio, data_fim, transacoes)
        """
        try:
            with open(ofx_file_path, 'r', encoding='latin-1') as file:
                ofx_data = ofxparse.OfxParser.parse(file)
                
                transacoes = []
                datas = []
                
                # Processar conta
                if hasattr(ofx_data, 'account') and ofx_data.account:
                    account = ofx_data.account
                    
                    # Processar transações
                    for transaction in account.statement.transactions:
                        # Extrair dados da transação
                        data_transacao = transaction.date.date() if hasattr(transaction.date, 'date') else transaction.date
                        valor = float(transaction.amount)
                        
                        transacao_data = {
                            'data': data_transacao.strftime('%Y-%m-%d'),
                            'data_obj': data_transacao,
                            'valor': abs(valor),
                            'valor_original': valor,
                            'tipo': 'Crédito' if valor > 0 else 'Débito',
                            'descricao': transaction.memo or transaction.payee or 'Transação sem descrição',
                            'numero_documento': getattr(transaction, 'checknum', '') or getattr(transaction, 'fitid', ''),
                            'fonte': 'ofx'
                        }
                        
                        transacoes.append(transacao_data)
                        datas.append(data_transacao)
                
                # Calcular período
                if datas:
                    data_inicio = min(datas)
                    data_fim = max(datas)
                    return data_inicio, data_fim, transacoes
                else:
                    return None, None, []
                    
        except Exception as e:
            print(f"Erro ao processar OFX: {e}")
            return None, None, []