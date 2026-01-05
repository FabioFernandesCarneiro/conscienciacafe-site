import csv
import requests
import io
from datetime import datetime
from typing import List, Dict, Any

class SheetImporter:
    def __init__(self, sheet_url: str):
        # Convert view URL to export URL if needed
        if '/edit' in sheet_url:
            self.csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv')
            self.csv_url = self.csv_url.replace('/edit', '/export?format=csv')
        else:
            self.csv_url = sheet_url

    def import_transactions(self) -> List[Dict[str, Any]]:
        """
        Import transactions from public Google Sheet CSV
        """
        try:
            response = requests.get(self.csv_url)
            response.raise_for_status()
            
            # Decode content
            content = response.content.decode('utf-8')
            
            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            
            transactions = []
            
            for row in reader:
                # Expected columns: Data, Descrição, Valor, Tipo
                if not row['Data'] or not row['Valor']:
                    continue
                    
                # Parse Date (DD/MM/YYYY)
                try:
                    date_obj = datetime.strptime(row['Data'], '%d/%m/%Y').date()
                except ValueError:
                    continue # Skip invalid dates
                
                # Parse Amount (Handle "1.234,56" or "1234.56" or "199,9")
                amount_str = row['Valor'].replace('.', '').replace(',', '.')
                try:
                    amount = float(amount_str)
                except ValueError:
                    continue
                    
                # Determine Type
                # If amount is negative, it's expense. If positive, revenue.
                # The sheet has 'Tipo' column (CRÉDITO/DÉBITO) but amount sign is safer if consistent
                t_type = 'revenue' if amount > 0 else 'expense'
                
                transactions.append({
                    'date': date_obj,
                    'description': row['Descrição'],
                    'amount': amount,
                    'type': t_type,
                    'source': 'caixinha_sheet'
                })
                
            return transactions
            
        except Exception as e:
            print(f"Error importing sheet: {e}")
            return []
