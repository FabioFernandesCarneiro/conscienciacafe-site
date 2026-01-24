"""Blueprint for ML-powered intelligent suggestions routes."""

from __future__ import annotations

from typing import Optional

from flask import Blueprint, jsonify, request

from .ml_categorizer import MLCategorizer, clean_description_for_ml, extract_name_from_description
from .legacy_routes import get_categorias_cache


def create_ml_blueprint(ml_categorizer: MLCategorizer) -> Blueprint:
    """Create blueprint for ML suggestion routes."""
    bp = Blueprint('ml', __name__)

    def _find_category_code_by_name(category_name: str) -> Optional[str]:
        """Find category code by name from cache."""
        cache = get_categorias_cache()
        if not cache['data']:
            return None

        for categoria in cache['data']:
            if categoria['descricao'].lower() == category_name.lower():
                return categoria['codigo']

        return None

    def _find_first_category_by_type(category_type: str) -> Optional[str]:
        """Find first category of the specified type."""
        cache = get_categorias_cache()
        if not cache['data']:
            return None

        for categoria in cache['data']:
            if categoria['tipo'] == category_type:
                return categoria['codigo']

        return None

    @bp.route('/api/sugestoes-inteligentes', methods=['POST'])
    def api_sugestoes_inteligentes():
        """API para gerar sugestoes inteligentes usando ML"""
        try:
            data = request.get_json()
            if not data or 'transacoes' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Dados de transacoes sao obrigatorios'
                })

            print(f"Gerando sugestoes inteligentes para {len(data['transacoes'])} transacoes...")

            sugestoes = []

            for transacao in data['transacoes']:
                descricao = transacao.get('descricao', '')
                valor = float(transacao.get('valor', 0))

                clean_description = clean_description_for_ml(descricao)

                categoria_ml, confianca = ml_categorizer.predict_category(
                    descricao, clean_description, abs(valor)
                )

                similares = ml_categorizer.suggest_similar_transactions(clean_description, limit=3)

                categoria_sugerida = ''
                cliente_sugerido = ''
                confianca_final = 0.0

                if categoria_ml and confianca > 0.5:
                    categoria_sugerida = categoria_ml
                    confianca_final = confianca
                    print(f"   ML: {categoria_ml} (confianca: {confianca:.2f})")

                if similares:
                    melhor_similar = max(similares, key=lambda x: x['frequency'])
                    if melhor_similar['category']:
                        categoria_codigo = _find_category_code_by_name(melhor_similar['category'])
                        if categoria_codigo:
                            categoria_sugerida = categoria_codigo
                            confianca_final = max(confianca_final, 0.8)

                    if melhor_similar['client_supplier']:
                        cliente_sugerido = melhor_similar['client_supplier']
                        confianca_final += 0.1

                    print(f"   Historico: {melhor_similar['category']} | {melhor_similar['client_supplier']} (freq: {melhor_similar['frequency']})")

                if not categoria_sugerida:
                    if valor > 0:
                        categoria_sugerida = _find_first_category_by_type('R')
                    else:
                        categoria_sugerida = _find_first_category_by_type('D')
                    confianca_final = 0.3

                if not cliente_sugerido:
                    cliente_sugerido = extract_name_from_description(descricao) or 'A definir'

                fonte = 'ml' if categoria_ml else 'historico' if similares else 'fallback'
                sugestoes.append({
                    'categoria': categoria_sugerida,
                    'cliente': cliente_sugerido,
                    'confianca': min(confianca_final, 1.0),
                    'fonte': fonte
                })

            return jsonify({
                'success': True,
                'sugestoes': sugestoes,
                'stats': ml_categorizer.get_learning_stats()
            })

        except Exception as e:
            print(f"Erro nas sugestoes inteligentes: {e}")
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}',
                'sugestoes': []
            })

    return bp


__all__ = ['create_ml_blueprint']
