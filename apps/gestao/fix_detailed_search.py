#!/usr/bin/env python3
"""
Correção para busca detalhada usando consulta específica
Para obter os valores reais dos campos cNumDoc nos detalhes
"""

import os
from dotenv import load_dotenv
from src.omie_client import OmieClient

def fix_detailed_search():
    """Testa consulta específica para obter número do documento"""
    load_dotenv()
    
    print("🔧 CORREÇÃO - BUSCA DETALHADA COM CONSULTA ESPECÍFICA")
    print("=" * 70)
    
    omie_client = OmieClient(
        app_key=os.getenv('OMIE_APP_KEY'),
        app_secret=os.getenv('OMIE_APP_SECRET')
    )
    omie_client.set_account_id(8)
    
    print("🔍 Buscando lançamentos de 12/07/2025...")
    
    try:
        # Listar lançamentos
        result = omie_client.omie.listar_lanc_c_c(
            nPagina=1,
            nRegPorPagina=20,
            dtPagInicial="12/07/2025",
            dtPagFinal="12/07/2025"
        )
        
        if isinstance(result, dict) and 'listaLancamentos' in result:
            lancamentos = result['listaLancamentos']
            current_account_str = str(omie_client.current_account_id)
            
            print(f"📊 {len(lancamentos)} lançamentos encontrados")
            
            for i, lanc in enumerate(lancamentos):
                if omie_client._is_current_account_lancamento(lanc, current_account_str):
                    cabecalho = lanc.get('cabecalho', {})
                    valor = float(cabecalho.get('nValorLanc', 0))
                    codigo_lancamento = lanc.get('nCodLanc')
                    
                    # Focar no lançamento da Thaionara (R$ 62,05)
                    if abs(valor - 62.05) < 0.01:
                        print(f"\\n🎯 LANÇAMENTO DA THAIONARA ENCONTRADO")
                        print(f"   Código: {codigo_lancamento}")
                        print(f"   Valor: R$ {valor:.2f}")
                        print(f"   Código Integração (listagem): '{lanc.get('cCodIntLanc', '')}'")
                        
                        # CONSULTA ESPECÍFICA para obter detalhes completos
                        print(f"\\n🔍 CONSULTANDO LANÇAMENTO ESPECÍFICO...")
                        
                        try:
                            lanc_detalhado = omie_client.omie.consulta_lanc_c_c(
                                nCodLanc=int(codigo_lancamento)
                            )
                            
                            print(f"   ✅ Consulta específica realizada")
                            print(f"   📋 Keys: {list(lanc_detalhado.keys())}")
                            
                            # Verificar código de integração na consulta específica
                            codigo_int_detalhado = lanc_detalhado.get('cCodIntLanc', '')
                            print(f"   🔑 Código Integração (específica): '{codigo_int_detalhado}'")
                            
                            # Verificar detalhes completos
                            detalhes = lanc_detalhado.get('detalhes', [])
                            print(f"   📝 Detalhes ({len(detalhes)}):")
                            
                            for j, detalhe in enumerate(detalhes):
                                print(f"      Detalhe {j+1}: {type(detalhe)}")
                                
                                if isinstance(detalhe, dict):
                                    print(f"         Keys: {list(detalhe.keys())}")
                                    
                                    # Procurar especificamente por cNumDoc
                                    num_doc = detalhe.get('cNumDoc', '')
                                    if num_doc:
                                        print(f"         🎯 cNumDoc ENCONTRADO: '{num_doc}'")
                                        
                                        # Verificar se corresponde ao OFX ID esperado
                                        ofx_id_esperado = "68725a13-ed77-475f-9"
                                        if num_doc == ofx_id_esperado:
                                            print(f"         ✅ MATCH! Este é o OFX ID truncado!")
                                        else:
                                            print(f"         🤔 Valor diferente do esperado: '{ofx_id_esperado}'")
                                    
                                    # Mostrar outros campos relevantes
                                    for key, value in detalhe.items():
                                        if key in ['cTipo', 'cObs', 'cCodCateg', 'nCodCliente']:
                                            print(f"         {key}: '{value}'")
                                else:
                                    print(f"         Valor string: {detalhe}")
                            
                            # Verificar outros campos que podem ter o número do documento
                            print(f"\\n   🔍 OUTROS CAMPOS RELEVANTES:")
                            for key, value in lanc_detalhado.items():
                                if key not in ['cabecalho', 'detalhes']:
                                    value_str = str(value)
                                    # Procurar padrões de UUID no valor
                                    import re
                                    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}'
                                    if re.search(uuid_pattern, value_str.lower()):
                                        print(f"      🎯 {key}: '{value}' (contém padrão UUID)")
                                    elif 'doc' in key.lower() or 'num' in key.lower():
                                        print(f"      📄 {key}: '{value}'")
                        
                        except Exception as e:
                            print(f"   ❌ Erro na consulta específica: {e}")
                        
                        break  # Parar após encontrar o lançamento da Thaionara
            
        else:
            print(f"❌ Erro na listagem: {result}")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\\n" + "=" * 70)
    print("🏁 CORREÇÃO CONCLUÍDA")

if __name__ == "__main__":
    fix_detailed_search()