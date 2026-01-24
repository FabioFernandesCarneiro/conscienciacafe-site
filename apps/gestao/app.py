#!/usr/bin/env python3
"""Sistema Web de Gestão Financeira - Consciência Café."""

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from datetime import datetime, date, timedelta
import os
import requests
import logging
from dotenv import load_dotenv
from flask_login import LoginManager, current_user
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

# Importar módulos B2B (inicialização adiada para após exchange_rate_service)
try:
    from src.b2b.sales_analyzer import SalesAnalyzer
    from src.b2b.sales_repository import SalesRepository
    _b2b_modules_loaded = True
except ImportError as e:
    logger.warning("Erro ao carregar módulos B2B: %s", e)
    _b2b_modules_loaded = False
    sales_analyzer = None

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
        auth_service,
    )
)

# Registrar blueprints de comissões e câmbio
from src.services.commission_service import CommissionService
from src.services.commission_rate_service import CommissionRateService
from src.services.exchange_rate_service import ExchangeRateService
from src.commission_routes import create_commission_blueprint
from src.exchange_routes import create_exchange_blueprint

commission_rate_service = CommissionRateService()
exchange_rate_service = ExchangeRateService()
commission_service = CommissionService(commission_rate_service, exchange_rate_service)

app.register_blueprint(create_commission_blueprint(commission_service, commission_rate_service))
app.register_blueprint(create_exchange_blueprint(exchange_rate_service))

# Inicializar analisadores B2B (após exchange_rate_service estar disponível)
if _b2b_modules_loaded:
    sales_repository = SalesRepository(exchange_rate_service=exchange_rate_service)
    sales_analyzer = SalesAnalyzer(sales_repository, crm_service)
    print("✅ Módulos B2B carregados com sucesso")
else:
    sales_analyzer = None


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
    """API para obter extrato de conta corrente (funcionalidade Omie removida)"""
    return jsonify({
        'success': False,
        'error': 'Integração Omie desativada. Use /api/local/extrato-conta-corrente para dados locais.',
        'extrato': [],
        'resumo': {}
    })

@app.route('/api/contas-disponiveis')
def api_contas_disponiveis():
    """API para listar contas disponíveis (funcionalidade Omie removida)"""
    return jsonify({
        'success': True,
        'contas': [],
        'message': 'Integração Omie desativada'
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
    """API para listar categorias (funcionalidade Omie removida)"""
    return jsonify({
        'success': True,
        'categorias': [],
        'message': 'Integração Omie desativada'
    })

@app.route('/api/criar-cliente', methods=['POST'])
def criar_cliente():
    """API para criar cliente (funcionalidade Omie removida)"""
    return jsonify({
        'success': False,
        'error': 'Integração Omie desativada'
    }), 501

@app.route('/api/clientes-fornecedores')
def api_clientes_fornecedores():
    """API para listar clientes/fornecedores (funcionalidade Omie removida)"""
    return jsonify({
        'success': True,
        'clientes_fornecedores': [],
        'message': 'Integração Omie desativada'
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
    """API para conciliação de arquivo OFX (funcionalidade Omie removida)"""
    return jsonify({
        'success': False,
        'error': 'Integração Omie desativada. Funcionalidade de conciliação não disponível.'
    }), 501

@app.route('/api/conciliar-matches', methods=['POST'])
def api_conciliar_matches():
    """API para conciliar matches (funcionalidade Omie removida)"""
    return jsonify({
        'success': False,
        'error': 'Integração Omie desativada'
    }), 501


@app.route('/api/incluir-lancamentos', methods=['POST'])
def api_incluir_lancamentos():
    """API para incluir lançamentos (funcionalidade Omie removida)"""
    return jsonify({
        'success': False,
        'error': 'Integração Omie desativada'
    }), 501

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
    # Lista de usuários para admin selecionar responsável
    users = auth_service.get_all_active_users()
    return render_template(
        'crm_leads.html',
        stage_options=crm_service.stage_options(),
        users=users,
    )


@app.route('/crm/api/leads', methods=['GET', 'POST'])
def crm_leads_api():
    """API para criar e listar leads do CRM"""
    try:
        if request.method == 'POST':
            payload = request.get_json(force=True)
            if not payload or not payload.get('name'):
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400

            # Determinar user_id: vendedor é automaticamente ele, admin pode escolher
            user_id = None
            if current_user.is_authenticated:
                if current_user.is_seller:
                    user_id = current_user.id
                elif current_user.is_admin and payload.get('user_id'):
                    user_id = payload.get('user_id')

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
                user_id=user_id,
            )

            return jsonify({'success': True, 'lead_id': lead_id}), 201

        # GET - Buscar por ID específico ou listar com filtros
        lead_id = request.args.get('lead_id', type=int)
        if lead_id:
            lead = crm_service.get_lead(lead_id)
            if not lead:
                return jsonify({'success': False, 'error': 'Lead não encontrado'}), 404
            return jsonify({'success': True, 'leads': [lead]})

        # Vendedor vê apenas seus próprios leads
        user_id = None
        if current_user.is_authenticated and current_user.is_seller:
            user_id = current_user.id

        leads = crm_service.list_leads(
            status=request.args.get('status') or None,
            owner=request.args.get('owner') or None,
            city=request.args.get('city') or None,
            country=request.args.get('country') or None,
            is_customer=None,
            search=request.args.get('search') or None,
            limit=int(request.args.get('limit', 200)),
            offset=int(request.args.get('offset', 0)),
            user_id=user_id,
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
        if not _b2b_modules_loaded:
            return jsonify({
                'success': False,
                'error': 'Módulo B2B não disponível'
            })

        month = request.args.get('month')
        # Vendedor vê apenas seus próprios dados
        user_id = None
        if current_user.is_authenticated and current_user.is_seller:
            user_id = current_user.id

        # Determinar moeda alvo baseado no usuário
        target_currency = 'BRL'
        if current_user.is_authenticated:
            target_currency = getattr(current_user, 'native_currency', 'BRL') or 'BRL'

        # Criar analyzer com a moeda do usuário
        user_repository = SalesRepository(
            exchange_rate_service=exchange_rate_service,
            target_currency=target_currency
        )
        user_analyzer = SalesAnalyzer(user_repository, crm_service, target_currency=target_currency)

        dashboard_data = user_analyzer.get_dashboard_data(reference_month=month, user_id=user_id)

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
        # Vendedor vê apenas seus próprios dados
        user_id = None
        if current_user.is_authenticated and current_user.is_seller:
            user_id = current_user.id

        month = request.args.get('mes')
        if month:
            dashboard = sales_analyzer.get_dashboard_data(reference_month=month, user_id=user_id)
            return jsonify({
                'success': True,
                'data': dashboard.get('summary', {})
            })

        period_days = int(request.args.get('periodo', 30))
        resumo = sales_analyzer.get_sales_summary(period_days, user_id=user_id)
        
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
    # Funcionalidade removida - dependia de client_manager (Omie)
    return jsonify({
        'success': True,
        'clientes_inativos': [],
        'total': 0,
        'message': 'Funcionalidade em desenvolvimento'
    })


@app.route('/api/b2b/cliente/<client_id>')
def api_b2b_cliente_detalhes(client_id):
    """API para obter detalhes de um cliente específico"""
    # Funcionalidade removida - dependia de client_manager (Omie)
    return jsonify({
        'success': False,
        'error': 'Funcionalidade em desenvolvimento'
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
                'database': database_status
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
