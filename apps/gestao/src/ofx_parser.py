"""
Parser de arquivos OFX para extrair transações bancárias
"""

import ofxparse
from typing import List, Dict, Any

class OFXParser:
    def __init__(self, ofx_file_path: str):
        self.ofx_file_path = ofx_file_path
        
    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse do arquivo OFX e retorna lista de transações
        """
        transactions = []
        
        try:
            with open(self.ofx_file_path, 'r', encoding='latin-1') as file:
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
                            'bank_id': account.routing_number,
                        }
                        
                        transactions.append(trans_data)
                        
        except Exception as e:
            print(f"Erro ao processar arquivo OFX: {e}")
            raise
            
        return transactions