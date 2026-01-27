"""Blueprint for CRM and B2B dashboard routes."""

from __future__ import annotations

from typing import Optional

import requests
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from .b2b.crm_service import CRMService
from .b2b.google_maps_client import GoogleMapsClient
from .b2b.lead_enrichment import LeadEnrichmentService
from .b2b.sales_analyzer import SalesAnalyzer
from .b2b.sales_repository import SalesRepository
from .services.exchange_rate_service import ExchangeRateService
from .services.order_service import OrderService


def create_crm_blueprint(
    crm_service: CRMService,
    google_maps_client: Optional[GoogleMapsClient],
    lead_enrichment_service: LeadEnrichmentService,
    sales_analyzer: Optional[SalesAnalyzer],
    sales_repository: Optional[SalesRepository],
    exchange_rate_service: ExchangeRateService,
    order_service: OrderService,
    auth_service,
) -> Blueprint:
    """Create blueprint for CRM and B2B routes."""
    bp = Blueprint('crm', __name__)

    # ==========================
    # CRM Pages
    # ==========================

    @bp.route('/crm/leads')
    @login_required
    def crm_leads_page():
        """Pagina principal do CRM B2B"""
        users = auth_service.get_all_active_users()
        return render_template(
            'crm_leads.html',
            stage_options=crm_service.stage_options(),
            users=users,
        )

    # ==========================
    # CRM API Routes
    # ==========================

    @bp.route('/crm/api/leads', methods=['GET', 'POST'])
    @login_required
    def crm_leads_api():
        """API para criar e listar leads do CRM"""
        try:
            if request.method == 'POST':
                payload = request.get_json(force=True)
                if not payload or not payload.get('name'):
                    return jsonify({'success': False, 'error': 'Nome e obrigatorio'}), 400

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

            # GET - Buscar por ID especifico ou listar com filtros
            lead_id = request.args.get('lead_id', type=int)
            if lead_id:
                lead = crm_service.get_lead(lead_id)
                if not lead:
                    return jsonify({'success': False, 'error': 'Lead nao encontrado'}), 404
                return jsonify({'success': True, 'leads': [lead]})

            # Vendedor ve apenas seus proprios leads
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

    @bp.route('/crm/api/leads/<int:lead_id>', methods=['PATCH', 'DELETE'])
    @login_required
    def crm_lead_detail_api(lead_id: int):
        """Atualiza ou remove um lead especifico"""
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

    @bp.route('/crm/api/leads/<int:lead_id>/interactions', methods=['GET', 'POST'])
    @login_required
    def crm_lead_interactions_api(lead_id: int):
        """Lista ou cria interacoes/comentarios de um lead"""
        try:
            if request.method == 'POST':
                payload = request.get_json(force=True) or {}
                comment = payload.get('notes') or payload.get('comment')
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

    @bp.route('/crm/api/leads/discover')
    @login_required
    def crm_leads_discover_api():
        """
        Busca leads via Google Maps/Places.

        Parâmetros:
            keyword: Termo de busca (ex: "cafeteria", "padaria")
            city: Cidade para buscar
            state: Estado (opcional)
            country: País (opcional)
            fetch_details: Se 'true', busca telefone/website via Place Details API
                          (custo adicional, mas dados mais completos)

        Nota: O enriquecimento (Instagram, WhatsApp) agora é feito sob demanda
              via endpoint /crm/api/leads/<id>/enrich-full para economizar custos.
        """
        if not google_maps_client:
            return jsonify({'success': False, 'error': 'GOOGLE_API_KEY nao configurada'}), 400

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

            # Enriquecimento em batch removido para economizar custos
            # Use /crm/api/leads/<id>/enrich-full para enriquecer leads individuais

            cache_stats = google_maps_client.get_cache_stats()
            return jsonify({
                'success': True,
                'results': leads,
                'status': status,
                'cache_stats': cache_stats,
                'tip': 'Use fetch_details=true para obter telefone/website. Enriquecimento completo disponível ao salvar o lead.'
            })

        except requests.HTTPError as exc:
            return jsonify({'success': False, 'error': f'HTTP error: {exc}'}), 502
        except Exception as exc:
            return jsonify({'success': False, 'error': str(exc)}), 500

    @bp.route('/crm/api/leads/<int:lead_id>/enrich', methods=['POST'])
    @login_required
    def crm_lead_enrich_api(lead_id: int):
        """Enriquece um lead com dados fornecidos manualmente (Instagram, WhatsApp, etc)"""
        try:
            payload = request.get_json(force=True) or {}

            enrichment_data = {}
            if 'instagram' in payload:
                enrichment_data['instagram'] = payload['instagram']
            if 'whatsapp' in payload:
                enrichment_data['whatsapp'] = payload['whatsapp']
            if 'phone' in payload:
                enrichment_data['phone'] = payload['phone']
                if 'whatsapp' not in payload and payload.get('phone'):
                    enrichment_data['whatsapp'] = payload['phone']

            if enrichment_data:
                crm_service.update_lead(lead_id, **enrichment_data)

            return jsonify({'success': True, 'updated_fields': list(enrichment_data.keys())})

        except Exception as exc:
            return jsonify({'success': False, 'error': str(exc)}), 500

    @bp.route('/crm/api/leads/<int:lead_id>/enrich-full', methods=['POST'])
    @login_required
    def crm_lead_enrich_full_api(lead_id: int):
        """
        Enriquecimento completo de um lead específico (sob demanda).

        Este endpoint busca dados adicionais como Instagram e WhatsApp
        via scraping do Google Business Profile e website do estabelecimento.

        Custos:
            - Place Details API: ~$0.017 por chamada (se necessário)
            - Scraping: Grátis (mas mais lento)

        O enriquecimento é feito sob demanda para economizar custos,
        ao invés de enriquecer todos os leads em batch na busca.
        """
        try:
            lead = crm_service.get_lead(lead_id)
            if not lead:
                return jsonify({'success': False, 'error': 'Lead não encontrado'}), 404

            # Preparar dados para enriquecimento
            lead_data = {
                'name': lead.get('name'),
                'place_id': lead.get('google_place_id'),
                'website': lead.get('website'),
                'phone': lead.get('phone'),
                'city': lead.get('city'),
                '_details_fetched': bool(lead.get('phone') and lead.get('website')),
            }

            # Executar enriquecimento
            print(f"🔍 Enriquecendo lead #{lead_id}: {lead.get('name')}")
            enriched = lead_enrichment_service.enrich_lead(
                lead_data,
                google_maps_client=google_maps_client,
                skip_api_calls=False
            )

            # Extrair apenas campos que podem ser atualizados
            update_data = {}
            updatable_fields = ['phone', 'website', 'instagram', 'whatsapp']
            for field in updatable_fields:
                if enriched.get(field) and not lead.get(field):
                    update_data[field] = enriched[field]

            # Atualizar lead se houver novos dados
            if update_data:
                crm_service.update_lead(lead_id, **update_data)
                print(f"✅ Lead #{lead_id} atualizado com: {list(update_data.keys())}")

            return jsonify({
                'success': True,
                'updated_fields': list(update_data.keys()),
                'enriched_data': {k: enriched.get(k) for k in updatable_fields},
                'instagram_suggestion': enriched.get('instagram_suggestion'),
            })

        except Exception as exc:
            print(f"❌ Erro ao enriquecer lead #{lead_id}: {exc}")
            return jsonify({'success': False, 'error': str(exc)}), 500

    @bp.route('/crm/api/leads/enrich-discovery', methods=['POST'])
    @login_required
    def crm_leads_enrich_discovery_api():
        """
        Enriquece um lead da busca (ainda não salvo) antes de salvar.

        Recebe os dados do lead da busca e retorna os dados enriquecidos.
        Útil para preview antes de salvar no CRM.
        """
        try:
            lead_data = request.get_json(force=True) or {}

            if not lead_data.get('name'):
                return jsonify({'success': False, 'error': 'Dados do lead são obrigatórios'}), 400

            print(f"🔍 Enriquecendo lead da busca: {lead_data.get('name')}")
            enriched = lead_enrichment_service.enrich_lead(
                lead_data,
                google_maps_client=google_maps_client,
                skip_api_calls=False
            )

            return jsonify({
                'success': True,
                'enriched_data': enriched,
                'instagram_suggestion': enriched.get('instagram_suggestion'),
            })

        except Exception as exc:
            return jsonify({'success': False, 'error': str(exc)}), 500

    # ==========================
    # B2B Dashboard Routes
    # ==========================

    @bp.route('/dashboard-b2b')
    @login_required
    def dashboard_b2b():
        """Dashboard B2B para analise de vendas"""
        return render_template('b2b_dashboard.html')

    @bp.route('/api/b2b/dashboard')
    @login_required
    def api_b2b_dashboard():
        """API principal para dados do dashboard B2B"""
        try:
            if not sales_analyzer:
                return jsonify({
                    'success': False,
                    'error': 'Modulo B2B nao disponivel'
                })

            month = request.args.get('month')
            user_id = None
            if current_user.is_authenticated and current_user.is_seller:
                user_id = current_user.id

            target_currency = 'BRL'
            if current_user.is_authenticated:
                target_currency = getattr(current_user, 'native_currency', 'BRL') or 'BRL'

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

    @bp.route('/api/b2b/resumo-vendas')
    @login_required
    def api_b2b_resumo_vendas():
        """API para obter resumo de vendas B2B"""
        try:
            if not sales_analyzer:
                return jsonify({
                    'success': False,
                    'error': 'Modulo B2B nao disponivel'
                })

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
            print(f"Erro no resumo de vendas B2B: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            })

    @bp.route('/api/b2b/clientes-inativos')
    @login_required
    def api_b2b_clientes_inativos():
        """API para obter lista de clientes inativos"""
        return jsonify({
            'success': True,
            'clientes_inativos': [],
            'total': 0,
            'message': 'Funcionalidade em desenvolvimento'
        })

    @bp.route('/api/b2b/cliente/<client_id>')
    @login_required
    def api_b2b_cliente_detalhes(client_id):
        """API para obter detalhes de um cliente especifico"""
        return jsonify({
            'success': False,
            'error': 'Funcionalidade em desenvolvimento'
        })

    @bp.route('/api/b2b/previsao-vendas')
    @login_required
    def api_b2b_previsao_vendas():
        """API para obter previsao de vendas"""
        try:
            if not sales_analyzer:
                return jsonify({
                    'success': False,
                    'error': 'Modulo B2B nao disponivel'
                })

            months_ahead = int(request.args.get('meses', 3))
            previsao = sales_analyzer.get_sales_forecast(months_ahead)

            return jsonify({
                'success': True,
                'data': previsao
            })

        except Exception as e:
            print(f"Erro na previsao de vendas: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            })

    @bp.route('/api/b2b/status-integracao')
    @login_required
    def api_b2b_status_integracao():
        """API para verificar status das integracoes B2B"""
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

    @bp.route('/api/b2b/cache/limpar')
    @login_required
    def api_b2b_limpar_cache():
        """API para limpar cache dos dados B2B"""
        try:
            if sales_analyzer:
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

    return bp


__all__ = ['create_crm_blueprint']
