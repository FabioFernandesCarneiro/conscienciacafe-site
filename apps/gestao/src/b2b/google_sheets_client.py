#!/usr/bin/env python3
"""
Cliente Google Sheets para dados B2B
Integração com planilha de controle de vendas B2B
"""

import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class GoogleSheetsClient:
    def __init__(self, credentials_file: str = None, spreadsheet_key: str = None):
        self.credentials_file = credentials_file or os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        self.spreadsheet_key = spreadsheet_key or os.getenv('GOOGLE_SPREADSHEET_KEY')

        # Para desenvolvimento, usar dados mock se não tiver credenciais
        has_credentials = self.credentials_file and self.spreadsheet_key and os.path.exists(self.credentials_file or "")
        self.use_mock_data = not has_credentials

        if self.use_mock_data:
            print("⚠️ Usando dados mock para desenvolvimento - Configure credenciais Google Sheets para dados reais")
        else:
            print("✅ Google Sheets configurado - usando dados reais")
    
    def get_sales_data(self, sheet_name: str = 'Vendas') -> List[Dict[str, Any]]:
        """
        Obtém dados de vendas da planilha Google Sheets
        
        Returns:
            Lista de vendas no formato: [{'cliente': str, 'data': str, 'valor': float, 'produto': str}]
        """
        if self.use_mock_data:
            return self._get_mock_sales_data()
        
        try:
            # Implementar integração real com Google Sheets API
            import gspread
            from google.oauth2.service_account import Credentials
            
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # Carregar credenciais do arquivo
            if not self.credentials_file or not os.path.exists(self.credentials_file):
                print(f"❌ Arquivo de credenciais não encontrado: {self.credentials_file}")
                return self._get_mock_sales_data()

            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes)
            print(f"✅ Credenciais Google carregadas do arquivo: {self.credentials_file}")

            client = gspread.authorize(credentials)
            
            # Abrir planilha
            sheet = client.open_by_key(self.spreadsheet_key)
            worksheet = sheet.worksheet(sheet_name)
            
            # Obter dados da planilha de forma mais robusta
            # Primeiro, obter apenas as primeiras 5 colunas para evitar problemas com vazias
            all_values = worksheet.get_all_values()
            
            if len(all_values) < 2:
                print("⚠️ Planilha vazia ou sem dados")
                return self._get_mock_sales_data()
            
            # Cabeçalhos (primeira linha)
            headers = all_values[0][:5]  # Primeiras 5 colunas
            
            # Dados (demais linhas)
            records = []
            for row in all_values[1:]:  # Pular cabeçalho
                if len(row) >= 5 and any(cell.strip() for cell in row[:5]):  # Linha não vazia
                    record = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            record[header] = row[i]
                    records.append(record)
            
            print(f"📊 Conectado ao Google Sheets! {len(records)} registros encontrados")
            
            return self._normalize_sales_data(records)
            
        except Exception as e:
            print(f"❌ Erro ao acessar Google Sheets: {e}")
            return self._get_mock_sales_data()
    
    def _get_mock_sales_data(self) -> List[Dict[str, Any]]:
        """
        Dados mock realistas para desenvolvimento e testes
        Simula dados de vendas B2B dos últimos 6 meses
        """
        import random
        from datetime import datetime, timedelta
        
        clientes_b2b = [
            'Mercado São João',
            'Supermercados Família',
            'Padaria Central',
            'Café & Cia Distribuidora',
            'Empório Gourmet',
            'RestauranteCorp',
            'Hotel Plaza Food',
            'Buffet Eventos',
            'Cafeteria Universitária',
            'Lanchonete Popular',
            'Bar do João',
            'Restaurante Italiano',
            'Fast Food Center',
            'Catering Solutions',
            'Food Truck Gourmet'
        ]
        
        produtos = [
            'Café Especial 1kg',
            'Café Premium 500g', 
            'Café Tradicional 500g',
            'Café Orgânico 1kg',
            'Café Expresso 250g',
            'Café Gourmet 1kg'
        ]
        
        vendas_mock = []
        base_date = datetime.now() - timedelta(days=180)  # 6 meses atrás
        
        # Gerar vendas aleatórias
        for i in range(250):  # 250 vendas nos últimos 6 meses
            cliente = random.choice(clientes_b2b)
            produto = random.choice(produtos)
            
            # Data aleatória nos últimos 6 meses
            random_days = random.randint(0, 180)
            data_venda = base_date + timedelta(days=random_days)
            
            # Valor baseado no produto
            valores_base = {
                'Café Especial 1kg': 35.00,
                'Café Premium 500g': 22.00,
                'Café Tradicional 500g': 18.00,
                'Café Orgânico 1kg': 42.00,
                'Café Expresso 250g': 15.00,
                'Café Gourmet 1kg': 45.00
            }
            
            valor_base = valores_base[produto]
            quantidade = random.randint(2, 20)  # Quantidade B2B
            valor_total = valor_base * quantidade
            
            # Variação de preço ±10%
            variacao = random.uniform(0.9, 1.1)
            valor_final = round(valor_total * variacao, 2)
            
            vendas_mock.append({
                'cliente': cliente,
                'data': data_venda.strftime('%Y-%m-%d'),
                'produto': produto,
                'quantidade': quantidade,
                'valor_unitario': valor_base,
                'valor': valor_final,
                'observacoes': f'Venda B2B - {produto}'
            })
        
        # Simular alguns clientes inativos (sem compras recentes)
        clientes_ativos = set([v['cliente'] for v in vendas_mock 
                              if datetime.strptime(v['data'], '%Y-%m-%d') > datetime.now() - timedelta(days=30)])
        
        print(f"📊 Dados mock gerados: {len(vendas_mock)} vendas, {len(clientes_ativos)} clientes ativos no mês")
        
        return vendas_mock
    
    def _normalize_sales_data(self, raw_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza dados da planilha para formato padrão
        Mapeia os campos reais: País, Cliente, Mês, Qtde (Kg), Valor
        """
        normalized = []
        
        for row in raw_data:
            try:
                # Validar se tem dados essenciais
                cliente = row.get('Cliente', '').strip()
                valor_str = row.get('Valor', '').strip()
                mes = row.get('Mês', '').strip()
                
                if not cliente or not valor_str or not mes:
                    continue  # Pular linhas sem dados essenciais
                
                # Processar valor (remover símbolos de moeda se houver)
                valor_limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
                valor = float(valor_limpo) if valor_limpo else 0
                
                # Processar quantidade (formato brasileiro com vírgula)
                qtde_str = row.get('Qtde (Kg)', '').strip()
                qtde_limpa = qtde_str.replace(',', '.') if qtde_str else '1'
                quantidade = float(qtde_limpa) if qtde_limpa else 1
                
                # Gerar data a partir do mês
                data = self._parse_month_to_date(mes)
                
                normalized.append({
                    'cliente': cliente,
                    'data': data,
                    'produto': 'Café',  # Default
                    'valor': valor,
                    'quantidade': quantidade,
                    'observacoes': f"Venda {mes} - {row.get('País', 'Brasil')}"
                })
                
            except (ValueError, TypeError) as e:
                print(f"⚠️ Erro ao processar linha: {row} - {e}")
                continue
        
        return normalized
    
    def _parse_month_to_date(self, month_str: str) -> str:
        """
        Converte strings de mês/ano para data YYYY-MM-DD
        Ex: "08/2025", "01/24", "12/2024" -> "2025-08-15"
        """
        if not month_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            month_str = month_str.strip()
            
            # Formato "MM/YYYY" ou "MM/YY"
            if '/' in month_str:
                parts = month_str.split('/')
                if len(parts) == 2:
                    month_part = parts[0].strip().zfill(2)  # Garantir 2 dígitos
                    year_part = parts[1].strip()
                    
                    # Converter ano de 2 dígitos para 4
                    if len(year_part) == 2:
                        # Se for > 50, assume século passado, senão atual
                        year_int = int(year_part)
                        if year_int > 50:
                            year = '19' + year_part
                        else:
                            year = '20' + year_part
                    else:
                        year = year_part
                    
                    # Validar mês
                    month_int = int(month_part)
                    if 1 <= month_int <= 12:
                        return f"{year}-{month_part}-15"  # Dia 15 como padrão
            
            # Formato "YYYY-MM" 
            if '-' in month_str and len(month_str) == 7:
                return f"{month_str}-15"
            
            # Se não conseguir parse, usar data atual
            print(f"⚠️ Formato de data não reconhecido: '{month_str}', usando data atual")
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception as e:
            print(f"⚠️ Erro ao processar data '{month_str}': {e}")
            return datetime.now().strftime('%Y-%m-%d')
    
    def _parse_date(self, date_str: str) -> str:
        """
        Converte diferentes formatos de data para YYYY-MM-DD
        """
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        # Tentar diferentes formatos de data
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%m/%d/%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(date_str), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Se não conseguir parse, usar data atual
        print(f"⚠️ Formato de data não reconhecido: {date_str}")
        return datetime.now().strftime('%Y-%m-%d')

# Funções de configuração para facilitar setup
def setup_google_sheets_credentials():
    """
    Guia para configurar credenciais Google Sheets
    """
    print("""
🔧 CONFIGURAÇÃO GOOGLE SHEETS API

Para conectar com sua planilha real, siga os passos:

1. Acesse Google Cloud Console: https://console.cloud.google.com/
2. Crie um novo projeto ou use existente
3. Ative a Google Sheets API
4. Crie credenciais (Service Account)
5. Baixe o arquivo JSON de credenciais
6. Compartilhe sua planilha com o email do service account

7. Configure as variáveis no .env:
   GOOGLE_CREDENTIALS_FILE=/caminho/para/credentials.json
   GOOGLE_SPREADSHEET_KEY=sua_planilha_key_aqui

8. Instale dependências:
   pip install gspread google-auth-oauthlib google-auth-httplib2

Enquanto isso, o sistema funciona com dados mock para desenvolvimento!
    """)

if __name__ == "__main__":
    # Teste da integração
    client = GoogleSheetsClient()
    sales_data = client.get_sales_data()
    print(f"✅ {len(sales_data)} vendas carregadas")
    
    if sales_data:
        print("📊 Exemplo de dados:")
        for i, venda in enumerate(sales_data[:3]):
            print(f"   {i+1}. {venda['cliente']} - R$ {venda['valor']:.2f} - {venda['data']}")