"""Blueprint for coffee catalog and orders management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .services.catalog_service import CatalogService, PACKAGE_SIZES
from .services.order_service import OrderService
from .b2b.crm_service import CRMService
from .b2b.google_sheets_client import GoogleSheetsClient
from .b2b.lead_enrichment import LeadEnrichmentService
from .b2b.google_maps_client import GoogleMapsClient


def _parse_brazilian_number(value: str) -> float:
    """Parse Brazilian number format (1.234,56 -> 1234.56)."""
    # Remove thousand separators (dots) and replace decimal comma with dot
    normalized = value.strip().replace('.', '').replace(',', '.')
    return float(normalized)


def _parse_price_form(form) -> Dict[str, Dict[str, float]]:
    """Parse price form fields for BRL and PYG currencies."""
    prices: Dict[str, Dict[str, float]] = {'BRL': {}, 'PYG': {}}

    for size in PACKAGE_SIZES:
        # Parse BRL prices
        brl_value = form.get(f'price_brl_{size}')
        if brl_value:
            try:
                prices['BRL'][size] = _parse_brazilian_number(brl_value)
            except ValueError:
                raise ValueError(f'Preço BRL inválido para {size}')

        # Parse PYG prices
        pyg_value = form.get(f'price_pyg_{size}')
        if pyg_value:
            try:
                prices['PYG'][size] = _parse_brazilian_number(pyg_value)
            except ValueError:
                raise ValueError(f'Preço PYG inválido para {size}')

        # Fallback: legacy format (price_{size})
        legacy_value = form.get(f'price_{size}')
        if legacy_value and size not in prices['BRL']:
            try:
                prices['BRL'][size] = _parse_brazilian_number(legacy_value)
            except ValueError:
                raise ValueError(f'Preço inválido para {size}')

    return prices


def create_orders_blueprint(
    catalog_service: CatalogService,
    order_service: OrderService,
    crm_service: CRMService,
    google_sheets_client: GoogleSheetsClient,
    lead_enrichment_service: LeadEnrichmentService,
    google_maps_client: Optional[GoogleMapsClient] = None,
    auth_service=None,
) -> Blueprint:
    bp = Blueprint('orders', __name__, url_prefix='/orders')

    def _require_admin() -> bool:
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acesso restrito a administradores.', 'danger')
            return False
        return True

    def _normalize_name(name: Optional[str]) -> Optional[str]:
        return name.strip().lower() if isinstance(name, str) else None

    def _parse_number(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        candidate = str(value).strip()
        if not candidate:
            return None
        candidate = candidate.replace('R$', '').replace(' ', '')
        if candidate.count(',') == 1 and candidate.count('.') > 1:
            candidate = candidate.replace('.', '')
        candidate = candidate.replace(',', '.')
        try:
            return float(candidate)
        except ValueError:
            return None

    def _to_date(value: Any) -> Optional[date]:
        if isinstance(value, date):
            return value
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value)).date()
        except ValueError:
            return None

    # ARCHIVED: Helper functions for import feature were removed (2025-10-10)
    # Original code preserved in: Consciencia_Cafe/olds/
    # Functions that were here: _find_existing_lead, _discover_lead_payload, _ensure_lead_simple

    def _mark_lead_as_customer(lead_id: Optional[int]) -> None:
        if not lead_id:
            return
        try:
            crm_service.update_lead(int(lead_id), status='cliente', is_customer=True)
        except Exception as exc:
            print(f"⚠️ Erro ao atualizar lead {lead_id} para cliente: {exc}")

    def _extract_order_form_data(form, *, require_date: bool = False) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        order_data: Dict[str, Any] = {
            'lead_id': form.get('lead_id') or None,
            'client_id': None,
            'order_date': form.get('order_date') or None,
            'currency': form.get('currency') or 'BRL',
            'notes': form.get('notes', '').strip() or None,
            'source': form.get('source', '').strip() or None,
        }
        if order_data['lead_id']:
            try:
                order_data['lead_id'] = int(order_data['lead_id'])
            except ValueError:
                order_data['lead_id'] = None

        if require_date and not order_data['order_date']:
            raise ValueError('Informe a data do pedido.')

        item_coffee = form.getlist('item_coffee_id')
        item_package = form.getlist('item_package_size')
        item_quantity = form.getlist('item_quantity')
        item_unit_price = form.getlist('item_unit_price')

        rows = len(item_quantity)
        items: List[Dict[str, Any]] = []
        for idx in range(rows):
            quantity_raw = item_quantity[idx].strip() if idx < len(item_quantity) else ''
            unit_price_raw = item_unit_price[idx].strip() if idx < len(item_unit_price) else ''
            if not quantity_raw or not unit_price_raw:
                continue
            try:
                quantity = float(quantity_raw.replace(',', '.'))
                unit_price = float(unit_price_raw.replace(',', '.'))
            except ValueError:
                raise ValueError('Quantidade ou preço inválido em um dos itens.')

            coffee_raw = item_coffee[idx] if idx < len(item_coffee) else ''
            package_size = item_package[idx] if idx < len(item_package) else ''

            coffee_id: Optional[int] = None
            if coffee_raw:
                try:
                    coffee_id = int(coffee_raw)
                except ValueError:
                    coffee_id = None

            items.append({
                'coffee_id': coffee_id,
                'description': None,
                'package_size': package_size or None,
                'quantity': quantity,
                'unit_price': unit_price,
            })

        if not items:
            raise ValueError('Informe ao menos um item válido.')

        return order_data, items

    def _order_state_from_form(form) -> Dict[str, Any]:
        state: Dict[str, Any] = {
            'lead_id': form.get('lead_id') or None,
            'order_date': form.get('order_date') or None,
            'currency': form.get('currency') or 'BRL',
            'notes': form.get('notes', '').strip() or None,
            'source': form.get('source', '').strip() or None,
        }
        items: List[Dict[str, Any]] = []
        item_coffee = form.getlist('item_coffee_id')
        item_package = form.getlist('item_package_size')
        item_quantity = form.getlist('item_quantity')
        item_unit_price = form.getlist('item_unit_price')

        rows = max(len(item_coffee), len(item_package), len(item_quantity), len(item_unit_price))
        for idx in range(rows):
            coffee_raw = item_coffee[idx] if idx < len(item_coffee) else ''
            package_raw = item_package[idx] if idx < len(item_package) else ''
            quantity_raw = item_quantity[idx] if idx < len(item_quantity) else ''
            unit_price_raw = item_unit_price[idx] if idx < len(item_unit_price) else ''

            coffee_id: Optional[int] = None
            if coffee_raw:
                try:
                    coffee_id = int(coffee_raw)
                except ValueError:
                    coffee_id = None

            items.append({
                'coffee_id': coffee_id,
                'package_size': package_raw or None,
                'quantity': quantity_raw,
                'unit_price': unit_price_raw,
            })

        state['items'] = items
        total_amount = 0.0
        for item in items:
            try:
                quantity_val = float((item.get('quantity') or '').replace(',', '.'))
                price_val = float((item.get('unit_price') or '').replace(',', '.'))
            except (ValueError, AttributeError):
                continue
            total_amount += quantity_val * price_val
        if total_amount > 0:
            state['total_amount'] = total_amount
        return state

    @bp.route('/coffees')
    @login_required
    def coffees_index():
        coffees = catalog_service.list_coffees(include_inactive=True)
        return render_template('orders/coffees_list.html', coffees=coffees, package_sizes=PACKAGE_SIZES)

    @bp.route('/coffees/new', methods=['GET', 'POST'])
    @login_required
    def coffees_new():
        if not _require_admin():
            return redirect(url_for('orders.coffees_index'))
        if request.method == 'POST':
            data = {
                'name': request.form.get('name', '').strip(),
                'variety': request.form.get('variety', '').strip() or None,
                'farm_name': request.form.get('farm_name', '').strip() or None,
                'region': request.form.get('region', '').strip() or None,
                'process': request.form.get('process', '').strip() or None,
                'sensorial_notes': request.form.get('sensorial_notes', '').strip() or None,
                'sca_score': request.form.get('sca_score') or None,
                'active': True,
            }
            if data['sca_score']:
                try:
                    data['sca_score'] = float(data['sca_score'].replace(',', '.'))
                except ValueError:
                    flash('Pontuação SCA inválida.', 'danger')
                    return render_template('orders/coffees_form.html', coffee={**data, 'prices_map': {}}, package_sizes=PACKAGE_SIZES)
            try:
                prices = _parse_price_form(request.form)
                if not prices:
                    flash('Informe pelo menos um preço de embalagem.', 'danger')
                    return render_template('orders/coffees_form.html', coffee={**data, 'prices_map': {}}, package_sizes=PACKAGE_SIZES)
                catalog_service.create_coffee(data, prices)
            except ValueError as exc:
                flash(str(exc), 'danger')
                return render_template('orders/coffees_form.html', coffee={**data, 'prices_map': prices}, package_sizes=PACKAGE_SIZES)

            flash('Café cadastrado com sucesso!', 'success')
            return redirect(url_for('orders.coffees_index'))

        return render_template('orders/coffees_form.html', coffee=None, package_sizes=PACKAGE_SIZES)

    @bp.route('/coffees/<int:coffee_id>/edit', methods=['GET', 'POST'])
    @login_required
    def coffees_edit(coffee_id: int):
        if not _require_admin():
            return redirect(url_for('orders.coffees_index'))
        coffee = catalog_service.get_coffee(coffee_id)
        if not coffee:
            flash('Café não encontrado.', 'danger')
            return redirect(url_for('orders.coffees_index'))

        if request.method == 'POST':
            data = {
                'name': request.form.get('name', '').strip(),
                'variety': request.form.get('variety', '').strip() or None,
                'farm_name': request.form.get('farm_name', '').strip() or None,
                'region': request.form.get('region', '').strip() or None,
                'process': request.form.get('process', '').strip() or None,
                'sensorial_notes': request.form.get('sensorial_notes', '').strip() or None,
                'sca_score': request.form.get('sca_score') or None,
                'active': 'active' in request.form,
            }
            if data['sca_score']:
                try:
                    data['sca_score'] = float(data['sca_score'].replace(',', '.'))
                except ValueError:
                    flash('Pontuação SCA inválida.', 'danger')
                    coffee.update(data)
                    return render_template('orders/coffees_form.html', coffee=coffee, package_sizes=PACKAGE_SIZES)
            try:
                prices = _parse_price_form(request.form)
                if not prices:
                    flash('Informe pelo menos um preço de embalagem.', 'danger')
                    coffee.update(data)
                    coffee['prices_map'] = prices
                    return render_template('orders/coffees_form.html', coffee=coffee, package_sizes=PACKAGE_SIZES)
                catalog_service.update_coffee(coffee_id, data, prices)
            except ValueError as exc:
                flash(str(exc), 'danger')
                coffee.update(data)
                coffee['prices_map'] = prices
                return render_template('orders/coffees_form.html', coffee=coffee, package_sizes=PACKAGE_SIZES)

            flash('Café atualizado com sucesso!', 'success')
            return redirect(url_for('orders.coffees_index'))

        return render_template('orders/coffees_form.html', coffee=coffee, package_sizes=PACKAGE_SIZES)

    @bp.route('/coffees/<int:coffee_id>/duplicate', methods=['GET', 'POST'])
    @login_required
    def coffees_duplicate(coffee_id: int):
        if not _require_admin():
            return redirect(url_for('orders.coffees_index'))
        original_coffee = catalog_service.get_coffee(coffee_id)
        if not original_coffee:
            flash('Café não encontrado.', 'danger')
            return redirect(url_for('orders.coffees_index'))

        if request.method == 'POST':
            data = {
                'name': request.form.get('name', '').strip(),
                'variety': request.form.get('variety', '').strip() or None,
                'farm_name': request.form.get('farm_name', '').strip() or None,
                'region': request.form.get('region', '').strip() or None,
                'process': request.form.get('process', '').strip() or None,
                'sensorial_notes': request.form.get('sensorial_notes', '').strip() or None,
                'sca_score': request.form.get('sca_score') or None,
                'active': True,
            }
            if data['sca_score']:
                try:
                    data['sca_score'] = float(data['sca_score'].replace(',', '.'))
                except ValueError:
                    flash('Pontuação SCA inválida.', 'danger')
                    return render_template('orders/coffees_form.html', coffee={**data, 'prices_map': {}}, package_sizes=PACKAGE_SIZES, is_duplicate=True)
            try:
                prices = _parse_price_form(request.form)
                if not prices:
                    flash('Informe pelo menos um preço de embalagem.', 'danger')
                    return render_template('orders/coffees_form.html', coffee={**data, 'prices_map': {}}, package_sizes=PACKAGE_SIZES, is_duplicate=True)
                catalog_service.create_coffee(data, prices)
            except ValueError as exc:
                flash(str(exc), 'danger')
                return render_template('orders/coffees_form.html', coffee={**data, 'prices_map': prices}, package_sizes=PACKAGE_SIZES, is_duplicate=True)

            flash('Café duplicado com sucesso!', 'success')
            return redirect(url_for('orders.coffees_index'))

        # Pre-fill form with original coffee data but suggest a new name
        duplicate_coffee = {
            'name': f"{original_coffee.get('name', '')} (Cópia)",
            'variety': original_coffee.get('variety'),
            'farm_name': original_coffee.get('farm_name'),
            'region': original_coffee.get('region'),
            'process': original_coffee.get('process'),
            'sensorial_notes': original_coffee.get('sensorial_notes'),
            'sca_score': original_coffee.get('sca_score'),
            'prices_map_brl': original_coffee.get('prices_map_brl', {}),
            'prices_map_pyg': original_coffee.get('prices_map_pyg', {}),
        }
        return render_template('orders/coffees_form.html', coffee=duplicate_coffee, package_sizes=PACKAGE_SIZES, is_duplicate=True)

    @bp.route('/')
    @login_required
    def orders_index():
        start_date_raw = request.args.get('start_date')
        end_date_raw = request.args.get('end_date')
        coffee_id_raw = request.args.get('coffee_id')
        client_query = (request.args.get('client_query') or '').strip()
        min_total_raw = request.args.get('min_total')
        max_total_raw = request.args.get('max_total')

        start_date = _to_date(start_date_raw)
        end_date = _to_date(end_date_raw)
        coffee_id = None
        if coffee_id_raw and coffee_id_raw.isdigit():
            coffee_id = int(coffee_id_raw)
        min_total = _parse_number(min_total_raw)
        max_total = _parse_number(max_total_raw)

        # Vendedor vê apenas seus próprios pedidos
        user_id = None
        if current_user.is_authenticated and current_user.is_seller:
            user_id = current_user.id

        orders = order_service.list_orders(
            start_date=start_date,
            end_date=end_date,
            coffee_id=coffee_id,
            lead_name=client_query or None,
            min_total=min_total,
            max_total=max_total,
            limit=500,
            user_id=user_id,
        )
        coffees = catalog_service.list_coffees(include_inactive=True)
        total_amount = sum(order.get('total_amount') or 0 for order in orders)

        # Calcular totais por moeda
        total_by_currency: dict[str, float] = {}
        for order in orders:
            currency = order.get('currency') or 'BRL'
            amount = order.get('total_amount') or 0
            total_by_currency[currency] = total_by_currency.get(currency, 0) + amount

        has_filters = any([
            bool(start_date_raw),
            bool(end_date_raw),
            bool(coffee_id_raw),
            bool(client_query),
            bool(min_total_raw),
            bool(max_total_raw),
        ])
        filters = {
            'start_date': start_date_raw or '',
            'end_date': end_date_raw or '',
            'coffee_id': coffee_id_raw or '',
            'client_query': client_query,
            'min_total': min_total_raw or '',
            'max_total': max_total_raw or '',
        }
        stats = {
            'count': len(orders),
            'total_amount': total_amount,
            'total_by_currency': total_by_currency,
        }
        return render_template(
            'orders/orders_list.html',
            orders=orders,
            coffees=coffees,
            filters=filters,
            has_filters=has_filters,
            stats=stats,
        )

    @bp.route('/new', methods=['GET', 'POST'])
    @login_required
    def orders_new():
        # Vendedor vê apenas seus próprios leads
        user_id = None
        if current_user.is_authenticated and current_user.is_seller:
            user_id = current_user.id
        leads = crm_service.list_leads(limit=500, user_id=user_id)
        coffees = catalog_service.list_coffees(include_inactive=True)
        default_date = date.today().isoformat()

        # Lista de usuários para admin selecionar responsável
        users = auth_service.get_all_active_users() if auth_service else []

        # Moeda padrão baseada no país do usuário (PY → PYG, BR/outros → BRL)
        default_currency = 'PYG' if current_user.is_authenticated and current_user.country == 'PY' else 'BRL'

        if request.method == 'POST':
            try:
                order_data, items = _extract_order_form_data(request.form)
            except ValueError as exc:
                flash(str(exc), 'danger')
                order_state = _order_state_from_form(request.form)
                return render_template(
                    'orders/orders_form.html',
                    order=order_state,
                    leads=leads,
                    coffees=coffees,
                    package_sizes=PACKAGE_SIZES,
                    default_date=default_date,
                    default_currency=default_currency,
                    is_edit=False,
                    users=users,
                )

            # Admin pode selecionar usuário
            if current_user.is_authenticated and current_user.is_admin:
                form_user_id = request.form.get('user_id')
                if form_user_id:
                    order_data['user_id'] = int(form_user_id)
                else:
                    order_data['user_id'] = current_user.id
            # Vendedor: user_id é automaticamente dele
            elif current_user.is_authenticated and current_user.is_seller:
                order_data['user_id'] = current_user.id

            try:
                order_service.create_order(order_data, items)
                _mark_lead_as_customer(order_data.get('lead_id'))
            except ValueError as exc:
                flash(str(exc), 'danger')
                order_state = _order_state_from_form(request.form)
                return render_template(
                    'orders/orders_form.html',
                    order=order_state,
                    leads=leads,
                    coffees=coffees,
                    package_sizes=PACKAGE_SIZES,
                    default_date=default_date,
                    default_currency=default_currency,
                    is_edit=False,
                    users=users,
                )

            flash('Pedido registrado com sucesso!', 'success')
            return redirect(url_for('orders.orders_index'))

        return render_template(
            'orders/orders_form.html',
            order=None,
            leads=leads,
            coffees=coffees,
            package_sizes=PACKAGE_SIZES,
            default_date=default_date,
            default_currency=default_currency,
            is_edit=False,
            users=users,
        )

    @bp.route('/<int:order_id>')
    @login_required
    def orders_view(order_id: int):
        order = order_service.get_order(order_id)
        if not order:
            flash('Pedido não encontrado.', 'warning')
            return redirect(url_for('orders.orders_index'))

        # Vendedor só pode ver seus próprios pedidos
        if current_user.is_authenticated and current_user.is_seller:
            if order.get('user_id') != current_user.id:
                flash('Você não tem permissão para ver este pedido.', 'danger')
                return redirect(url_for('orders.orders_index'))

        lead = crm_service.get_lead(order['lead_id']) if order.get('lead_id') else None
        return render_template(
            'orders/orders_detail.html',
            order=order,
            lead=lead,
        )

    @bp.route('/<int:order_id>/edit', methods=['GET', 'POST'])
    @login_required
    def orders_edit(order_id: int):
        order = order_service.get_order(order_id)
        if not order:
            flash('Pedido não encontrado.', 'warning')
            return redirect(url_for('orders.orders_index'))

        # Vendedor só pode editar seus próprios pedidos
        if current_user.is_authenticated and current_user.is_seller:
            if order.get('user_id') != current_user.id:
                flash('Você não tem permissão para editar este pedido.', 'danger')
                return redirect(url_for('orders.orders_index'))

        # Vendedor vê apenas seus próprios leads
        user_id = None
        if current_user.is_authenticated and current_user.is_seller:
            user_id = current_user.id
        leads = crm_service.list_leads(limit=500, user_id=user_id)
        coffees = catalog_service.list_coffees(include_inactive=True)
        default_date = order.get('order_date') or date.today().isoformat()

        # Lista de usuários para admin selecionar responsável
        users = auth_service.get_all_active_users() if auth_service else []

        if request.method == 'POST':
            try:
                order_data, items = _extract_order_form_data(request.form, require_date=True)
            except ValueError as exc:
                flash(str(exc), 'danger')
                order_state = _order_state_from_form(request.form)
                order_state['id'] = order_id
                return render_template(
                    'orders/orders_form.html',
                    order=order_state,
                    leads=leads,
                    coffees=coffees,
                    package_sizes=PACKAGE_SIZES,
                    default_date=default_date,
                    is_edit=True,
                    users=users,
                )

            # Admin pode selecionar usuário
            if current_user.is_authenticated and current_user.is_admin:
                form_user_id = request.form.get('user_id')
                if form_user_id:
                    order_data['user_id'] = int(form_user_id)
                else:
                    order_data['user_id'] = current_user.id
            # Vendedor: user_id é automaticamente dele
            elif current_user.is_authenticated and current_user.is_seller:
                order_data['user_id'] = current_user.id

            try:
                order_service.update_order(order_id, order_data, items)
                _mark_lead_as_customer(order_data.get('lead_id'))
            except ValueError as exc:
                flash(str(exc), 'danger')
                order_state = _order_state_from_form(request.form)
                order_state['id'] = order_id
                return render_template(
                    'orders/orders_form.html',
                    order=order_state,
                    leads=leads,
                    coffees=coffees,
                    package_sizes=PACKAGE_SIZES,
                    default_date=default_date,
                    is_edit=True,
                    users=users,
                )

            flash('Pedido atualizado com sucesso!', 'success')
            return redirect(url_for('orders.orders_view', order_id=order_id))

        return render_template(
            'orders/orders_form.html',
            order=order,
            leads=leads,
            coffees=coffees,
            package_sizes=PACKAGE_SIZES,
            default_date=default_date,
            is_edit=True,
            users=users,
        )

    # ARCHIVED: Import functionality moved to olds/ directory (2025-10-10)
    # This feature is no longer needed but preserved for future reference
    # See: Consciencia_Cafe/olds/templates/orders/import_orders.html
    # See: Consciencia_Cafe/olds/templates/orders/import_report.html
    """
    @bp.route('/import', methods=['GET', 'POST'])
    @login_required
    def orders_import():
        if not _require_admin():
            return redirect(url_for('orders.orders_index'))

        if request.method == 'POST':
            try:
                sales_data = google_sheets_client.get_sales_data()
            except Exception as exc:
                flash(f'Erro ao acessar planilha: {exc}', 'danger')
                return redirect(url_for('orders.orders_import'))

            if not sales_data:
                flash('Nenhum dado encontrado na planilha configurada.', 'warning')
                return redirect(url_for('orders.orders_import'))

            # CLEAR ALL DATA BEFORE IMPORT
            try:
                orders_deleted = order_service.delete_all_orders()
                leads_deleted = crm_service.delete_all_leads()
                print(f"🗑️ Limpeza: {orders_deleted} pedidos e {leads_deleted} leads removidos")
            except Exception as exc:
                flash(f'Erro ao limpar dados: {exc}', 'danger')
                return redirect(url_for('orders.orders_import'))

            default_coffee_id = catalog_service.ensure_default_product()
            summary = {
                'orders_created': 0,
                'orders_skipped': 0,
                'leads_created': 0,
                'leads_reused': 0,
                'errors': 0,
                'promotion_errors': 0,
            }
            skipped_details: List[Dict[str, Any]] = []

            for idx, entry in enumerate(sales_data, start=1):
                name = (entry.get('cliente') or '').strip()
                if not name:
                    summary['errors'] += 1
                    skipped_details.append({
                        'row': idx,
                        'cliente': entry.get('cliente', ''),
                        'data': entry.get('data', ''),
                        'valor': entry.get('valor', ''),
                        'quantidade': entry.get('quantidade', ''),
                        'motivo': 'Nome do cliente não informado'
                    })
                    continue

                quantity = _parse_number(entry.get('quantidade') or entry.get('quantity'))
                value = _parse_number(entry.get('valor'))
                if not quantity or quantity <= 0 or value is None:
                    summary['orders_skipped'] += 1
                    motivo = []
                    if not quantity or quantity <= 0:
                        motivo.append('quantidade inválida')
                    if value is None:
                        motivo.append('valor não informado')
                    skipped_details.append({
                        'row': idx,
                        'cliente': name,
                        'data': entry.get('data', ''),
                        'valor': entry.get('valor', ''),
                        'quantidade': entry.get('quantidade', ''),
                        'motivo': ', '.join(motivo).capitalize()
                    })
                    continue

                # Get country from spreadsheet - try all common field names
                country = (
                    entry.get('pais') or
                    entry.get('país') or
                    entry.get('Pais') or
                    entry.get('País') or
                    entry.get('country') or
                    entry.get('Country') or
                    entry.get('PAIS') or
                    entry.get('PAÍS') or
                    ''
                ).strip() or None

                # Debug: print country value
                print(f"🌍 Cliente: {name} | País da planilha: {repr(country)} | Campos disponíveis: {list(entry.keys())}")

                lead_id, created = _ensure_lead_simple(name, country)
                if not lead_id:
                    summary['errors'] += 1
                    skipped_details.append({
                        'row': idx,
                        'cliente': name,
                        'data': entry.get('data', ''),
                        'valor': value,
                        'quantidade': quantity,
                        'motivo': 'Erro ao criar/encontrar lead'
                    })
                    continue
                if created:
                    summary['leads_created'] += 1
                else:
                    summary['leads_reused'] += 1

                order_date_str = entry.get('data')
                order_date_obj = _to_date(order_date_str)

                unit_price = value / quantity if quantity else value
                try:
                    order_service.create_order(
                        {
                            'lead_id': lead_id,
                            'order_date': order_date_str,
                            'currency': entry.get('currency', 'BRL'),
                            'notes': entry.get('observacoes'),
                            'source': 'google_sheets',
                        },
                        [
                            {
                                'coffee_id': default_coffee_id,
                                'description': entry.get('produto') or 'Café padrão importado',
                                'package_size': '1kg',
                                'quantity': float(quantity),
                                'unit_price': float(unit_price),
                            }
                        ],
                    )
                    summary['orders_created'] += 1
                    try:
                        _mark_lead_as_customer(lead_id)
                    except Exception:
                        summary['promotion_errors'] += 1
                except ValueError as exc:
                    summary['orders_skipped'] += 1
                    skipped_details.append({
                        'row': idx,
                        'cliente': name,
                        'data': order_date_str,
                        'valor': value,
                        'quantidade': quantity,
                        'motivo': f'Erro ao criar pedido: {str(exc)}'
                    })
                except Exception as exc:
                    summary['orders_skipped'] += 1
                    skipped_details.append({
                        'row': idx,
                        'cliente': name,
                        'data': order_date_str,
                        'valor': value,
                        'quantidade': quantity,
                        'motivo': f'Erro inesperado: {str(exc)}'
                    })

            message_parts = [
                f"{summary['orders_created']} pedidos criados",
                f"{summary['orders_skipped']} ignorados",
                f"{summary['leads_created']} novos leads",
            ]
            if summary['errors']:
                message_parts.append(f"{summary['errors']} erros")
            if summary['promotion_errors']:
                message_parts.append(f"{summary['promotion_errors']} promoções pendentes")
            if summary['leads_reused']:
                message_parts.append(f"{summary['leads_reused']} leads reaproveitados")

            flash("Importação concluída: " + ", ".join(message_parts) + ".", 'success')

            # Render report with skipped details if there are any
            if skipped_details:
                return render_template(
                    'orders/import_report.html',
                    summary=summary,
                    skipped_details=skipped_details
                )

            return redirect(url_for('orders.orders_index'))

        sales_data = google_sheets_client.get_sales_data()
        preview_rows = sales_data[:10]
        total_rows = len(sales_data)
        using_mock = getattr(google_sheets_client, 'use_mock_data', False)
        return render_template(
            'orders/import_orders.html',
            preview_rows=preview_rows,
            total_rows=total_rows,
            using_mock_data=using_mock,
        )
    """
    # End of archived import functionality

    @bp.route('/<int:order_id>/delete', methods=['POST'])
    @login_required
    def orders_delete(order_id: int):
        if current_user.role != 'admin':
            flash('Apenas administradores podem excluir pedidos.', 'danger')
            return redirect(url_for('orders.orders_index'))
        order_service.delete_order(order_id)
        flash('Pedido removido.', 'info')
        return redirect(url_for('orders.orders_index'))

    return bp
