#!/usr/bin/env python3
"""
Encontrar lançamentos com documentos preenchidos
"""

import os
from dotenv import load_dotenv
from src.omie_client import OmieClient

def find_docs_populated():
    """Encontra lançamentos com documentos preenchidos"""
    load_dotenv()
    
    print("🔍 BUSCANDO DOCUMENTOS PREENCHIDOS")
    print("=" * 50)
    
    omie_client = OmieClient(
        app_key=os.getenv('OMIE_APP_KEY'),
        app_secret=os.getenv('OMIE_APP_SECRET')
    )
    
    try:
        # Buscar páginas até encontrar documentos
        for pagina in range(1, 6):  # Buscar nas primeiras 5 páginas
            print(f"\n📄 PÁGINA {pagina}:")
            
            result = omie_client.omie.listar_lanc_c_c(
                nPagina=pagina,
                nRegPorPagina=100,
                dtPagInicial="01/03/2025",
                dtPagFinal="31/03/2025"
            )
            
            if isinstance(result, dict) and 'listaLancamentos' in result:
                lancamentos = result['listaLancamentos']
                
                if not lancamentos:
                    print("   ❌ Sem lançamentos")
                    break
                
                docs_found = 0
                contas_com_docs = set()
                
                for lanc in lancamentos:
                    cabecalho = lanc.get('cabecalho', {})
                    num_doc = cabecalho.get('cNumDocumento', '').strip()
                    conta_id = str(cabecalho.get('nCodCC', ''))
                    valor = abs(float(cabecalho.get('nValorLanc', 0)))
                    data = cabecalho.get('dDtLanc', '')
                    
                    if num_doc:  # Se tem documento preenchido
                        docs_found += 1
                        contas_com_docs.add(conta_id)
                        
                        if docs_found <= 10:  # Mostrar apenas os primeiros 10
                            print(f"   {docs_found:2d}. Conta {conta_id} | {data} | R$ {valor:8.2f}")
                            print(f"       📄 Documento: '{num_doc}'")
                
                print(f"   📊 Total com documentos: {docs_found}/{len(lancamentos)}")
                print(f"   🏦 Contas com documentos: {sorted(contas_com_docs)}")
                
                if docs_found > 0:
                    print(f"\n✅ Encontrados lançamentos com documentos!")
                    
                    # Se encontramos documentos, vamos procurar pelos específicos da screenshot
                    target_docs = [
                        "67d487ce-0d78-44f9-9",
                        "67002eb5-fda1-473d-a", 
                        "678a9d46-4fa1-40bd-a"
                    ]
                    
                    print(f"\n🎯 Procurando documentos específicos da screenshot:")
                    matches = 0
                    for lanc in lancamentos:
                        cabecalho = lanc.get('cabecalho', {})
                        num_doc = cabecalho.get('cNumDocumento', '').strip()
                        conta_id = str(cabecalho.get('nCodCC', ''))
                        
                        if num_doc in target_docs:
                            matches += 1
                            print(f"   ✅ MATCH {matches}: Conta {conta_id} - Doc: {num_doc}")
                    
                    if matches == 0:
                        print(f"   ❌ Nenhum dos documentos da screenshot encontrado nesta página")
                    
                if len(lancamentos) < 100:  # Última página
                    break
            else:
                print(f"   ❌ Erro na consulta")
                break
    
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Tentar buscar em período mais amplo
    print(f"\n🔍 BUSCANDO PERÍODO MAIS AMPLO (janeiro-abril 2025):")
    print("-" * 50)
    
    try:
        result = omie_client.omie.listar_lanc_c_c(
            nPagina=1,
            nRegPorPagina=100,
            dtPagInicial="01/01/2025",
            dtPagFinal="30/04/2025"
        )
        
        if isinstance(result, dict) and 'listaLancamentos' in result:
            lancamentos = result['listaLancamentos']
            
            target_docs = [
                "67d487ce-0d78-44f9-9",
                "67002eb5-fda1-473d-a",
                "678a9d46-4fa1-40bd-a"
            ]
            
            matches = 0
            for lanc in lancamentos:
                cabecalho = lanc.get('cabecalho', {})
                num_doc = cabecalho.get('cNumDocumento', '').strip()
                conta_id = str(cabecalho.get('nCodCC', ''))
                valor = abs(float(cabecalho.get('nValorLanc', 0)))
                data = cabecalho.get('dDtLanc', '')
                
                if num_doc in target_docs:
                    matches += 1
                    print(f"✅ MATCH {matches}: Conta {conta_id}")
                    print(f"   Documento: {num_doc}")
                    print(f"   Data: {data} | Valor: R$ {valor:.2f}")
                    print()
            
            if matches > 0:
                print(f"🎉 ENCONTRADOS {matches} MATCHES EM PERÍODO AMPLO!")
            else:
                print(f"❌ Ainda não encontrou os documentos da screenshot")
                
    except Exception as e:
        print(f"❌ Erro período amplo: {e}")
    
    print(f"\n" + "=" * 50)

if __name__ == "__main__":
    find_docs_populated()