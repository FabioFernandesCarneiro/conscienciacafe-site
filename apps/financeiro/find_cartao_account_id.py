#!/usr/bin/env python3
"""
Encontrar o ID correto da conta do cartão baseado nos lançamentos conciliados
"""

import os
from dotenv import load_dotenv
from src.omie_client import OmieClient
import ofxparse

def find_cartao_account_id():
    """Encontra o ID correto da conta do cartão"""
    load_dotenv()
    
    print("🔍 DESCOBRINDO ID DA CONTA DO CARTÃO")
    print("=" * 50)
    
    omie_client = OmieClient(
        app_key=os.getenv('OMIE_APP_KEY'),
        app_secret=os.getenv('OMIE_APP_SECRET')
    )
    
    # IDs truncados da screenshot para procurar
    target_docs = [
        "67d487ce-0d78-44f9-9",  # Primeiro da screenshot
        "67002eb5-fda1-473d-a",  # Segundo da screenshot  
        "678a9d46-4fa1-40bd-a",  # Terceiro da screenshot
        "669c0666-320e-4b8a-9",  # Quarto da screenshot
        "67d31e9e-b545-4266-a"   # Quinto da screenshot
    ]
    
    print(f"🎯 Procurando pelos documentos: {target_docs[:3]}...")
    
    # Buscar em lançamentos de conta corrente sem filtro de conta
    print(f"\n🏦 BUSCANDO EM LANÇAMENTOS DE CONTA CORRENTE:")
    print("-" * 50)
    
    try:
        result = omie_client.omie.listar_lanc_c_c(
            nPagina=1,
            nRegPorPagina=100,
            dtPagInicial="01/03/2025",
            dtPagFinal="31/03/2025"
        )
        
        if isinstance(result, dict) and 'listaLancamentos' in result:
            lancamentos = result['listaLancamentos']
            print(f"✅ {len(lancamentos)} lançamentos encontrados em março")
            
            matches = {}  # conta_id -> número de matches
            
            for lanc in lancamentos:
                cabecalho = lanc.get('cabecalho', {})
                num_doc = cabecalho.get('cNumDocumento', '')
                conta_id = str(cabecalho.get('nCodCC', ''))
                valor = abs(float(cabecalho.get('nValorLanc', 0)))
                data = cabecalho.get('dDtLanc', '')
                
                # Verificar se é um dos documentos da screenshot
                for target_doc in target_docs:
                    if num_doc == target_doc:
                        if conta_id not in matches:
                            matches[conta_id] = []
                        
                        matches[conta_id].append({
                            'doc': num_doc,
                            'valor': valor,
                            'data': data
                        })
                        
                        print(f"✅ MATCH encontrado!")
                        print(f"   Conta ID: {conta_id}")
                        print(f"   Documento: {num_doc}")
                        print(f"   Valor: R$ {valor:.2f}")
                        print(f"   Data: {data}")
                        print()
                        break
            
            # Mostrar resumo
            if matches:
                print(f"📊 CONTAS COM MATCHES:")
                for conta_id, lista_matches in matches.items():
                    print(f"   Conta {conta_id}: {len(lista_matches)} matches")
                
                # Identificar a conta com mais matches
                best_account = max(matches.keys(), key=lambda x: len(matches[x]))
                print(f"\n🎯 CONTA CORRETA DO CARTÃO: {best_account}")
                print(f"   (Teve {len(matches[best_account])} matches dos {len(target_docs)} procurados)")
                
                # Verificar se é diferente do mapeamento atual
                current_mapping = 2103553431  # ID atual no código
                if best_account != str(current_mapping):
                    print(f"\n🔧 CORREÇÃO NECESSÁRIA:")
                    print(f"   Atual: 9 -> {current_mapping}")
                    print(f"   Correto: 9 -> {best_account}")
                else:
                    print(f"\n✅ Mapeamento já está correto!")
            else:
                print(f"❌ Nenhum match encontrado com os documentos da screenshot")
                
                # Debug: mostrar algumas entradas
                print(f"\n🔍 AMOSTRAS DOS DOCUMENTOS ENCONTRADOS:")
                for i, lanc in enumerate(lancamentos[:5]):
                    cabecalho = lanc.get('cabecalho', {})
                    num_doc = cabecalho.get('cNumDocumento', '')
                    conta_id = cabecalho.get('nCodCC', '')
                    print(f"   {i+1}. Conta {conta_id}: '{num_doc}'")
        else:
            print(f"❌ Erro na consulta")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print(f"\n" + "=" * 50)

if __name__ == "__main__":
    find_cartao_account_id()