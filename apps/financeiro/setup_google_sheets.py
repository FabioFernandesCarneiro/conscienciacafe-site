#!/usr/bin/env python3
"""
Script de configuração do Google Sheets API
"""

import os
from pathlib import Path

def setup_google_sheets():
    print("""
🔧 CONFIGURAÇÃO GOOGLE SHEETS API PARA MAC

Para conectar com sua planilha real, siga os passos:

1. 🌐 Acesse Google Cloud Console: 
   https://console.cloud.google.com/

2. 📁 Crie um novo projeto ou use existente
   
3. ⚡ Ative a Google Sheets API:
   - Vá em "APIs & Services" > "Library"
   - Procure por "Google Sheets API"
   - Clique em "Enable"

4. 🔑 Crie credenciais (Service Account):
   - Vá em "APIs & Services" > "Credentials"
   - Clique em "Create Credentials" > "Service Account"
   - Dê um nome (ex: "consciencia-cafe-sheets")
   - Baixe o arquivo JSON de credenciais

5. 📋 Compartilhe sua planilha:
   - Na sua planilha Google Sheets
   - Clique em "Compartilhar"
   - Adicione o EMAIL do service account (está no arquivo JSON)
   - Dê permissão de "Editor"

6. 🔧 Configure as variáveis de ambiente:
""")

    # Verificar se existe .env
    env_file = Path(".env")
    
    if env_file.exists():
        print("   ✅ Arquivo .env já existe")
        with open(env_file, "r") as f:
            content = f.read()
            
        if "GOOGLE_CREDENTIALS_FILE" in content and "GOOGLE_SPREADSHEET_KEY" in content:
            print("   ✅ Variáveis Google Sheets já configuradas")
        else:
            print("   ⚠️  Adicione estas linhas ao seu arquivo .env:")
            print_env_template()
    else:
        print("   📝 Crie um arquivo .env com estas linhas:")
        print_env_template()
        
        # Criar arquivo .env básico
        with open(env_file, "w") as f:
            f.write("""# Configurações Omie ERP
OMIE_APP_KEY=your_omie_app_key_here
OMIE_APP_SECRET=your_omie_app_secret_here

# Configurações Google Sheets
GOOGLE_CREDENTIALS_FILE=/caminho/para/sua/credentials.json
GOOGLE_SPREADSHEET_KEY=1qCYWQuFeDVOPweeblQsutuVahicZXpoJa14mooGoFEg

# Flask
FLASK_SECRET_KEY=your_secret_key_here
""")
        print("   ✅ Arquivo .env criado!")

    print("""
7. 🧪 Testar a conexão:
   python3 setup_google_sheets.py --test

💡 DICAS IMPORTANTES:
   - O arquivo credentials.json deve estar no projeto
   - O GOOGLE_SPREADSHEET_KEY é o ID da planilha (parte da URL)
   - Exemplo de URL: https://docs.google.com/spreadsheets/d/[ID_AQUI]/edit
   
🔄 Enquanto não configurar, o sistema usa dados mock para desenvolvimento!
""")

def print_env_template():
    print("""
   GOOGLE_CREDENTIALS_FILE=/Users/seu_usuario/caminho/para/credentials.json
   GOOGLE_SPREADSHEET_KEY=1qCYWQuFeDVOPweeblQsutuVahicZXpoJa14mooGoFEg
   """)

def test_connection():
    """Testa a conexão com Google Sheets"""
    try:
        from src.b2b.google_sheets_client import GoogleSheetsClient
        
        print("🧪 Testando conexão com Google Sheets...")
        
        client = GoogleSheetsClient()
        
        if client.use_mock_data:
            print("⚠️  Usando dados mock - Configure as credenciais primeiro")
        else:
            print("🔄 Tentando acessar planilha...")
            data = client.get_sales_data()
            
            if data:
                print(f"✅ Sucesso! {len(data)} registros encontrados")
                print("📊 Exemplo de dados:")
                for i, record in enumerate(data[:3]):
                    print(f"   {i+1}. {record.get('cliente', 'N/A')} - R$ {record.get('valor', 0):.2f}")
            else:
                print("❌ Nenhum dado encontrado na planilha")
                
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print("💡 Verifique as credenciais e permissões da planilha")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_connection()
    else:
        setup_google_sheets()