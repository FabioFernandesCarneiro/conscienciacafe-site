"""Blueprint for exchange rate management routes."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .services.exchange_rate_service import ExchangeRateService
from .db import session_scope
from .models import ExchangeRate


def create_exchange_blueprint(exchange_rate_service: ExchangeRateService) -> Blueprint:
    bp = Blueprint('exchange', __name__, url_prefix='/exchange')

    def _require_admin():
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acesso negado. Somente administradores.', 'danger')
            return False
        return True

    @bp.route('/')
    @login_required
    def index():
        """List exchange rate history."""
        if not _require_admin():
            return redirect(url_for('dashboard'))

        from_currency = request.args.get('from_currency', 'PYG')
        to_currency = request.args.get('to_currency', 'BRL')

        rates = exchange_rate_service.list_rates(
            from_currency=from_currency,
            to_currency=to_currency,
            limit=100
        )

        latest_rates = exchange_rate_service.get_latest_rates()

        return render_template(
            'exchange/index.html',
            rates=rates,
            latest_rates=latest_rates,
            from_currency=from_currency,
            to_currency=to_currency
        )

    @bp.route('/set', methods=['GET', 'POST'])
    @login_required
    def set_rate():
        """Set a new exchange rate."""
        if not _require_admin():
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            try:
                from_currency = request.form.get('from_currency', 'PYG').upper()
                to_currency = request.form.get('to_currency', 'BRL').upper()
                rate = float(request.form.get('rate', 0))
                effective_date_str = request.form.get('effective_date')

                if not effective_date_str:
                    effective_date = date.today()
                else:
                    effective_date = date.fromisoformat(effective_date_str)

                exchange_rate_service.set_rate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=rate,
                    effective_date=effective_date,
                    created_by=int(current_user.get_id())
                )

                flash(f'Taxa de cambio {from_currency}/{to_currency} = {rate} definida!', 'success')
                return redirect(url_for('exchange.index'))

            except ValueError as exc:
                flash(str(exc), 'danger')

        # Get current rate for default values
        current_rate = exchange_rate_service.get_rate('PYG', 'BRL')

        return render_template(
            'exchange/set_rate.html',
            current_rate=current_rate,
            edit_mode=False,
            rate_data=None
        )

    @bp.route('/<int:rate_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_rate(rate_id: int):
        """Edit an existing exchange rate."""
        if not _require_admin():
            return redirect(url_for('dashboard'))

        with session_scope() as session:
            rate_record = session.get(ExchangeRate, rate_id)
            if not rate_record:
                flash('Taxa não encontrada.', 'danger')
                return redirect(url_for('exchange.index'))

            rate_data = {
                'id': rate_record.id,
                'from_currency': rate_record.from_currency,
                'to_currency': rate_record.to_currency,
                'rate': float(rate_record.rate),
                'effective_date': rate_record.effective_date.isoformat() if rate_record.effective_date else None
            }

        if request.method == 'POST':
            try:
                from_currency = request.form.get('from_currency', '').upper()
                to_currency = request.form.get('to_currency', '').upper()
                rate = float(request.form.get('rate', 0))
                effective_date_str = request.form.get('effective_date')

                if not effective_date_str:
                    effective_date = date.today()
                else:
                    effective_date = date.fromisoformat(effective_date_str)

                # Update the rate in database
                with session_scope() as session:
                    rate_record = session.get(ExchangeRate, rate_id)
                    if rate_record:
                        rate_record.from_currency = from_currency
                        rate_record.to_currency = to_currency
                        rate_record.rate = rate
                        rate_record.effective_date = effective_date
                        rate_record.created_by = int(current_user.get_id())

                flash(f'Taxa de câmbio atualizada com sucesso!', 'success')
                return redirect(url_for('exchange.index'))

            except ValueError as exc:
                flash(str(exc), 'danger')

        return render_template(
            'exchange/set_rate.html',
            current_rate=rate_data['rate'],
            edit_mode=True,
            rate_data=rate_data
        )

    @bp.route('/<int:rate_id>/delete', methods=['POST'])
    @login_required
    def delete_rate(rate_id: int):
        """Delete an exchange rate."""
        if not _require_admin():
            return redirect(url_for('dashboard'))

        with session_scope() as session:
            rate_record = session.get(ExchangeRate, rate_id)
            if rate_record:
                session.delete(rate_record)
                flash('Taxa de câmbio excluída.', 'success')
            else:
                flash('Taxa não encontrada.', 'danger')

        return redirect(url_for('exchange.index'))

    # ==========================
    # API Routes
    # ==========================

    @bp.route('/api/convert')
    @login_required
    def api_convert():
        """Convert an amount between currencies."""
        amount = request.args.get('amount', type=float)
        from_currency = request.args.get('from', 'PYG').upper()
        to_currency = request.args.get('to', 'BRL').upper()
        for_date_str = request.args.get('date')

        if amount is None:
            return jsonify({'error': 'amount is required'}), 400

        for_date = date.fromisoformat(for_date_str) if for_date_str else None

        converted = exchange_rate_service.convert(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            for_date=for_date
        )

        if converted is None:
            return jsonify({
                'error': f'No exchange rate found for {from_currency}/{to_currency}'
            }), 404

        rate = exchange_rate_service.get_rate(from_currency, to_currency, for_date)

        return jsonify({
            'amount': amount,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'rate': rate,
            'converted': converted
        })

    @bp.route('/api/rate')
    @login_required
    def api_rate():
        """Get the exchange rate for a currency pair."""
        from_currency = request.args.get('from', 'PYG').upper()
        to_currency = request.args.get('to', 'BRL').upper()
        for_date_str = request.args.get('date')

        for_date = date.fromisoformat(for_date_str) if for_date_str else None

        rate = exchange_rate_service.get_rate(from_currency, to_currency, for_date)

        return jsonify({
            'from_currency': from_currency,
            'to_currency': to_currency,
            'rate': rate
        })

    @bp.route('/api/latest')
    @login_required
    def api_latest():
        """Get all latest exchange rates."""
        rates = exchange_rate_service.get_latest_rates()
        return jsonify(rates)

    return bp


__all__ = ['create_exchange_blueprint']
