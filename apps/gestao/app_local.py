#!/usr/bin/env python3
"""
Sistema Web de Gestão Financeira - Versão Local
Aplicação Flask usando dados locais (SQLite) ao invés do Omie
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime, date, timedelta
import os
import tempfile
from dotenv import load_dotenv
from src.local_data_service import LocalDataService
import time

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Serviço de dados locais (força modo SQLite)
local_service = LocalDataService(use_sqlalchemy=False)

@app.route('/')
def dashboard():
    """Dashboard principal"""
    try:
        # Obter estatísticas do banco local
        stats = local_service.get_database_statistics()

        # Contas disponíveis
        accounts = local_service.get_available_accounts()

        # Informações da última migração
        migration_info = stats.get('last_migration', {})

        return render_template('dashboard_local.html',
                             stats=stats,
                             accounts=accounts,
                             migration_info=migration_info)
    except Exception as e:
        return render_template('dashboard_local.html',
                             error=f"Erro ao carregar dashboard: {str(e)}",
                             stats={},
                             accounts=[],
                             migration_info={})

@app.route('/extrato-pj')
def extrato_pj():
    """Página de extrato pessoa jurídica"""
    return render_template('extrato_pj_local.html')

# ============ APIs LOCAIS ============

@app.route('/api/contas-disponiveis')
def api_contas_disponiveis_local():
    """API para listar contas disponíveis (dados locais)"""
    try:
        contas = local_service.get_available_accounts()

        return jsonify({
            'success': True,
            'contas': contas,
            'fonte': 'local_database',
            'total': len(contas)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar contas locais: {str(e)}',
            'contas': []
        })

@app.route('/api/extrato-conta-corrente')
def api_extrato_conta_corrente_local():
    """API para obter extrato usando dados locais"""
    try:
        # Parâmetros da requisição
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        conta_id = request.args.get('conta_id')
        pagina = int(request.args.get('pagina', 1))

        if not conta_id:
            return jsonify({
                'success': False,
                'error': 'Parâmetro conta_id é obrigatório'
            })

        # Se não informar datas, usar últimos 30 dias
        if not data_inicio or not data_fim:
            hoje = date.today()
            data_fim_obj = hoje
            data_inicio_obj = hoje - timedelta(days=30)
            data_inicio = data_inicio_obj.strftime('%d/%m/%Y')
            data_fim = data_fim_obj.strftime('%d/%m/%Y')

        print(f"🔧 [LOCAL] Buscando extrato da conta ID: {conta_id} de {data_inicio} a {data_fim}")

        # Usar serviço local
        result = local_service.get_account_statement(
            account_id=int(conta_id),
            start_date=data_inicio,
            end_date=data_fim,
            page=pagina
        )

        if result['success']:
            print(f"✅ [LOCAL] {len(result['extrato'])} movimentos encontrados")
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        print(f"❌ [LOCAL] Erro ao buscar extrato: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro ao carregar extrato local: {str(e)}'
        }), 500

@app.route('/api/categorias-omie')
def api_categorias_local():
    """API para listar categorias (dados locais)"""
    try:
        categorias = local_service.get_categories()

        return jsonify({
            'success': True,
            'categorias': categorias,
            'fonte': 'local_database',
            'total': len(categorias)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar categorias locais: {str(e)}',
            'categorias': []
        })

@app.route('/api/clientes-fornecedores')
def api_clientes_fornecedores_local():
    """API para listar clientes e fornecedores (dados locais)"""
    try:
        clientes_fornecedores = local_service.get_clients_suppliers()

        return jsonify({
            'success': True,
            'clientes_fornecedores': clientes_fornecedores,
            'fonte': 'local_database',
            'total': len(clientes_fornecedores)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar clientes/fornecedores locais: {str(e)}',
            'clientes_fornecedores': []
        })

@app.route('/api/estatisticas-banco')
def api_estatisticas_banco():
    """API para estatísticas do banco de dados local"""
    try:
        stats = local_service.get_database_statistics()

        return jsonify({
            'success': True,
            'estatisticas': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter estatísticas: {str(e)}'
        })

@app.route('/api/buscar-transacoes')
def api_buscar_transacoes():
    """API para buscar transações por texto"""
    try:
        query = request.args.get('q', '')
        conta_id = request.args.get('conta_id')
        limit = int(request.args.get('limit', 50))

        if not query or len(query) < 3:
            return jsonify({
                'success': False,
                'error': 'Query deve ter pelo menos 3 caracteres'
            })

        account_id = int(conta_id) if conta_id else None
        transacoes = local_service.search_transactions(query, account_id, limit)

        return jsonify({
            'success': True,
            'transacoes': transacoes,
            'total': len(transacoes)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro na busca: {str(e)}'
        })

@app.route('/api/resumo-mensal')
def api_resumo_mensal():
    """API para resumo mensal de transações"""
    try:
        year = int(request.args.get('ano', date.today().year))
        conta_id = request.args.get('conta_id')

        account_id = int(conta_id) if conta_id else None
        resumo = local_service.get_monthly_summary(year, account_id)

        return jsonify({
            'success': True,
            'resumo_mensal': resumo,
            'ano': year
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter resumo mensal: {str(e)}'
        })

@app.route('/api/status-migracao')
def api_status_migracao():
    """API para verificar status da migração"""
    try:
        import json
        import os

        status_file = "data/migration_status.json"
        pid_file = "data/migration.pid"

        status_info = {
            'migration_running': False,
            'pid': None,
            'last_status': None
        }

        # Verificar se migração está rodando
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            try:
                os.kill(pid, 0)  # Verificar se processo existe
                status_info['migration_running'] = True
                status_info['pid'] = pid
            except OSError:
                status_info['migration_running'] = False
                os.remove(pid_file)  # Remover PID órfão

        # Ler último status
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status_info['last_status'] = json.load(f)

        # Adicionar estatísticas do banco
        status_info['database_stats'] = local_service.get_database_statistics()

        return jsonify({
            'success': True,
            'status': status_info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao verificar status: {str(e)}'
        })

# ============ ROTAS DE ADMINISTRAÇÃO ============

@app.route('/admin')
def admin():
    """Página de administração"""
    try:
        stats = local_service.get_database_statistics()
        return render_template('admin_local.html', stats=stats)
    except Exception as e:
        return render_template('admin_local.html',
                             error=f"Erro ao carregar admin: {str(e)}")

@app.route('/api/iniciar-migracao', methods=['POST'])
def api_iniciar_migracao():
    """API para iniciar nova migração"""
    try:
        import subprocess
        import os

        # Verificar se já há migração rodando
        pid_file = "data/migration.pid"
        if os.path.exists(pid_file):
            return jsonify({
                'success': False,
                'error': 'Migração já está em execução'
            })

        # Iniciar migração em background
        process = subprocess.Popen([
            'bash', 'start_migration.sh'
        ], cwd=os.getcwd())

        return jsonify({
            'success': True,
            'message': 'Migração iniciada em background',
            'pid': process.pid
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao iniciar migração: {str(e)}'
        })

# ============ FALLBACK PARA OMIE (OPCIONAL) ============

@app.route('/api/modo-operacao')
def api_modo_operacao():
    """Retorna modo de operação atual"""
    try:
        stats = local_service.get_database_statistics()
        has_data = stats.get('total_transactions', 0) > 0

        return jsonify({
            'success': True,
            'modo': 'local' if has_data else 'omie',
            'dados_locais': has_data,
            'estatisticas': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao verificar modo: {str(e)}',
            'modo': 'error'
        })

if __name__ == '__main__':
    print("🚀 Sistema Web de Gestão Financeira - Versão Local")
    print("=" * 60)

    # Verificar se há dados locais
    try:
        stats = local_service.get_database_statistics()
        print(f"🏦 Contas: {stats.get('total_accounts', 0)}")
        print(f"💰 Transações: {stats.get('total_transactions', 0)}")
        print(f"👥 Clientes: {stats.get('total_clients', 0)}")

        if stats.get('total_transactions', 0) > 0:
            print("✅ Dados locais disponíveis - Modo LOCAL ativo")
        else:
            print("⚠️ Sem dados locais - Execute migração primeiro")

    except Exception as e:
        print(f"❌ Erro ao verificar dados: {e}")

    print(f"🌐 Acessível em: http://localhost:5003")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5003, debug=True)
