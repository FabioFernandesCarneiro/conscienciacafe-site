"""Blueprint for commission management routes."""

from __future__ import annotations

from datetime import date, datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .services.commission_service import CommissionService
from .services.commission_rate_service import CommissionRateService


def create_commission_blueprint(
    commission_service: CommissionService,
    commission_rate_service: CommissionRateService
) -> Blueprint:
    bp = Blueprint('commissions', __name__, url_prefix='/commissions')

    def _require_admin():
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acesso negado. Somente administradores.', 'danger')
            return False
        return True

    # ==========================
    # Commission Rate Routes
    # ==========================

    @bp.route('/rates')
    @login_required
    def list_rates():
        """List all sellers and their current commission rates."""
        if not _require_admin():
            return redirect(url_for('dashboard'))

        rates = commission_rate_service.list_all_current_rates()
        return render_template('commissions/rates.html', rates=rates)

    @bp.route('/rates/<int:user_id>')
    @login_required
    def rate_history(user_id: int):
        """View commission rate history for a seller."""
        if not _require_admin():
            return redirect(url_for('dashboard'))

        rates = commission_rate_service.list_rates(user_id)
        current_rate = commission_rate_service.get_current_rate(user_id)

        return render_template(
            'commissions/rate_history.html',
            user_id=user_id,
            rates=rates,
            current_rate=current_rate
        )

    @bp.route('/rates/<int:user_id>/set', methods=['GET', 'POST'])
    @login_required
    def set_rate(user_id: int):
        """Set a new commission rate for a seller."""
        if not _require_admin():
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            try:
                rate = float(request.form.get('rate', 0))
                start_date_str = request.form.get('start_date')

                if not start_date_str:
                    start_date = date.today()
                else:
                    start_date = date.fromisoformat(start_date_str)

                commission_rate_service.set_rate(
                    user_id=user_id,
                    rate=rate,
                    start_date=start_date,
                    created_by=int(current_user.get_id())
                )

                flash(f'Taxa de comissao de {rate}% definida com sucesso!', 'success')
                return redirect(url_for('commissions.list_rates'))

            except ValueError as exc:
                flash(str(exc), 'danger')

        current_rate = commission_rate_service.get_current_rate(user_id)
        return render_template(
            'commissions/set_rate.html',
            user_id=user_id,
            current_rate=current_rate
        )

    # ==========================
    # Commission Routes
    # ==========================

    @bp.route('/')
    @login_required
    def index():
        """View commissions - calculated dynamically from orders."""
        # Parse month/year from query params
        month = request.args.get('month', type=int) or date.today().month
        year = request.args.get('year', type=int) or date.today().year
        user_id = request.args.get('user_id', type=int)

        # Determine which user's commissions to show
        if current_user.is_seller:
            user_id = current_user.id
        elif not user_id and current_user.is_admin:
            # Admin must select a user
            sellers = commission_rate_service.list_all_current_rates()
            return render_template(
                'commissions/select_seller.html',
                sellers=sellers,
                month=month,
                year=year
            )

        if not user_id:
            flash('Selecione um vendedor.', 'warning')
            return redirect(url_for('commissions.list_rates'))

        # Get commission data calculated from orders
        data = commission_service.get_commissions_for_period(user_id, month, year)

        # Generate list of months for selector
        months = [
            {'value': i, 'label': _get_month_name(i)}
            for i in range(1, 13)
        ]

        # Generate years list (current year and 2 previous)
        current_year = date.today().year
        years = list(range(current_year - 2, current_year + 1))

        return render_template(
            'commissions/index.html',
            data=data,
            months=months,
            years=years,
            selected_month=month,
            selected_year=year,
            is_admin=current_user.is_admin
        )

    @bp.route('/pay', methods=['POST'])
    @login_required
    def register_payment():
        """Register payment for selected commissions (admin only)."""
        if not _require_admin():
            return jsonify({'error': 'Acesso negado'}), 403

        user_id = request.form.get('user_id', type=int)
        order_ids = request.form.getlist('order_ids', type=int)
        payment_reference = request.form.get('payment_reference')

        if not user_id or not order_ids:
            flash('Selecione os pedidos para registrar pagamento.', 'warning')
            return redirect(request.referrer or url_for('commissions.index'))

        try:
            created = commission_service.register_payment(
                user_id=user_id,
                order_ids=order_ids,
                payment_reference=payment_reference,
                admin_user_id=int(current_user.get_id())
            )
            flash(f'Pagamento registrado para {len(created)} comissoes!', 'success')
        except ValueError as exc:
            flash(str(exc), 'danger')

        return redirect(request.referrer or url_for('commissions.index'))

    @bp.route('/history')
    @login_required
    def payment_history():
        """View payment history."""
        user_id = request.args.get('user_id', type=int)
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)

        if current_user.is_seller:
            user_id = current_user.id

        paid = commission_service.get_paid_commissions(
            user_id=user_id,
            month=month,
            year=year
        )

        return render_template(
            'commissions/history.html',
            commissions=paid,
            filters={'user_id': user_id, 'month': month, 'year': year}
        )

    # ==========================
    # API Routes
    # ==========================

    @bp.route('/api/summary')
    @login_required
    def api_summary():
        """Get commission summary for current user."""
        user_id = request.args.get('user_id', type=int)
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)

        if current_user.is_seller:
            user_id = current_user.id
        elif not user_id:
            return jsonify({'error': 'user_id required for admin'}), 400

        summary = commission_service.get_summary(user_id, month, year)
        return jsonify(summary)

    def _get_month_name(month: int) -> str:
        """Get Portuguese month name."""
        names = [
            '', 'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return names[month] if 1 <= month <= 12 else ''

    return bp


__all__ = ['create_commission_blueprint']
