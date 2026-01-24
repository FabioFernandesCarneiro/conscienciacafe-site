"""Blueprint for legacy routes (Omie integration disabled).

These routes maintain backward compatibility with old API clients
while returning appropriate error messages indicating that the
Omie integration has been disabled.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template

# Cache structures maintained for backward compatibility
_contas_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 3600
}

_categorias_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 7200
}

_clientes_fornecedores_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 3600
}


def create_legacy_blueprint() -> Blueprint:
    """Create blueprint for legacy/disabled Omie routes."""
    bp = Blueprint('legacy', __name__)

    # ==========================
    # Extrato PJ (Legacy)
    # ==========================

    @bp.route('/extrato-pj')
    def extrato_pj():
        """Tela de extrato das contas pessoa juridica"""
        return render_template('extrato_pj.html')

    @bp.route('/api/extrato-conta-corrente')
    def api_extrato_conta_corrente():
        """API para obter extrato de conta corrente (funcionalidade Omie removida)"""
        return jsonify({
            'success': False,
            'error': 'Integracao Omie desativada. Use /api/local/extrato-conta-corrente para dados locais.',
            'extrato': [],
            'resumo': {}
        })

    @bp.route('/api/contas-disponiveis')
    def api_contas_disponiveis():
        """API para listar contas disponiveis (funcionalidade Omie removida)"""
        return jsonify({
            'success': True,
            'contas': [],
            'message': 'Integracao Omie desativada'
        })

    # ==========================
    # Cache Management (Legacy)
    # ==========================

    @bp.route('/api/contas-cache/limpar')
    def api_limpar_cache_contas():
        """API para limpar cache de contas (forcar nova consulta)"""
        global _contas_cache
        _contas_cache = {
            'data': None,
            'timestamp': 0,
            'cache_duration': 3600
        }

        return jsonify({
            'success': True,
            'message': 'Cache de contas limpo com sucesso'
        })

    @bp.route('/api/cache/limpar-todos')
    def api_limpar_todos_caches():
        """API para limpar todos os caches"""
        global _contas_cache, _categorias_cache, _clientes_fornecedores_cache

        _contas_cache = {
            'data': None,
            'timestamp': 0,
            'cache_duration': 3600
        }

        _categorias_cache = {
            'data': None,
            'timestamp': 0,
            'cache_duration': 7200
        }

        _clientes_fornecedores_cache = {
            'data': None,
            'timestamp': 0,
            'cache_duration': 3600
        }

        return jsonify({
            'success': True,
            'message': 'Todos os caches foram limpos com sucesso'
        })

    # ==========================
    # Categorias (Legacy)
    # ==========================

    @bp.route('/api/categorias-omie')
    def api_categorias_omie():
        """API para listar categorias (funcionalidade Omie removida)"""
        return jsonify({
            'success': True,
            'categorias': [],
            'message': 'Integracao Omie desativada'
        })

    # ==========================
    # Clientes/Fornecedores (Legacy)
    # ==========================

    @bp.route('/api/criar-cliente', methods=['POST'])
    def criar_cliente():
        """API para criar cliente (funcionalidade Omie removida)"""
        return jsonify({
            'success': False,
            'error': 'Integracao Omie desativada'
        }), 501

    @bp.route('/api/clientes-fornecedores')
    def api_clientes_fornecedores():
        """API para listar clientes/fornecedores (funcionalidade Omie removida)"""
        return jsonify({
            'success': True,
            'clientes_fornecedores': [],
            'message': 'Integracao Omie desativada'
        })

    # ==========================
    # Conciliacao (Legacy)
    # ==========================

    @bp.route('/api/conciliar', methods=['POST'])
    def api_conciliar():
        """API para conciliacao de arquivo OFX (funcionalidade Omie removida)"""
        return jsonify({
            'success': False,
            'error': 'Integracao Omie desativada. Funcionalidade de conciliacao nao disponivel.'
        }), 501

    @bp.route('/api/conciliar-matches', methods=['POST'])
    def api_conciliar_matches():
        """API para conciliar matches (funcionalidade Omie removida)"""
        return jsonify({
            'success': False,
            'error': 'Integracao Omie desativada'
        }), 501

    @bp.route('/api/incluir-lancamentos', methods=['POST'])
    def api_incluir_lancamentos():
        """API para incluir lancamentos (funcionalidade Omie removida)"""
        return jsonify({
            'success': False,
            'error': 'Integracao Omie desativada'
        }), 501

    return bp


def get_categorias_cache():
    """Get the categorias cache for external use."""
    return _categorias_cache


__all__ = ['create_legacy_blueprint', 'get_categorias_cache']
