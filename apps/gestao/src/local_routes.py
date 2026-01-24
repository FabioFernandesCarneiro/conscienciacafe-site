"""Blueprint for local data routes (database without Omie integration)."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta

from flask import Blueprint, jsonify, render_template, request

from .local_data_service import LocalDataService


def create_local_blueprint(local_service: LocalDataService) -> Blueprint:
    """Create blueprint for local data routes."""
    bp = Blueprint('local', __name__)

    @bp.route('/local')
    @bp.route('/local/dashboard')
    def dashboard_local():
        """Dashboard da versao local (sem Omie)"""
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

    @bp.route('/local/extrato-pj')
    def extrato_pj_local():
        """Tela de extrato para a versao local"""
        return render_template('extrato_pj_local.html')

    @bp.route('/api/local/contas-disponiveis')
    def api_local_contas_disponiveis():
        """API para listar contas disponiveis no banco local"""
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

    @bp.route('/api/local/extrato-conta-corrente')
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
                    'error': 'Parametro conta_id e obrigatorio'
                }), 400

            if not data_inicio or not data_fim:
                hoje = date.today()
                data_fim_obj = hoje
                data_inicio_obj = hoje - timedelta(days=30)
                data_inicio = data_inicio_obj.strftime('%d/%m/%Y')
                data_fim = data_fim_obj.strftime('%d/%m/%Y')

            print(f"[LOCAL] Buscando extrato da conta ID: {conta_id} de {data_inicio} a {data_fim}")

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
                'error': 'Parametro conta_id deve ser numerico'
            }), 400
        except Exception as exc:
            print(f"[LOCAL] Erro ao buscar extrato: {exc}")
            return jsonify({
                'success': False,
                'error': f'Erro ao carregar extrato local: {exc}'
            }), 500

    @bp.route('/api/local/categorias')
    def api_local_categorias():
        """API para listar categorias disponiveis no banco local"""
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

    @bp.route('/api/local/clientes-fornecedores')
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

    @bp.route('/api/local/estatisticas-banco')
    def api_local_estatisticas_banco():
        """API para estatisticas do banco de dados local"""
        try:
            stats = local_service.get_database_statistics()
            return jsonify({
                'success': True,
                'estatisticas': stats
            })
        except Exception as exc:
            return jsonify({
                'success': False,
                'error': f'Erro ao obter estatisticas: {exc}'
            })

    @bp.route('/api/local/buscar-transacoes')
    def api_local_buscar_transacoes():
        """API para buscar transacoes no banco local"""
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
                'error': 'Parametro conta_id deve ser numerico'
            }), 400
        except Exception as exc:
            return jsonify({
                'success': False,
                'error': f'Erro na busca: {exc}'
            }), 500

    @bp.route('/api/local/status-migracao')
    def api_local_status_migracao():
        """API para verificar status da migracao em execucao"""
        try:
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

    return bp


__all__ = ['create_local_blueprint']
