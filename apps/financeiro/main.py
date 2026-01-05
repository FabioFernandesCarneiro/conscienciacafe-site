#!/usr/bin/env python3
"""
Sistema Inteligente de Conciliação Bancária
Integração com Omie ERP para automatizar conciliação bancária com aprendizado de máquina
"""

import os
from dotenv import load_dotenv
from src.ofx_parser import OFXParser
from src.omie_client import OmieClient
from src.reconciliation_engine import ReconciliationEngine
from src.ml_categorizer import MLCategorizer
from src.ofx_detector import comprehensive_ofx_analysis

def main():
    load_dotenv()
    
    # Inicializar componentes
    omie_client = OmieClient(
        app_key=os.getenv('OMIE_APP_KEY'),
        app_secret=os.getenv('OMIE_APP_SECRET')
    )
    
    ml_categorizer = MLCategorizer()
    reconciliation_engine = ReconciliationEngine(omie_client, ml_categorizer)
    
    # Solicitar arquivo OFX
    ofx_file = input("Caminho do arquivo OFX: ")
    
    if not os.path.exists(ofx_file):
        print("Arquivo OFX não encontrado!")
        return
    
    # 🔍 DETECTAR TIPO DE CONTA AUTOMATICAMENTE
    print("\n🔍 ANALISANDO ARQUIVO OFX...")
    ofx_info = comprehensive_ofx_analysis(ofx_file)
    
    print(f"📄 Arquivo: {ofx_info['filename']}")
    print(f"🏦 Tipo detectado: {ofx_info['detected_type']}")
    print(f"📋 Descrição: {ofx_info['description']}")
    print(f"🆔 ID Omie: {ofx_info['omie_account_id']}")
    print(f"🔗 ID da conta: {ofx_info['account_id']}")
    print(f"✅ Validação: {ofx_info['validation']}")
    print(f"🎯 Confiança: {ofx_info['confidence']}")
    
    # Confirmar ou permitir alteração
    if ofx_info['validation'] == 'inconsistent':
        print("\n⚠️ INCONSISTÊNCIA DETECTADA!")
        print(f"   Cabeçalho indica: {ofx_info['detected_type']}")
        print(f"   Nome do arquivo indica: {ofx_info['filename_pattern']}")
        
        choice = input("\nContinuar mesmo assim? (s/N): ").lower()
        if choice != 's':
            print("Operação cancelada.")
            return
    
    # Configurar cliente Omie com a conta correta
    print(f"\n🔧 CONFIGURANDO CONTA: ID {ofx_info['omie_account_id']}")
    omie_client.set_account_id(ofx_info['omie_account_id'])
    
    # Processar transações
    parser = OFXParser(ofx_file)
    transactions = parser.parse()
    
    print(f"\n🚀 PROCESSANDO {len(transactions)} TRANSAÇÕES...")
    reconciliation_engine.process_transactions(transactions)

if __name__ == "__main__":
    main()