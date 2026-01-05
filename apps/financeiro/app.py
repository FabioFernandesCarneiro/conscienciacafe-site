#!/usr/bin/env python3
"""Sistema Web de Gestão Financeira - Consciência Café."""

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from datetime import datetime, date, timedelta
import os
import tempfile
import requests
import logging
from dotenv import load_dotenv
from flask_login import LoginManager, current_user
from src.omie_client import OmieClient
from smart_reconciliation_extrato import SmartReconciliationExtrato
from src.ml_categorizer import MLCategorizer
from src.b2b.google_sheets_client import GoogleSheetsClient
from src.b2b.b2b_metrics import B2BMetrics
from src.b2b.crm_service import CRMService
from src.b2b.google_maps_client import GoogleMapsClient
from src.b2b.lead_enrichment import LeadEnrichmentService
from src.local_data_service import LocalDataService
import time
from src.auth_service_sqlalchemy import AuthService
from src.auth_routes import create_auth_blueprint
from src.services.catalog_service import CatalogService
from src.services.order_service import OrderService
from src.orders_routes import create_orders_blueprint
from src.db import init_engine
from src.models import Base

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar engine do banco (suporta DATABASE_URL do Railway)
engine = init_engine(os.getenv('DATABASE_URL'))
Base.metadata.create_all(engine)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Configurar logging básico enquanto estivermos em modo de desenvolvimento
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
logger = logging.getLogger(__name__)

# Cliente Omie global
omie_client = OmieClient(
    app_key=os.getenv('OMIE_APP_KEY'),
    app_secret=os.getenv('OMIE_APP_SECRET')
)

# Sistema de ML para categorização inteligente
ml_categorizer = MLCategorizer()

# Sistema B2B para análise de vendas
google_sheets_client = GoogleSheetsClient()
b2b_metrics = B2BMetrics()

# Serviços locais em desenvolvimento
local_service = LocalDataService()
crm_service = CRMService()
lead_enrichment_service = LeadEnrichmentService()
auth_service = AuthService()
coffee_catalog_service = CatalogService()
order_service = OrderService()

try:
    google_maps_client = GoogleMapsClient()
except Exception as exc:
    logger.warning("Google Maps API desabilitada: %s", exc)
    google_maps_client = None

# Importar após inicialização dos clientes
try:
    from src.b2b.sales_analyzer import SalesAnalyzer
    from src.b2b.client_manager import ClientManager
    from src.b2b.sales_repository import SalesRepository
    
    # Inicializar analisadores B2B
    sales_repository = SalesRepository()
    sales_analyzer = SalesAnalyzer(sales_repository, crm_service)
    client_manager = ClientManager(omie_client)
    print("✅ Módulos B2B carregados com sucesso")
except ImportError as e:
    logger.warning("Erro ao carregar módulos B2B: %s", e)
    sales_analyzer = None
    client_manager = None

# Cache para contas correntes (evitar consultas desnecessárias)
contas_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 3600  # 1 hora
}


# ==========================
# Autenticação e Login
# ==========================

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id: str):
    try:
        return auth_service.load_user_by_id(int(user_id))
    except (TypeError, ValueError):
        return None


LOGIN_EXEMPT_ENDPOINTS = {
    'auth.login',
    'auth.logout',
    'admin_fix_sequences',
}


@app.before_request
def require_login():
    endpoint = request.endpoint
    if not endpoint:
        return
    if endpoint.startswith('static') or endpoint in LOGIN_EXEMPT_ENDPOINTS:
        return
    if endpoint.startswith('auth.'):
        return
    if current_user.is_authenticated:
        return
    next_url = request.url if request.method == 'GET' else url_for('dashboard')
    return redirect(url_for('auth.login', next=next_url))


# Registrar blueprint de autenticação
app.register_blueprint(create_auth_blueprint(auth_service))
# Registrar blueprint de pedidos
app.register_blueprint(
    create_orders_blueprint(
        coffee_catalog_service,
        order_service,
        crm_service,
        google_sheets_client,
        lead_enrichment_service,
        google_maps_client,
    )
)

# Registrar blueprint financeiro (Novo)
from src.financial_routes import create_financial_blueprint
app.register_blueprint(create_financial_blueprint())

def processar_contas_biblioteca_oficial(lista_contas):
    """Processa lista de contas da biblioteca oficial api-omie"""
    contas = []
    
    for conta in lista_contas:
        # Extrair informações baseado na estrutura real da API
        codigo_cc = conta.get('nCodCC', '')
        nome_conta = conta.get('descricao', 'Conta sem nome')
        inativo = conta.get('inativo', 'N')
        ativo = inativo == 'N'  # N = Ativo, S = Inativo
        
        # Informações adicionais da conta
        tipo_conta = conta.get('tipo', 'CC')  # CC = Conta Corrente
        codigo_banco = conta.get('codigo_banco', '')
        numero_conta = conta.get('numero_conta_corrente', '')
        bloqueado = conta.get('bloqueado', 'N') == 'S'
        
        if ativo and codigo_cc and not bloqueado:  # Só contas ativas, com código e não bloqueadas
            # Determinar tipo baseado no nome e tipo
            tipo_formatado = determinar_tipo_conta(nome_conta)
            
            contas.append({
                'id': str(codigo_cc),
                'nome': nome_conta,
                'tipo': tipo_formatado,
                'ativo': True,
                'fonte': 'omie_biblioteca_oficial',
                'omie_info': {
                    'codigo_cc': codigo_cc,
                    'tipo_original': tipo_conta,
                    'banco': codigo_banco,
                    'numero_conta': numero_conta,
                    'inativo': inativo,
                    'bloqueado': bloqueado,
                    'saldo_inicial': conta.get('saldo_inicial', 0),
                    'saldo_data': conta.get('saldo_data', '')
                }
            })
    
    return contas

def determinar_tipo_conta(nome_conta):
    """Determina tipo da conta baseado no nome"""
    nome_lower = nome_conta.lower()
    
    if 'cartão' in nome_lower or 'cartao' in nome_lower:
        return 'cartao_credito'
    elif 'poupança' in nome_lower or 'poupanca' in nome_lower:
        return 'poupanca'
    elif 'investimento' in nome_lower:
        return 'investimento'
    elif 'caixa' in nome_lower:
        return 'caixa'
    else:
        return 'conta_corrente'

def deduzir_nome_conta_por_id_e_descricao(conta_id, descricao):
    """Deduz nome da conta baseado no ID e descrições dos lançamentos"""
    conta_id_str = str(conta_id)
    desc_lower = descricao.lower() if descricao else ''
    
    # Mapeamento conhecido baseado nos IDs que descobrimos
    mapeamento_conhecido = {
        '2103553430': 'Conta Corrente Nubank PJ',
        '1952848402': 'BTG Pactual - Ag: 50 / Conta: 491512-9', 
        '2101800357': 'Caixa',
        '2103781092': 'Cora'
    }
    
    # Se temos mapeamento conhecido, usar ele
    if conta_id_str in mapeamento_conhecido:
        return mapeamento_conhecido[conta_id_str]
    
    # Senão, tentar deduzir pelo conteúdo das descrições
    if 'nubank' in desc_lower:
        if 'cartão' in desc_lower or 'cartao' in desc_lower:
            return f"Cartão Nubank - {conta_id_str}"
        else:
            return f"Conta Corrente Nubank - {conta_id_str}"
    elif 'btg' in desc_lower:
        return f"BTG Pactual - {conta_id_str}"
    elif 'caixa' in desc_lower:
        return f"Caixa - {conta_id_str}"
    elif 'cora' in desc_lower:
        return f"Cora - {conta_id_str}"
    elif 'mercado livre' in desc_lower or 'mercadolivre' in desc_lower:
        return f"Mercado Livre - {conta_id_str}"
    else:
        return f"Conta {conta_id_str}"

def descobrir_contas_por_lancamentos():
    """Descobre contas ativas através dos lançamentos dos últimos 90 dias"""
    contas_encontradas = {}
    
    try:
        # Buscar lançamentos dos últimos 90 dias para descobrir contas ativas
        data_fim = date.today()
        data_inicio = data_fim - timedelta(days=90)
        
        data_inicio_str = data_inicio.strftime('%d/%m/%Y')
        data_fim_str = data_fim.strftime('%d/%m/%Y')
        
        print(f"   🔍 Analisando lançamentos de {data_inicio_str} a {data_fim_str}")
        
        # Buscar lançamentos para descobrir contas
        result = omie_client.omie.listar_lanc_c_c(
            nPagina=1,
            nRegPorPagina=200,  # Buscar mais lançamentos para descobrir mais contas
            dtPagInicial=data_inicio_str,
            dtPagFinal=data_fim_str
        )
        
        if isinstance(result, dict) and 'listaLancamentos' in result:
            for lanc in result['listaLancamentos']:
                cabecalho = lanc.get('cabecalho', {})
                conta_id = cabecalho.get('nCodCC', '')
                desc_lanc = cabecalho.get('cDescLanc', '')
                
                if conta_id and str(conta_id) not in contas_encontradas:
                    # Tentar deduzir nome da conta baseado na descrição e ID
                    nome_conta = deduzir_nome_conta_por_id_e_descricao(conta_id, desc_lanc)
                    
                    contas_encontradas[str(conta_id)] = {
                        'id': str(conta_id),
                        'nome': nome_conta,
                        'tipo': determinar_tipo_conta(nome_conta),
                        'ativo': True,
                        'fonte': 'descoberta_lancamentos',
                        'transacoes_encontradas': 1
                    }
                elif conta_id in contas_encontradas:
                    contas_encontradas[conta_id]['transacoes_encontradas'] += 1
        
        # Converter para lista e ordenar por número de transações
        contas = list(contas_encontradas.values())
        contas.sort(key=lambda x: x['transacoes_encontradas'], reverse=True)
        
        print(f"   ✅ {len(contas)} contas descobertas através de lançamentos")
        
        return contas
        
    except Exception as e:
        print(f"   ❌ Erro ao descobrir contas por lançamentos: {e}")
        return []

def obter_nome_conta_por_id(conta_id):
    """Obtém o nome da conta a partir do ID consultando o cache de contas"""
    try:
        # Verificar se temos contas no cache
        if contas_cache['data']:
            for conta in contas_cache['data']:
                if conta['id'] == str(conta_id):
                    return conta['nome']
        
        # Se não encontrou no cache, tentar buscar
        contas = buscar_contas_omie()
        for conta in contas:
            if conta['id'] == str(conta_id):
                return conta['nome']
        
        # Fallback para nome genérico
        return f"Conta {conta_id}"
    
    except Exception as e:
        print(f"❌ Erro ao obter nome da conta {conta_id}: {e}")
        return f"Conta {conta_id}"

@app.route('/')
def dashboard():
    """Página principal - Dashboard (B2B)"""
    return render_template('b2b_dashboard.html')

@app.route('/local')
@app.route('/local/dashboard')
def dashboard_local():
    """Dashboard da versão local (sem Omie)"""
    try:
        stats = local_service.get_database_statistics()
        accounts = local_service.get_available_accounts()
        migration_info = stats.get('last_migration', {})
        return render_template(
            'dashboard_local.html',
            stats=stats,
            accounts=accounts,
            migration_info=migration_info
        )
    except Exception as exc:
        return render_template(
            'dashboard_local.html',
            error=f"Erro ao carregar dashboard: {exc}",
            stats={},
            accounts=[],
            migration_info={}
        )

@app.route('/local/extrato-pj')
def extrato_pj_local():
    """Tela de extrato para a versão local"""
    return render_template('extrato_pj_local.html')

@app.route('/api/local/contas-disponiveis')
def api_local_contas_disponiveis():
    """API para listar contas disponíveis no banco local"""
    try:
        contas = local_service.get_available_accounts()
        return jsonify({
            'success': True,
            'contas': contas,
            'fonte': 'local_database',
            'total': len(contas)
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar contas locais: {exc}',
            'contas': []
        })

@app.route('/api/local/extrato-conta-corrente')
def api_local_extrato_conta_corrente():
    """API para obter extrato de contas usando o banco local"""
    try:
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        conta_id = request.args.get('conta_id')
        pagina = int(request.args.get('pagina', 1))

        if not conta_id:
            return jsonify({
                'success': False,
                'error': 'Parâmetro conta_id é obrigatório'
            }), 400

        if not data_inicio or not data_fim:
            hoje = date.today()
            data_fim_obj = hoje
            data_inicio_obj = hoje - timedelta(days=30)
            data_inicio = data_inicio_obj.strftime('%d/%m/%Y')
            data_fim = data_fim_obj.strftime('%d/%m/%Y')

        print(f"🔧 [LOCAL] Buscando extrato da conta ID: {conta_id} de {data_inicio} a {data_fim}")

        result = local_service.get_account_statement(
            account_id=int(conta_id),
            start_date=data_inicio,
            end_date=data_fim,
            page=pagina
        )

        if result.get('success'):
            return jsonify(result)
        return jsonify(result), 400
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Parâmetro conta_id deve ser numérico'
        }), 400
    except Exception as exc:
        print(f"❌ [LOCAL] Erro ao buscar extrato: {exc}")
        return jsonify({
            'success': False,
            'error': f'Erro ao carregar extrato local: {exc}'
        }), 500

@app.route('/api/local/categorias')
def api_local_categorias():
    """API para listar categorias disponíveis no banco local"""
    try:
        categorias = local_service.get_categories()
        return jsonify({
            'success': True,
            'categorias': categorias,
            'fonte': 'local_database',
            'total': len(categorias)
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar categorias locais: {exc}',
            'categorias': []
        })

@app.route('/api/local/clientes-fornecedores')
def api_local_clientes_fornecedores():
    """API para listar clientes e fornecedores locais"""
    try:
        clientes_fornecedores = local_service.get_clients_suppliers()
        return jsonify({
            'success': True,
            'clientes_fornecedores': clientes_fornecedores,
            'fonte': 'local_database',
            'total': len(clientes_fornecedores)
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar clientes/fornecedores locais: {exc}',
            'clientes_fornecedores': []
        })

@app.route('/api/local/estatisticas-banco')
def api_local_estatisticas_banco():
    """API para estatísticas do banco de dados local"""
    try:
        stats = local_service.get_database_statistics()
        return jsonify({
            'success': True,
            'estatisticas': stats
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter estatísticas: {exc}'
        })

@app.route('/api/local/buscar-transacoes')
def api_local_buscar_transacoes():
    """API para buscar transações no banco local"""
    try:
        query = request.args.get('q', '')
        conta_id = request.args.get('conta_id')
        limit = int(request.args.get('limit', 50))

        if not query or len(query) < 3:
            return jsonify({
                'success': False,
                'error': 'Query deve ter pelo menos 3 caracteres'
            }), 400

        account_id = int(conta_id) if conta_id else None
        transacoes = local_service.search_transactions(query, account_id, limit)

        return jsonify({
            'success': True,
            'transacoes': transacoes,
            'total': len(transacoes)
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Parâmetro conta_id deve ser numérico'
        }), 400
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f'Erro na busca: {exc}'
        }), 500

@app.route('/api/local/status-migracao')
def api_local_status_migracao():
    """API para verificar status da migração em execução"""
    try:
        import json

        status_file = "data/migration_status.json"
        pid_file = "data/migration.pid"

        status_info = {
            'migration_running': False,
            'pid': None,
            'last_status': None
        }

        if os.path.exists(pid_file):
            with open(pid_file, 'r', encoding='utf-8') as pid_handle:
                pid = int(pid_handle.read().strip())

            try:
                os.kill(pid, 0)
                status_info['migration_running'] = True
                status_info['pid'] = pid
            except OSError:
                status_info['migration_running'] = False
                os.remove(pid_file)

        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as status_handle:
                status_info['last_status'] = json.load(status_handle)

        status_info['database_stats'] = local_service.get_database_statistics()

        return jsonify({
            'success': True,
            'status': status_info
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f'Erro ao verificar status: {exc}'
        }), 500

@app.route('/extrato-pj')
def extrato_pj():
    """Tela de extrato das contas pessoa jurídica"""
    return render_template('extrato_pj.html')

@app.route('/api/extrato-conta-corrente')
def api_extrato_conta_corrente():
    """API para obter extrato de conta corrente usando API oficial de Extrato"""
    try:
        # Parâmetros da requisição
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        conta_id = request.args.get('conta_id', '2103553430')  # Default: Nubank PJ
        
        # Se não informar datas, usar últimos 30 dias
        if not data_inicio or not data_fim:
            hoje = date.today()
            data_fim_obj = hoje
            data_inicio_obj = hoje - timedelta(days=30)
            data_inicio = data_inicio_obj.strftime('%d/%m/%Y')
            data_fim = data_fim_obj.strftime('%d/%m/%Y')
        
        print(f"🔧 Buscando extrato da conta ID: {conta_id} de {data_inicio} a {data_fim}")
        
        # Usar API oficial de Extrato do Omie
        result = omie_client.omie._chamar_api(
            call='ListarExtrato',
            endpoint='financas/extrato/',
            param={
                'nCodCC': int(conta_id),
                'dPeriodoInicial': data_inicio,
                'dPeriodoFinal': data_fim
            }
        )
        
        if isinstance(result, dict) and 'listaMovimentos' in result:
            movimentos = result['listaMovimentos']
            
            # Processar movimentos para o formato da interface
            extrato = []
            total_creditos = 0
            total_debitos = 0
            
            # Converter datas do período para comparação
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%d/%m/%Y').date()
                data_fim_obj = datetime.strptime(data_fim, '%d/%m/%Y').date()
            except ValueError:
                data_inicio_obj = None
                data_fim_obj = None
            
            for movimento in movimentos:
                # Pular saldo anterior e registros de saldo inicial
                cliente = movimento.get('cDesCliente', '')
                if cliente == 'SALDO ANTERIOR' or cliente == 'SALDO INICIAL':
                    continue
                
                # Verificar se a transação está dentro do período (filtro rigoroso)
                data_movimento_str = movimento.get('dDataLancamento', '')
                if data_movimento_str and data_inicio_obj and data_fim_obj:
                    try:
                        data_movimento_obj = datetime.strptime(data_movimento_str, '%d/%m/%Y').date()
                        
                        # Filtro rigoroso: SOMENTE transações exatamente dentro do período solicitado
                        if data_movimento_obj < data_inicio_obj or data_movimento_obj > data_fim_obj:
                            continue
                    except ValueError:
                        continue
                elif not data_movimento_str:
                    continue
                
                valor = float(movimento.get('nValorDocumento', 0))
                
                if valor == 0:
                    continue
                
                # Determinar tipo baseado no valor
                tipo_transacao = 'Crédito' if valor > 0 else 'Débito'
                valor_abs = abs(valor)
                
                if tipo_transacao == 'Crédito':
                    total_creditos += valor_abs
                else:
                    total_debitos += valor_abs
                
                # Formatar item do extrato
                item_extrato = {
                    'data': movimento.get('dDataLancamento', ''),
                    'descricao': movimento.get('cObservacoes', ''),
                    'cliente': movimento.get('cDesCliente', ''),
                    'categoria': movimento.get('cDesCategoria', 'Não Categorizado'),
                    'categoria_codigo': movimento.get('cCodCategoria', ''),
                    'tipo': tipo_transacao,
                    'valor': valor_abs,
                    'valor_formatado': f"R$ {valor_abs:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'saldo': movimento.get('nSaldo', 0),
                    'saldo_formatado': f"R$ {movimento.get('nSaldo', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'codigo': movimento.get('nCodLancamento', ''),
                    'documento': movimento.get('cNumero', ''),
                    'conciliado': movimento.get('cSituacao', '') == 'Conciliado',
                    'data_conciliacao': movimento.get('dDataConciliacao', ''),
                    'natureza': movimento.get('cNatureza', ''),  # R = Receita, P = Pagamento
                    'tipo_documento': movimento.get('cTipoDocumento', ''),
                    'origem': movimento.get('cOrigem', '')
                }
                
                extrato.append(item_extrato)
            
            # Ordenar por data (mais recentes primeiro) 
            try:
                extrato.sort(key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'), reverse=True)
            except ValueError:
                # Se houver erro de formatação de data, manter ordem original
                pass
            
            # Informações da conta e saldos
            conta_info = {
                'id': conta_id,
                'nome': result.get('cDescricao', 'Conta sem nome'),
                'omie_id': conta_id,
                'banco': result.get('nCodBanco', ''),
                'tipo': result.get('cDesTipo', ''),
                'saldo_anterior': result.get('nSaldoAnterior', 0),
                'saldo_atual': result.get('nSaldoAtual', 0),
                'saldo_conciliado': result.get('nSaldoConciliado', 0),
                'saldo_disponivel': result.get('nSaldoDisponivel', 0)
            }
            
            response = jsonify({
                'success': True,
                'extrato': extrato,
                'resumo': {
                    'total_lancamentos': len(extrato),
                    'total_creditos': total_creditos,
                    'total_creditos_formatado': f"R$ {total_creditos:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'total_debitos': total_debitos,
                    'total_debitos_formatado': f"R$ {total_debitos:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'saldo_periodo': total_creditos - total_debitos,
                    'saldo_periodo_formatado': f"R$ {(total_creditos - total_debitos):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'periodo': f"{data_inicio} a {data_fim}",
                    'saldo_anterior': result.get('nSaldoAnterior', 0),
                    'saldo_atual': result.get('nSaldoAtual', 0),
                    'saldo_conciliado': result.get('nSaldoConciliado', 0)
                },
                'conta_info': conta_info
            })
            
            # Adicionar cabeçalhos para evitar cache
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            return response
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao consultar extrato na API do Omie'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })

def buscar_contas_omie():
    """Busca contas correntes diretamente da API Omie com cache"""
    try:
        # Verificar se cache ainda é válido
        agora = time.time()
        if (contas_cache['data'] is not None and 
            agora - contas_cache['timestamp'] < contas_cache['cache_duration']):
            return contas_cache['data']
        
        print("🔍 Buscando contas correntes do Omie...")
        
        # Método 1: Usar método listar_contas_correntes da biblioteca
        contas = []
        
        try:
            result = omie_client.omie.listar_contas_correntes(pagina=1, registros_por_pagina=100)
            
            if isinstance(result, dict) and 'ListarContasCorrentes' in result:
                print("✅ Usando listar_contas_correntes da biblioteca")
                contas = processar_contas_biblioteca_oficial(result['ListarContasCorrentes'])
        except Exception as e:
            print(f"⚠️ Método listar_contas_correntes falhou: {e}")
        
        # Método 2: Descobrir contas através dos lançamentos (fallback)
        if not contas:
            print("🔍 Descobrindo contas através dos lançamentos...")
            contas = descobrir_contas_por_lancamentos()
        
        # Ordenar por nome
        contas.sort(key=lambda x: x['nome'])
        
        # Atualizar cache
        contas_cache['data'] = contas
        contas_cache['timestamp'] = agora
        
        print(f"✅ {len(contas)} contas encontradas e cacheadas")
        
        return contas
        
    except Exception as e:
        print(f"❌ Erro ao buscar contas do Omie: {e}")
        
        # Retornar contas padrão em caso de erro
        return [
            {
                'id': '2103553430',
                'nome': 'Conta Corrente Nubank PJ (Padrão)',
                'tipo': 'conta_corrente',
                'ativo': True,
                'fonte': 'fallback'
            }
        ]

@app.route('/api/contas-disponiveis')
def api_contas_disponiveis():
    """API para listar contas disponíveis (busca dinâmica do Omie)"""
    try:
        contas = buscar_contas_omie()
        
        return jsonify({
            'success': True,
            'contas': contas,
            'cached': contas_cache['timestamp'] > 0,
            'cache_age': int(time.time() - contas_cache['timestamp']) if contas_cache['timestamp'] > 0 else 0
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar contas: {str(e)}',
            'contas': []
        })

@app.route('/api/contas-cache/limpar')
def api_limpar_cache_contas():
    """API para limpar cache de contas (forçar nova consulta)"""
    global contas_cache
    contas_cache = {
        'data': None,
        'timestamp': 0,
        'cache_duration': 3600
    }
    
    return jsonify({
        'success': True,
        'message': 'Cache de contas limpo com sucesso'
    })

@app.route('/api/cache/limpar-todos')
def api_limpar_todos_caches():
    """API para limpar todos os caches"""
    global contas_cache, categorias_cache, clientes_fornecedores_cache
    
    contas_cache = {
        'data': None,
        'timestamp': 0,
        'cache_duration': 3600
    }
    
    categorias_cache = {
        'data': None,
        'timestamp': 0,
        'cache_duration': 7200
    }
    
    clientes_fornecedores_cache = {
        'data': None,
        'timestamp': 0,
        'cache_duration': 3600
    }
    
    return jsonify({
        'success': True,
        'message': 'Todos os caches foram limpos com sucesso'
    })

# Cache para categorias e clientes
categorias_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 7200  # 2 horas
}

clientes_fornecedores_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 3600  # 1 hora
}

@app.route('/api/categorias-omie')
def api_categorias_omie():
    """API para listar categorias do Omie"""
    try:
        # Verificar cache
        agora = time.time()
        if (categorias_cache['data'] is not None and 
            agora - categorias_cache['timestamp'] < categorias_cache['cache_duration']):
            return jsonify({
                'success': True,
                'categorias': categorias_cache['data'],
                'cached': True
            })
        
        print("🏷️ Buscando categorias do Omie...")
        
        # Buscar categorias via API
        try:
            result = omie_client.omie._chamar_api(
                call='ListarCategorias',
                endpoint='geral/categorias/',
                param={'pagina': 1, 'registros_por_pagina': 100}
            )
            
            categorias = []
            if isinstance(result, dict) and 'categoria_cadastro' in result:
                for cat in result['categoria_cadastro']:
                    # Inferir tipo baseado na descrição se não estiver preenchido
                    tipo = cat.get('tipo', '')
                    if not tipo:
                        desc = cat.get('descricao', '').lower()
                        if any(keyword in desc for keyword in ['receita', 'venda', 'entrada', 'receb']):
                            tipo = 'R'
                        elif any(keyword in desc for keyword in ['despesa', 'gasto', 'saida', 'pag']):
                            tipo = 'D'
                        else:
                            # Para transferências e outros, considerar neutro
                            tipo = 'N'
                    
                    categorias.append({
                        'codigo': cat.get('codigo', ''),
                        'descricao': cat.get('descricao', ''),
                        'tipo': tipo,
                        'ativo': cat.get('inativo', 'N') == 'N'
                    })
            
            # Filtrar apenas categorias ativas
            categorias_ativas = [cat for cat in categorias if cat['ativo']]
            
            # Atualizar cache
            categorias_cache['data'] = categorias_ativas
            categorias_cache['timestamp'] = agora
            
            print(f"✅ {len(categorias_ativas)} categorias encontradas")
            
            return jsonify({
                'success': True,
                'categorias': categorias_ativas,
                'cached': False
            })
            
        except Exception as e:
            print(f"❌ Erro ao buscar categorias: {e}")
            # Retornar categorias padrão
            categorias_padrao = [
                {'codigo': 'REC01', 'descricao': 'Vendas', 'tipo': 'R'},
                {'codigo': 'REC02', 'descricao': 'Outras Receitas', 'tipo': 'R'},
                {'codigo': 'DES01', 'descricao': 'Despesas Operacionais', 'tipo': 'D'},
                {'codigo': 'DES02', 'descricao': 'Taxas Bancárias', 'tipo': 'D'},
                {'codigo': 'DES03', 'descricao': 'Compras', 'tipo': 'D'},
            ]
            
            return jsonify({
                'success': True,
                'categorias': categorias_padrao,
                'cached': False,
                'fallback': True
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}',
            'categorias': []
        })

@app.route('/api/criar-cliente', methods=['POST'])
def criar_cliente():
    """API para criar novo cliente no Omie"""
    try:
        data = request.get_json()
        
        if not data or not data.get('nome'):
            return jsonify({
                'success': False,
                'error': 'Nome do cliente é obrigatório'
            }), 400
        
        # Preparar dados do cliente (campos mínimos, sem CPF obrigatório)
        import time
        codigo_integracao = f"WEB_{int(time.time())}"  # Código único
        
        dados_cliente = {
            "codigo_cliente_integracao": codigo_integracao,
            "razao_social": data['nome'].upper().strip(),
            "nome_fantasia": data['nome'].strip()
        }
        
        # Campos opcionais
        if data.get('email'):
            dados_cliente['email'] = data['email'].strip()
        
        if data.get('telefone'):
            telefone = data['telefone'].strip()
            # Extrair DDD e número do telefone 
            import re
            match = re.search(r'\(?(\d{2})\)?\s*(\d{4,5})-?(\d{4})', telefone)
            if match:
                dados_cliente['telefone1_ddd'] = match.group(1)
                dados_cliente['telefone1_numero'] = match.group(2) + match.group(3)
        
        # CPF/CNPJ é opcional agora!
        if data.get('cpf_cnpj'):
            cpf_cnpj = data['cpf_cnpj'].strip()
            dados_cliente['cnpj_cpf'] = cpf_cnpj
            # Determinar se é pessoa física ou jurídica pelo tamanho
            cpf_cnpj_numbers = re.sub(r'[^\d]', '', cpf_cnpj)
            dados_cliente['pessoa_fisica'] = 'S' if len(cpf_cnpj_numbers) == 11 else 'N'
        
        print(f"🆕 Criando cliente: {dados_cliente}")
        
        # Chamar API do Omie
        result = omie_client.omie._chamar_api(
            call='IncluirCliente',
            endpoint='geral/clientes/',
            param=dados_cliente
        )
        
        if isinstance(result, dict) and 'codigo_cliente_omie' in result:
            # Limpar cache de clientes para forçar recarregamento
            clientes_fornecedores_cache['data'] = None
            
            return jsonify({
                'success': True,
                'cliente': {
                    'codigo': result['codigo_cliente_omie'],
                    'nome': dados_cliente['nome_fantasia'],
                    'codigo_integracao': codigo_integracao,
                    'tipo': 'Cliente'
                },
                'message': f"Cliente '{dados_cliente['nome_fantasia']}' criado com sucesso!"
            })
        else:
            # Tratar erros da API
            error_msg = "Erro desconhecido"
            if isinstance(result, dict):
                if 'Mensagem' in result and 'faultstring' in result['Mensagem']:
                    error_msg = result['Mensagem']['faultstring']
                elif 'descricao_status' in result:
                    error_msg = result['descricao_status']
            
            return jsonify({
                'success': False,
                'error': f"Erro da API Omie: {error_msg}"
            }), 400
            
    except Exception as e:
        print(f"❌ Erro ao criar cliente: {e}")
        return jsonify({
            'success': False,
            'error': f"Erro interno: {str(e)}"
        }), 500

@app.route('/api/clientes-fornecedores')
def api_clientes_fornecedores():
    """API para listar clientes e fornecedores do Omie"""
    try:
        # Verificar se foi solicitada atualização forçada (cache-busting)
        force_refresh = request.args.get('t') is not None
        
        # Verificar cache (ignorar se força atualização)
        agora = time.time()
        if (not force_refresh and 
            clientes_fornecedores_cache['data'] is not None and 
            agora - clientes_fornecedores_cache['timestamp'] < clientes_fornecedores_cache['cache_duration']):
            return jsonify({
                'success': True,
                'clientes_fornecedores': clientes_fornecedores_cache['data'],
                'cached': True
            })
        
        if force_refresh:
            print("🔄 Forçando atualização da lista de clientes/fornecedores...")
        
        print("👥 Buscando clientes e fornecedores do Omie...")
        
        todos_contatos = []
        
        # Buscar clientes
        try:
            result_clientes = omie_client.omie._chamar_api(
                call='ListarClientes',
                endpoint='geral/clientes/',
                param={'pagina': 1, 'registros_por_pagina': 200}
            )
            
            if isinstance(result_clientes, dict) and 'clientes_cadastro' in result_clientes:
                for cliente in result_clientes['clientes_cadastro']:
                    if cliente.get('inativo', 'N') == 'N':  # Só ativos
                        todos_contatos.append({
                            'codigo': cliente.get('codigo_cliente_omie', ''),
                            'nome': cliente.get('razao_social', cliente.get('nome_fantasia', '')),
                            'tipo': 'Cliente',
                            'cnpj_cpf': cliente.get('cnpj_cpf', '')
                        })
        except Exception as e:
            print(f"⚠️ Erro ao buscar clientes: {e}")
        
        # Buscar fornecedores
        try:
            result_fornecedores = omie_client.omie._chamar_api(
                call='ListarFornecedores',
                endpoint='geral/fornecedor/',
                param={'pagina': 1, 'registros_por_pagina': 200}
            )
            
            if isinstance(result_fornecedores, dict) and 'fornecedor_cadastro' in result_fornecedores:
                for fornecedor in result_fornecedores['fornecedor_cadastro']:
                    if fornecedor.get('inativo', 'N') == 'N':  # Só ativos
                        todos_contatos.append({
                            'codigo': fornecedor.get('codigo_fornecedor_omie', ''),
                            'nome': fornecedor.get('razao_social', fornecedor.get('nome_fantasia', '')),
                            'tipo': 'Fornecedor',
                            'cnpj_cpf': fornecedor.get('cnpj_cpf', '')
                        })
        except Exception as e:
            print(f"⚠️ Erro ao buscar fornecedores: {e}")
        
        # Ordenar por nome
        todos_contatos.sort(key=lambda x: x['nome'])
        
        # Atualizar cache
        clientes_fornecedores_cache['data'] = todos_contatos
        clientes_fornecedores_cache['timestamp'] = agora
        
        print(f"✅ {len(todos_contatos)} clientes/fornecedores encontrados")
        
        return jsonify({
            'success': True,
            'clientes_fornecedores': todos_contatos,
            'cached': False,
            'force_refreshed': force_refresh
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}',
            'clientes_fornecedores': []
        })

@app.route('/api/sugestoes-inteligentes', methods=['POST'])
def api_sugestoes_inteligentes():
    """API para gerar sugestões inteligentes usando ML"""
    try:
        data = request.get_json()
        if not data or 'transacoes' not in data:
            return jsonify({
                'success': False,
                'error': 'Dados de transações são obrigatórios'
            })
        
        print(f"🤖 Gerando sugestões inteligentes para {len(data['transacoes'])} transações...")
        
        sugestoes = []
        
        for transacao in data['transacoes']:
            descricao = transacao.get('descricao', '')
            valor = float(transacao.get('valor', 0))
            
            # Limpar descrição para ML
            clean_description = _clean_description_for_ml(descricao)
            
            # 1. Tentar predição com modelo ML
            categoria_ml, confianca = ml_categorizer.predict_category(
                descricao, clean_description, abs(valor)
            )
            
            # 2. Buscar transações similares
            similares = ml_categorizer.suggest_similar_transactions(clean_description, limit=3)
            
            # 3. Gerar sugestão final
            categoria_sugerida = ''
            cliente_sugerido = ''
            confianca_final = 0.0
            
            if categoria_ml and confianca > 0.5:  # Alta confiança
                categoria_sugerida = categoria_ml
                confianca_final = confianca
                print(f"   📊 ML: {categoria_ml} (confiança: {confianca:.2f})")
            
            # Se tiver transações similares, usar a mais frequente
            if similares:
                melhor_similar = max(similares, key=lambda x: x['frequency'])
                if melhor_similar['category']:
                    # Buscar código da categoria pelo nome
                    categoria_codigo = _buscar_codigo_categoria_por_nome(melhor_similar['category'])
                    if categoria_codigo:
                        categoria_sugerida = categoria_codigo
                        confianca_final = max(confianca_final, 0.8)
                
                if melhor_similar['client_supplier']:
                    cliente_sugerido = melhor_similar['client_supplier']
                    confianca_final += 0.1
                
                print(f"   📚 Histórico: {melhor_similar['category']} | {melhor_similar['client_supplier']} (freq: {melhor_similar['frequency']})")
            
            # Fallback baseado no tipo de transação
            if not categoria_sugerida:
                if valor > 0:  # Crédito
                    categoria_sugerida = _encontrar_primeira_categoria_tipo('R')
                else:  # Débito
                    categoria_sugerida = _encontrar_primeira_categoria_tipo('D')
                confianca_final = 0.3
            
            if not cliente_sugerido:
                cliente_sugerido = _extrair_nome_da_descricao(descricao) or 'A definir'
            
            sugestoes.append({
                'categoria': categoria_sugerida,
                'cliente': cliente_sugerido,
                'confianca': min(confianca_final, 1.0),
                'fonte': 'ml' if categoria_ml else 'historico' if similares else 'fallback'
            })
        
        return jsonify({
            'success': True,
            'sugestoes': sugestoes,
            'stats': ml_categorizer.get_learning_stats()
        })
        
    except Exception as e:
        print(f"❌ Erro nas sugestões inteligentes: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}',
            'sugestoes': []
        })

def _clean_description_for_ml(description):
    """Limpa descrição para uso no ML (similar ao sistema existente)"""
    import re
    
    if not description:
        return ""
    
    # Converter para minúsculas e remover caracteres especiais
    clean = description.lower()
    clean = re.sub(r'[^\w\s]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    return clean

def _buscar_codigo_categoria_por_nome(nome_categoria):
    """Busca código da categoria pelo nome nas categorias do Omie"""
    global categorias_cache
    
    if not categorias_cache['data']:
        return None
    
    for categoria in categorias_cache['data']:
        if categoria['descricao'].lower() == nome_categoria.lower():
            return categoria['codigo']
    
    return None

def _encontrar_primeira_categoria_tipo(tipo):
    """Encontra primeira categoria do tipo especificado"""
    global categorias_cache
    
    if not categorias_cache['data']:
        return None
    
    for categoria in categorias_cache['data']:
        if categoria['tipo'] == tipo:
            return categoria['codigo']
    
    return None

def _extrair_nome_da_descricao(descricao):
    """Extrai nome de pessoa/empresa da descrição"""
    import re
    
    if not descricao:
        return None
    
    # Padrões comuns para extrair nomes
    patterns = [
        r'pix.*?-\s*([A-Z][A-Z\s]+[A-Z])',  # PIX - NOME PESSOA
        r'transferência.*?-\s*([A-Z][A-Z\s]+[A-Z])',  # Transferência - NOME
        r'para\s+([A-Z][A-Z\s]+[A-Z])',  # para NOME
        r'de\s+([A-Z][A-Z\s]+[A-Z])',  # de NOME
    ]
    
    for pattern in patterns:
        match = re.search(pattern, descricao, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            # Validar se parece um nome (pelo menos 2 palavras)
            if len(nome.split()) >= 2 and len(nome) > 5:
                return nome.title()
    
    return None

@app.route('/api/conciliar', methods=['POST'])
def api_conciliar():
    """API para conciliação de arquivo OFX com extrato"""
    try:
        # Verificar se arquivo foi enviado
        if 'arquivo_ofx' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo OFX foi enviado'
            })
        
        arquivo_ofx = request.files['arquivo_ofx']
        if arquivo_ofx.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo foi selecionado'
            })
        
        # Verificar conta ID
        conta_id = request.form.get('conta_id')
        if not conta_id:
            return jsonify({
                'success': False,
                'error': 'ID da conta é obrigatório'
            })
        
        # Salvar arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ofx') as temp_file:
            arquivo_ofx.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Executar conciliação
            reconciliacao = SmartReconciliationExtrato()
            resultados = reconciliacao.conciliar(temp_file_path, conta_id)
            
            if not resultados:
                return jsonify({
                    'success': False,
                    'error': 'Erro ao processar conciliação'
                })
            
            # Processar resultados para JSON
            matches_formatados = []
            for match in resultados['matches']:
                ofx = match['ofx']
                omie = match['omie']
                matches_formatados.append({
                    'criterio': match['criterio'],
                    'confianca': match['confianca'],
                    'ofx': {
                        'data': ofx.get('data'),
                        'valor': ofx.get('valor'),
                        'descricao': ofx.get('descricao', ''),
                        'numero_documento': ofx.get('numero_documento', '')
                    },
                    'omie': {
                        'data': omie.get('data'),
                        'valor': omie.get('valor'),
                        'descricao': omie.get('descricao', ''),
                        'cliente': omie.get('cliente', ''),
                        'documento': omie.get('documento', ''),
                        'codigo_lancamento': omie.get('codigo_lancamento', '')
                    }
                })
            
            ofx_nao_conciliadas = []
            for ofx in resultados['ofx_nao_conciliadas']:
                ofx_data = {
                    'data': ofx.get('data'),
                    'valor': ofx.get('valor'),
                    'descricao': ofx.get('descricao', ''),
                    'numero_documento': ofx.get('numero_documento', '')
                }
                
                # Incluir sugestões se existirem
                if 'sugestoes' in ofx:
                    ofx_data['sugestoes'] = ofx['sugestoes']
                    print(f"📤 Enviando sugestão para frontend: {ofx['sugestoes']}")
                else:
                    print(f"⚠️ Transação sem sugestões: {ofx.get('descricao', '')[:50]}")
                
                ofx_nao_conciliadas.append(ofx_data)
            
            taxa_conciliacao = (len(resultados['matches']) / resultados['total_ofx'] * 100) if resultados['total_ofx'] > 0 else 0
            
            return jsonify({
                'success': True,
                'resultados': {
                    'total_ofx': resultados['total_ofx'],
                    'total_omie': resultados['total_omie'],
                    'matches_encontrados': len(resultados['matches']),
                    'taxa_conciliacao': round(taxa_conciliacao, 1),
                    'ofx_nao_conciliadas': len(resultados['ofx_nao_conciliadas']),
                    'omie_nao_conciliadas': len(resultados['omie_nao_conciliadas'])
                },
                'matches': matches_formatados,  # Todos os matches encontrados
                'ofx_nao_conciliadas': ofx_nao_conciliadas,  # Todas as não conciliadas
                'nome_arquivo': arquivo_ofx.filename
            })
            
        finally:
            # Limpar arquivo temporário
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })

@app.route('/api/conciliar-matches', methods=['POST'])
def api_conciliar_matches():
    """API para conciliar matches selecionados no Omie"""
    try:
        dados = request.get_json()
        
        if not dados or 'matches' not in dados:
            return jsonify({
                'success': False,
                'error': 'Lista de matches é obrigatória'
            }), 400
        
        matches = dados['matches']
        if not matches:
            return jsonify({
                'success': False,
                'error': 'Nenhum match selecionado'
            }), 400
        
        print(f"🔄 Processando conciliação de {len(matches)} matches...")
        
        resultados = []
        sucessos = 0
        erros = 0
        
        for i, match in enumerate(matches):
            try:
                print(f"   📝 [{i+1}/{len(matches)}] Conciliando match...")
                
                # Extrair dados do match
                transacao_ofx = match.get('ofx', {})
                movimento_omie = match.get('omie', {})
                criterio = match.get('criterio', 'unknown')
                confianca = match.get('confianca', 0.0)
                
                if not transacao_ofx or not movimento_omie:
                    raise ValueError("Dados de transação OFX ou movimento Omie ausentes")
                
                # Obter dados necessários para conciliação
                codigo_lancamento = movimento_omie.get('codigo_lancamento', '')
                numero_documento = movimento_omie.get('documento', '')
                valor = float(movimento_omie.get('valor', 0))
                
                print(f"      🎯 Conciliando: Código {codigo_lancamento}, Doc {numero_documento}, Valor R$ {valor:.2f}")
                
                # Implementar chamada real para API do Omie para marcar como conciliado
                sucesso_conciliacao = _conciliar_lancamento_omie(
                    codigo_lancamento=codigo_lancamento,
                    numero_documento=numero_documento
                )
                
                if sucesso_conciliacao:
                    resultados.append({
                        'index': i,
                        'success': True,
                        'codigo_lancamento': codigo_lancamento,
                        'numero_documento': numero_documento,
                        'valor': valor,
                        'criterio': criterio,
                        'message': f'Conciliado com sucesso (critério: {criterio})'
                    })
                    sucessos += 1
                    print(f"      ✅ Conciliado com sucesso")
                else:
                    raise Exception("Falha na conciliação no Omie")
                
            except Exception as e:
                erro_msg = str(e)
                print(f"      ❌ Erro: {erro_msg}")
                
                resultados.append({
                    'index': i,
                    'success': False,
                    'error': erro_msg,
                    'codigo_lancamento': movimento_omie.get('codigo_lancamento', ''),
                    'numero_documento': movimento_omie.get('documento', ''),
                    'valor': float(movimento_omie.get('valor', 0))
                })
                erros += 1
        
        # Resultado final
        taxa_sucesso = (sucessos / len(matches)) * 100 if matches else 0
        
        print(f"✅ Conciliação finalizada: {sucessos} sucessos, {erros} erros ({taxa_sucesso:.1f}% sucesso)")
        
        return jsonify({
            'success': True,
            'total_processados': len(matches),
            'sucessos': sucessos,
            'erros': erros,
            'taxa_sucesso': taxa_sucesso,
            'resultados': resultados,
            'message': f'Processados {len(matches)} matches: {sucessos} sucessos, {erros} erros'
        })
        
    except Exception as e:
        print(f"❌ Erro geral na conciliação: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/incluir-lancamentos', methods=['POST'])
def api_incluir_lancamentos():
    """API para incluir lançamentos sem match no Omie"""
    try:
        dados = request.get_json()
        
        if not dados or 'lancamentos' not in dados:
            return jsonify({
                'success': False,
                'error': 'Lista de lançamentos é obrigatória'
            }), 400
        
        lancamentos = dados['lancamentos']
        if not lancamentos:
            return jsonify({
                'success': False,
                'error': 'Nenhum lançamento selecionado'
            }), 400
        
        print(f"💰 Processando inclusão de {len(lancamentos)} lançamentos...")
        
        resultados = []
        sucessos = 0
        erros = 0
        
        for i, lancamento in enumerate(lancamentos):
            try:
                print(f"   📝 [{i+1}/{len(lancamentos)}] Incluindo lançamento...")
                
                # Extrair dados do lançamento
                transacao = lancamento.get('transacao', {})
                categoria = lancamento.get('categoria', '')
                cliente = lancamento.get('cliente', '')
                
                if not transacao:
                    raise ValueError("Dados de transação ausentes")
                
                if not categoria:
                    raise ValueError("Categoria é obrigatória")
                
                # Obter dados da transação
                data = transacao.get('data', '')
                valor = float(transacao.get('valor', 0))
                descricao = transacao.get('descricao', '')
                numero_documento = transacao.get('numero_documento', '')
                
                print(f"      💸 Incluindo: {descricao[:50]}... - R$ {valor:.2f} - {categoria}")
                
                # Implementar chamada real para API do Omie para incluir lançamento
                sucesso_inclusao = _incluir_lancamento_omie(
                    data=data,
                    valor=valor,
                    descricao=descricao,
                    categoria=categoria,
                    cliente=cliente,
                    numero_documento=numero_documento
                )
                
                if sucesso_inclusao:
                    resultados.append({
                        'index': i,
                        'success': True,
                        'data': data,
                        'valor': valor,
                        'descricao': descricao,
                        'categoria': categoria,
                        'cliente': cliente,
                        'numero_documento': numero_documento,
                        'codigo_lancamento': sucesso_inclusao if isinstance(sucesso_inclusao, int) else None,
                        'message': f'Lançamento incluído com sucesso (Código: {sucesso_inclusao})'
                    })
                    sucessos += 1
                    print(f"      ✅ Incluído com sucesso (Código: {sucesso_inclusao})")
                else:
                    raise Exception("Falha na inclusão no Omie")
                
            except Exception as e:
                erro_msg = str(e)
                print(f"      ❌ Erro: {erro_msg}")
                
                resultados.append({
                    'index': i,
                    'success': False,
                    'error': erro_msg,
                    'data': transacao.get('data', ''),
                    'valor': float(transacao.get('valor', 0)),
                    'descricao': transacao.get('descricao', ''),
                    'categoria': categoria,
                    'cliente': cliente
                })
                erros += 1
        
        # Resultado final
        taxa_sucesso = (sucessos / len(lancamentos)) * 100 if lancamentos else 0
        
        print(f"✅ Inclusão finalizada: {sucessos} sucessos, {erros} erros ({taxa_sucesso:.1f}% sucesso)")
        
        return jsonify({
            'success': True,
            'total_processados': len(lancamentos),
            'sucessos': sucessos,
            'erros': erros,
            'taxa_sucesso': taxa_sucesso,
            'resultados': resultados,
            'message': f'Processados {len(lancamentos)} lançamentos: {sucessos} sucessos, {erros} erros'
        })
        
    except Exception as e:
        print(f"❌ Erro geral na inclusão: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

def _incluir_lancamento_omie(data, valor, descricao, categoria, cliente, numero_documento):
    """Inclui um lançamento na conta corrente do Omie usando a estrutura oficial da API"""
    try:
        # Converter data para formato DD/MM/YYYY
        if isinstance(data, str) and '-' in data:  # formato YYYY-MM-DD
            parts = data.split('-')
            data_formatada = f"{parts[2]}/{parts[1]}/{parts[0]}"
        else:
            data_formatada = data
        
        # Gerar código interno único para o lançamento
        import time
        codigo_interno = f"CONC_{int(time.time())}"
        
        # Estrutura OFICIAL conforme documentação Omie
        dados_lancamento = {
            "cCodIntLanc": codigo_interno,
            "cabecalho": {
                "nCodCC": 2103553430,  # Código da conta corrente (usar a conta padrão)
                "dDtLanc": data_formatada,
                "nValorLanc": abs(float(valor))
            },
            "detalhes": {
                "cCodCateg": categoria if categoria else "1.01.01",  # Categoria obrigatória
                "cTipo": "DIN"  # Tipo documento: DIN = Dinheiro
            }
        }
        
        # Campos opcionais nos detalhes
        if descricao:
            dados_lancamento["detalhes"]["cObs"] = descricao[:500]  # Observações
        
        # Número do documento (ID do OFX truncado para facilitar conciliação)
        if numero_documento:
            # Truncar o ID do OFX para os primeiros 20 caracteres (limite do campo)
            doc_truncado = str(numero_documento)[:20]
            dados_lancamento["detalhes"]["cNumDoc"] = doc_truncado
            print(f"      📄 Documento adicionado: {doc_truncado}")
        
        # Cliente - buscar código pelo nome ou usar código diretamente
        if cliente:
            codigo_cliente = None
            
            if cliente.isdigit():
                # Se é numérico, usar diretamente
                codigo_cliente = int(cliente)
            else:
                # Buscar cliente pelo nome no cache ou API
                try:
                    if clientes_fornecedores_cache['data']:
                        # Buscar no cache primeiro
                        for contato in clientes_fornecedores_cache['data']:
                            if (contato.get('nome', '').upper() == cliente.upper() or 
                                contato.get('nome', '').upper().startswith(cliente.upper()[:10])):
                                codigo_cliente = contato.get('codigo')
                                print(f"      👤 Cliente encontrado no cache: {cliente} -> código {codigo_cliente}")
                                break
                    
                    if not codigo_cliente:
                        print(f"      ⚠️ Cliente '{cliente}' não encontrado no cache")
                
                except Exception as e:
                    print(f"      ⚠️ Erro ao buscar cliente: {e}")
            
            if codigo_cliente:
                dados_lancamento["detalhes"]["nCodCliente"] = codigo_cliente
                print(f"      👤 Cliente adicionado ao lançamento: {codigo_cliente}")
            else:
                print(f"      ⚠️ Cliente '{cliente}' não será incluído (código não encontrado)")
        
        print(f"      🔥 Dados para Omie: {dados_lancamento}")
        
        # Inicializar cliente Omie
        omie_client = OmieClient(
            app_key=os.getenv('OMIE_APP_KEY'),
            app_secret=os.getenv('OMIE_APP_SECRET')
        )
        
        # Chamar API do Omie para incluir lançamento (método correto)
        resultado = omie_client.omie._chamar_api(
            call='IncluirLancCC',
            endpoint='financas/contacorrentelancamentos/',
            param=dados_lancamento
        )
        
        print(f"      📡 Resposta Omie: {resultado}")
        
        # Verificar se a inclusão foi bem-sucedida (baseado no teste real da API)
        if isinstance(resultado, dict) and 'nCodLanc' in resultado and 'cCodStatus' in resultado:
            codigo_status = resultado.get('cCodStatus')
            if codigo_status == '0':  # Status 0 = sucesso
                codigo_lancamento = resultado.get('nCodLanc')
                print(f"      ✅ Lançamento incluído com código: {codigo_lancamento}")
                print(f"      📝 Status: {resultado.get('cDesStatus', 'N/A')}")
                
                # 🤖 APRENDIZADO ML: Adicionar dados para melhoria contínua
                try:
                    # Buscar nome da categoria pelo código
                    categoria_nome = None
                    if categoria and categorias_cache['data']:
                        for cat in categorias_cache['data']:
                            if cat.get('codigo') == categoria:
                                categoria_nome = cat.get('descricao', '')
                                break
                    
                    # Buscar nome do cliente pelo código
                    cliente_nome = None
                    if cliente and clientes_fornecedores_cache['data']:
                        for contato in clientes_fornecedores_cache['data']:
                            if contato.get('nome', '').upper() == cliente.upper():
                                cliente_nome = contato.get('nome', '')
                                break
                    
                    # Limpar descrição para o ML (mesmo processamento usado na predição)
                    descricao_limpa = descricao.lower()
                    import re
                    descricao_limpa = re.sub(r'[^\w\s]', ' ', descricao_limpa)
                    descricao_limpa = ' '.join(descricao_limpa.split())
                    
                    # Adicionar aos dados de aprendizado
                    ml_categorizer.add_learning_data(
                        description=descricao,
                        clean_description=descricao_limpa,
                        amount=float(valor),
                        category_id=categoria,
                        category_name=categoria_nome,
                        client_supplier_id=cliente,
                        client_supplier_name=cliente_nome
                    )
                    
                    print(f"      🧠 Dados adicionados ao ML para aprendizado contínuo")
                    
                except Exception as e:
                    print(f"      ⚠️ Erro no aprendizado ML (não crítico): {e}")
                
                # 🎯 CONCILIAÇÃO AUTOMÁTICA: Marcar lançamento como conciliado
                try:
                    print(f"      🎯 Conciliando automaticamente lançamento {codigo_lancamento}...")
                    sucesso_conciliacao = _conciliar_lancamento_omie(
                        codigo_lancamento=codigo_lancamento,
                        numero_documento=numero_documento
                    )
                    
                    if sucesso_conciliacao:
                        print(f"      ✅ Lançamento conciliado automaticamente")
                    else:
                        print(f"      ⚠️ Falha na conciliação automática (não crítico)")
                        
                except Exception as e:
                    print(f"      ⚠️ Erro na conciliação automática (não crítico): {e}")
                
                return codigo_lancamento  # Retornar código para futura conciliação
            else:
                print(f"      ❌ Erro na inclusão: {resultado.get('cDesStatus', 'Erro desconhecido')}")
                return False
        else:
            print(f"      ❌ Resposta inesperada do Omie: {resultado}")
            return False
            
    except Exception as e:
        print(f"      ❌ Erro ao incluir lançamento no Omie: {e}")
        return False

def _conciliar_lancamento_omie(codigo_lancamento, numero_documento):
    """Marca um lançamento como conciliado no Omie seguindo o padrão manual"""
    try:
        if not codigo_lancamento:
            print(f"      ⚠️ Código de lançamento não informado")
            return False
        
        print(f"      🔄 Conciliando lançamento código: {codigo_lancamento}")
        
        # Inicializar cliente Omie
        omie_client = OmieClient(
            app_key=os.getenv('OMIE_APP_KEY'),
            app_secret=os.getenv('OMIE_APP_SECRET')
        )
        
        # Primeiro, consultar o lançamento para obter dados atuais
        consulta_params = {
            "nCodLanc": int(codigo_lancamento)
        }
        
        consulta_resultado = omie_client.omie._chamar_api(
            call='ConsultaLancCC',
            endpoint='financas/contacorrentelancamentos/',
            param=consulta_params
        )
        
        print(f"      📋 Consulta resultado: {type(consulta_resultado)}")
        
        if not isinstance(consulta_resultado, dict):
            print(f"      ❌ Lançamento não encontrado: {codigo_lancamento}")
            return False
        
        # Preparar dados para alteração conforme estrutura descoberta
        # Os campos de conciliação estão no objeto 'diversos'
        from datetime import datetime
        agora = datetime.now()
        data_hoje = agora.strftime('%d/%m/%Y')
        hora_agora = agora.strftime('%H:%M:%S')
        
        # Converter resultado da consulta para dict se necessário
        if hasattr(consulta_resultado, 'get'):
            dados_alteracao = dict(consulta_resultado)
        else:
            dados_alteracao = consulta_resultado
        
        # Garantir que o objeto diversos existe e é um dict
        if 'diversos' not in dados_alteracao or dados_alteracao['diversos'] is None:
            dados_alteracao['diversos'] = {}
        elif hasattr(dados_alteracao['diversos'], 'get'):
            # Converter CaseInsensitiveDict para dict normal
            dados_alteracao['diversos'] = dict(dados_alteracao['diversos'])
        
        # Atualizar campos de conciliação dentro de 'diversos'
        dados_alteracao['diversos']['dDtConc'] = data_hoje   # Data da conciliação
        dados_alteracao['diversos']['cHrConc'] = hora_agora  # Hora da conciliação
        dados_alteracao['diversos']['cUsConc'] = 'SISTEMA'   # Usuário responsável
        
        # Garantir que o código do lançamento está correto
        dados_alteracao['nCodLanc'] = int(codigo_lancamento)
        
        print(f"      🔧 Atualizando campos de conciliação em 'diversos':")
        print(f"         - diversos.dDtConc: '{data_hoje}'")
        print(f"         - diversos.cHrConc: '{hora_agora}'")
        print(f"         - diversos.cUsConc: 'SISTEMA'")
        print(f"      🎯 Estrutura correta conforme descoberta na API")
        
        # Chamar API do Omie para alterar o lançamento (método correto)
        resultado = omie_client.omie._chamar_api(
            call='AlterarLancCC',
            endpoint='financas/contacorrentelancamentos/',
            param=dados_alteracao
        )
        
        print(f"      📡 Resposta conciliação: {resultado}")
        
        # Verificar se a alteração foi bem-sucedida
        if isinstance(resultado, dict) and ('codigo_lancamento' in resultado or 'nCodLancamento' in resultado):
            print(f"      ✅ Lançamento {codigo_lancamento} conciliado seguindo padrão do Omie")
            return True
        elif isinstance(resultado, str) and 'sucesso' in resultado.lower():
            print(f"      ✅ Lançamento {codigo_lancamento} conciliado com sucesso")
            return True
        else:
            print(f"      ❌ Falha na conciliação: {resultado}")
            return False
            
    except Exception as e:
        print(f"      ❌ Erro ao conciliar lançamento no Omie: {e}")
        return False

# ============================================================
# ROTAS B2B - DASHBOARD DE VENDAS
# ============================================================

@app.route('/dashboard-b2b')
def dashboard_b2b():
    """Dashboard B2B para análise de vendas"""
    return render_template('b2b_dashboard.html')


@app.route('/crm/leads')
def crm_leads_page():
    """Página principal do CRM B2B"""
    return render_template(
        'crm_leads.html',
        stage_options=crm_service.stage_options(),
    )


@app.route('/crm/api/leads', methods=['GET', 'POST'])
def crm_leads_api():
    """API para criar e listar leads do CRM"""
    try:
        if request.method == 'POST':
            payload = request.get_json(force=True)
            if not payload or not payload.get('name'):
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400

            lead_id = crm_service.create_lead(
                name=payload.get('name', '').strip(),
                category=payload.get('category'),
                city=payload.get('city'),
                state=payload.get('state'),
                country=payload.get('country'),
                source=payload.get('source'),
                owner=payload.get('owner'),
                whatsapp=payload.get('whatsapp'),
                phone=payload.get('phone'),
                email=payload.get('email'),
                instagram=payload.get('instagram'),
                website=payload.get('website'),
                primary_contact_name=payload.get('primary_contact_name'),
                notes=payload.get('notes'),
                address_line=payload.get('address_line'),
                address_number=payload.get('address_number'),
                address_complement=payload.get('address_complement'),
                neighborhood=payload.get('neighborhood'),
                postal_code=payload.get('postal_code'),
                latitude=payload.get('latitude'),
                longitude=payload.get('longitude'),
                status=payload.get('status'),
                google_place_id=payload.get('google_place_id'),
                search_keyword=payload.get('search_keyword'),
                search_city=payload.get('search_city'),
            )

            return jsonify({'success': True, 'lead_id': lead_id}), 201

        # GET - Buscar por ID específico ou listar com filtros
        lead_id = request.args.get('lead_id', type=int)
        if lead_id:
            lead = crm_service.get_lead(lead_id)
            if not lead:
                return jsonify({'success': False, 'error': 'Lead não encontrado'}), 404
            return jsonify({'success': True, 'leads': [lead]})

        leads = crm_service.list_leads(
            status=request.args.get('status') or None,
            owner=request.args.get('owner') or None,
            city=request.args.get('city') or None,
            country=request.args.get('country') or None,
            is_customer=None,
            search=request.args.get('search') or None,
            limit=int(request.args.get('limit', 200)),
            offset=int(request.args.get('offset', 0))
        )

        return jsonify({'success': True, 'leads': leads})

    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/crm/api/leads/<int:lead_id>', methods=['PATCH', 'DELETE'])
def crm_lead_detail_api(lead_id: int):
    """Atualiza ou remove um lead específico"""
    try:
        if request.method == 'PATCH':
            payload = request.get_json(force=True) or {}
            crm_service.update_lead(lead_id, **payload)
            return jsonify({'success': True})

        crm_service.delete_lead(lead_id)
        return jsonify({'success': True})

    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/crm/api/leads/<int:lead_id>/interactions', methods=['GET', 'POST'])
def crm_lead_interactions_api(lead_id: int):
    """Lista ou cria interações/comentários de um lead"""
    try:
        if request.method == 'POST':
            payload = request.get_json(force=True) or {}
            comment = payload.get('notes') or payload.get('comment')
            # Usar automaticamente o usuário logado como responsável
            owner = current_user.username if current_user.is_authenticated else 'Sistema'
            crm_service.add_comment(lead_id, comment, owner=owner)
            interactions = crm_service.list_interactions(lead_id)
            return jsonify({'success': True, 'interactions': interactions}), 201

        limit = request.args.get('limit', default=200, type=int)
        limit = max(1, min(limit, 500))
        interactions = crm_service.list_interactions(lead_id, limit=limit)
        return jsonify({'success': True, 'interactions': interactions})

    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/crm/api/leads/discover')
def crm_leads_discover_api():
    """Busca leads via Google Maps/Places"""
    if not google_maps_client:
        return jsonify({'success': False, 'error': 'GOOGLE_API_KEY não configurada'}), 400

    keyword = request.args.get('keyword', '').strip()
    city = request.args.get('city', '').strip()
    state = request.args.get('state', '').strip()
    country = request.args.get('country', '').strip()
    fetch_details = request.args.get('fetch_details', 'false').lower() == 'true'

    if not keyword or not city:
        return jsonify({'success': False, 'error': 'Informe keyword e cidade'}), 400

    query_parts = [keyword, city, state, country]
    query = ' '.join(part for part in query_parts if part)

    region = state.lower() if state else None
    if not region and country:
        region_map = {
            'brasil': 'br',
            'argentina': 'ar',
            'paraguai': 'py',
        }
        region = region_map.get(country.lower())

    try:
        raw = google_maps_client.text_search(query=query, region=region)
        status = raw.get('status', 'UNKNOWN')
        if status not in ('OK', 'ZERO_RESULTS'):
            return jsonify({'success': False, 'error': raw.get('error_message', status)}), 400

        results = raw.get('results', [])
        leads = google_maps_client.parse_results(keyword, results, city, fetch_details=fetch_details)

        if country:
            for lead in leads:
                lead.setdefault('country', country)

        # Enriquecer leads com dados adicionais (Instagram, WhatsApp via scraping)
        enrich = request.args.get('enrich', 'false').lower() == 'true'
        if enrich:
            print(f"🔍 Enriquecendo {len(leads)} leads...")
            leads = lead_enrichment_service.enrich_batch(leads, google_maps_client, delay_seconds=0.5)

        return jsonify({'success': True, 'results': leads, 'status': status})

    except requests.HTTPError as exc:
        return jsonify({'success': False, 'error': f'HTTP error: {exc}'}), 502
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

@app.route('/crm/api/leads/<int:lead_id>/enrich', methods=['POST'])
def crm_lead_enrich_api(lead_id: int):
    """Enriquece um lead com dados adicionais (Instagram, WhatsApp, etc)"""
    try:
        payload = request.get_json(force=True) or {}

        # Permitir atualização manual de dados sociais
        enrichment_data = {}
        if 'instagram' in payload:
            enrichment_data['instagram'] = payload['instagram']
        if 'whatsapp' in payload:
            enrichment_data['whatsapp'] = payload['whatsapp']
        if 'phone' in payload:
            enrichment_data['phone'] = payload['phone']
            # Se tem telefone e não tem WhatsApp, sugerir o mesmo número
            if 'whatsapp' not in payload and payload.get('phone'):
                enrichment_data['whatsapp'] = payload['phone']

        if enrichment_data:
            crm_service.update_lead(lead_id, **enrichment_data)

        return jsonify({'success': True, 'updated_fields': list(enrichment_data.keys())})

    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

@app.route('/api/b2b/dashboard')
def api_b2b_dashboard():
    """API principal para dados do dashboard B2B"""
    try:
        if not sales_analyzer:
            return jsonify({
                'success': False,
                'error': 'Módulo B2B não disponível'
            })
        
        month = request.args.get('month')
        dashboard_data = sales_analyzer.get_dashboard_data(reference_month=month)
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/b2b/resumo-vendas')
def api_b2b_resumo_vendas():
    """API para obter resumo de vendas B2B"""
    try:
        month = request.args.get('mes')
        if month:
            dashboard = sales_analyzer.get_dashboard_data(reference_month=month)
            return jsonify({
                'success': True,
                'data': dashboard.get('summary', {})
            })

        period_days = int(request.args.get('periodo', 30))
        resumo = sales_analyzer.get_sales_summary(period_days)
        
        return jsonify({
            'success': True,
            'data': resumo
        })
        
    except Exception as e:
        print(f"❌ Erro no resumo de vendas B2B: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/b2b/clientes-inativos')
def api_b2b_clientes_inativos():
    """API para obter lista de clientes inativos"""
    try:
        days_threshold = int(request.args.get('dias', 60))
        clientes_inativos = client_manager.get_inactive_clients(days_threshold)
        
        return jsonify({
            'success': True,
            'clientes_inativos': clientes_inativos,
            'total': len(clientes_inativos),
            'threshold_days': days_threshold
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar clientes inativos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/b2b/cliente/<client_id>')
def api_b2b_cliente_detalhes(client_id):
    """API para obter detalhes de um cliente específico"""
    try:
        detalhes = client_manager.get_client_details(client_id)
        
        return jsonify({
            'success': True,
            'data': detalhes
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar detalhes do cliente {client_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/b2b/previsao-vendas')
def api_b2b_previsao_vendas():
    """API para obter previsão de vendas"""
    try:
        months_ahead = int(request.args.get('meses', 3))
        previsao = sales_analyzer.get_sales_forecast(months_ahead)
        
        return jsonify({
            'success': True,
            'data': previsao
        })
        
    except Exception as e:
        print(f"❌ Erro na previsão de vendas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/b2b/status-integracao')
def api_b2b_status_integracao():
    """API para verificar status das integrações B2B"""
    try:
        try:
            order_service.list_orders(limit=1)
            database_status = {'connected': True, 'status': 'Conectado'}
        except Exception as exc:
            database_status = {'connected': False, 'status': f'Erro: {exc}'}
        
        return jsonify({
            'success': True,
            'integrations': {
                'database': database_status,
                'omie_api': {
                    'connected': omie_client is not None,
                    'status': 'Conectado' if omie_client else 'Desconectado'
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/b2b/cache/limpar')
def api_b2b_limpar_cache():
    """API para limpar cache dos dados B2B"""
    try:
        sales_analyzer.clear_cache()

        return jsonify({
            'success': True,
            'message': 'Cache B2B limpo com sucesso'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# ============================================================
# ROTAS ADMINISTRATIVAS
# ============================================================

@app.route('/admin/fix-sequences')
def admin_fix_sequences():
    """Fix PostgreSQL sequences for auto-increment columns"""
    try:
        from sqlalchemy import text

        # Only works with PostgreSQL
        if engine.dialect.name != 'postgresql':
            return jsonify({
                'success': False,
                'error': f'This tool only works with PostgreSQL. Current dialect: {engine.dialect.name}'
            })

        tables_to_fix = [
            'coffee_products',
            'coffee_packaging_prices',
            'orders',
            'order_items',
            'crm_users',
            'crm_leads',
            'crm_interactions',
        ]

        results = []

        with engine.connect() as conn:
            for table_name in tables_to_fix:
                try:
                    sequence_name = f"{table_name}_id_seq"

                    # Get current max ID
                    result = conn.execute(text(f"SELECT MAX(id) FROM {table_name}"))
                    max_id = result.scalar()

                    if max_id is None:
                        max_id = 0

                    # Set sequence to max_id + 1
                    next_val = max_id + 1
                    conn.execute(text(f"SELECT setval('{sequence_name}', {next_val}, false)"))

                    # Verify new sequence value
                    result = conn.execute(text(f"SELECT last_value FROM {sequence_name}"))
                    new_val = result.scalar()

                    results.append({
                        'table': table_name,
                        'success': True,
                        'max_id': max_id,
                        'new_sequence_value': int(new_val),
                        'next_id': int(new_val)
                    })

                except Exception as e:
                    results.append({
                        'table': table_name,
                        'success': False,
                        'error': str(e)
                    })

            conn.commit()

        success_count = sum(1 for r in results if r.get('success'))

        return jsonify({
            'success': True,
            'message': f'Fixed {success_count}/{len(tables_to_fix)} sequences',
            'results': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    # Criar diretórios necessários se não existem
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)

    # Porta para Railway (usa PORT do ambiente) ou local
    port = int(os.environ.get('PORT', 5002))

    print("🚀 Iniciando Sistema Web de Gestão Financeira")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"💰 Extrato PJ: http://localhost:{port}/extrato-pj")
    print(f"🏢 Dashboard B2B: http://localhost:{port}/dashboard-b2b")

    # Para Railway: não usar debug em produção
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') is not None
    app.run(debug=not is_production, host='0.0.0.0', port=port)
