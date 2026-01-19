#!/usr/bin/env python3
"""
Descobrir IDs corretos das contas no Omie
"""

import os
from dotenv import load_dotenv
from src.omie_client import OmieClient

def find_accounts():
    """Busca todas as contas disponíveis no Omie"""
    load_dotenv()

    omie = OmieClient(
        app_key=os.getenv('OMIE_APP_KEY'),
        app_secret=os.getenv('OMIE_APP_SECRET')
    )

    print("🔍 Buscando contas disponíveis no Omie...")

    try:
        # Buscar contas correntes
        result = omie.omie._chamar_api(
            call='ListarContaCorrente',
            endpoint='geral/contacorrente/',
            param={}
        )

        print(f"📊 Resultado: {result}")

        if result and 'ListarContaCorrente' in result:
            accounts = result['ListarContaCorrente']
            print(f"🏦 Encontradas {len(accounts)} contas:")

            for account in accounts:
                print(f"  ID: {account.get('nCodCC', 'N/A')} | Nome: {account.get('cNome', 'N/A')}")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    find_accounts()