"""Commission Service - calculates seller commissions dynamically from orders."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, extract
from sqlalchemy.orm import joinedload

from ..db import session_scope
from ..models import Commission, CommissionRate, Order, CRMUser
from .commission_rate_service import CommissionRateService
from .exchange_rate_service import ExchangeRateService


class CommissionService:
    """
    Calculates commissions dynamically from orders.
    Commission records are only created when payment is registered.
    """

    def __init__(
        self,
        commission_rate_service: Optional[CommissionRateService] = None,
        exchange_rate_service: Optional[ExchangeRateService] = None
    ):
        self.commission_rate_service = commission_rate_service or CommissionRateService()
        self.exchange_rate_service = exchange_rate_service or ExchangeRateService()

    def _get_native_currency(self, country: Optional[str]) -> str:
        """Get native currency based on country."""
        if country == 'PY':
            return 'PYG'
        return 'BRL'

    def get_commissions_for_period(
        self,
        user_id: int,
        month: int,
        year: int
    ) -> Dict[str, Any]:
        """
        Calculate commissions dynamically from orders for a given period.
        All values are converted to the seller's native currency.

        Args:
            user_id: The seller's user ID
            month: Month (1-12)
            year: Year

        Returns:
            Dict with orders, totals, and commission calculations in native currency
        """
        with session_scope() as session:
            # Get user info
            user = session.get(CRMUser, user_id)
            if not user or user.role != 'vendedor':
                return {
                    'user_id': user_id,
                    'username': user.username if user else None,
                    'country': user.country if user else None,
                    'native_currency': 'BRL',
                    'month': month,
                    'year': year,
                    'orders': [],
                    'totals': {'order_count': 0, 'total_commission': 0, 'paid': 0, 'pending': 0}
                }

            # Determine seller's native currency
            native_currency = self._get_native_currency(user.country)

            # Get commission rate for this user
            rate_info = self.commission_rate_service.get_current_rate(user_id)
            rate = Decimal(str(rate_info['rate'])) if rate_info and rate_info.get('rate') else Decimal('0')

            # Query orders for this seller in the period
            orders = (
                session.query(Order)
                .options(joinedload(Order.lead))
                .filter(
                    Order.user_id == user_id,
                    extract('month', Order.order_date) == month,
                    extract('year', Order.order_date) == year
                )
                .order_by(Order.order_date.desc())
                .all()
            )

            # Get already paid commissions for this period
            paid_commissions = (
                session.query(Commission)
                .filter(
                    Commission.user_id == user_id,
                    Commission.status == 'paid'
                )
                .all()
            )
            paid_order_ids = {c.order_id for c in paid_commissions}

            # Calculate commissions - convert everything to native currency
            order_list = []
            total_commission = Decimal('0')
            paid_amount = Decimal('0')

            for order in orders:
                order_total = Decimal(str(order.total_amount or 0))
                order_currency = (order.currency or 'BRL').upper().strip()

                # Calculate commission in order's original currency
                commission_original = (order_total * rate / Decimal('100')).quantize(Decimal('0.01'))

                # Convert to native currency if needed
                needs_conversion = order_currency != native_currency
                conversion_failed = False

                if needs_conversion:
                    # Try to convert using exchange rate service
                    converted = self.exchange_rate_service.convert(
                        float(commission_original),
                        order_currency,
                        native_currency,
                        order.order_date or date.today()
                    )

                    if converted is not None and converted > 0:
                        commission_native = Decimal(str(converted)).quantize(Decimal('0.01'))
                    else:
                        # Conversion failed - keep original and mark it
                        commission_native = commission_original
                        conversion_failed = True
                else:
                    commission_native = commission_original

                is_paid = order.id in paid_order_ids

                # Only add to total if conversion worked or no conversion needed
                if not conversion_failed:
                    total_commission += commission_native

                if is_paid and not conversion_failed:
                    paid_amount += commission_native

                order_list.append({
                    'order_id': order.id,
                    'order_date': order.order_date.isoformat() if order.order_date else None,
                    'lead_name': order.lead.name if order.lead else None,
                    'order_total': float(order_total),
                    'order_currency': order_currency,
                    'commission_original': float(commission_original),
                    'commission_native': float(commission_native),
                    'rate_applied': float(rate),
                    'is_paid': is_paid,
                    'needs_conversion': needs_conversion,
                    'conversion_failed': conversion_failed
                })

            pending = total_commission - paid_amount

            return {
                'user_id': user_id,
                'username': user.username,
                'country': user.country,
                'native_currency': native_currency,
                'month': month,
                'year': year,
                'period': f'{year}-{month:02d}',
                'rate': float(rate),
                'orders': order_list,
                'totals': {
                    'order_count': len(orders),
                    'total_commission': float(total_commission),
                    'paid': float(paid_amount),
                    'pending': float(pending)
                }
            }

    def get_summary(self, user_id: int, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """Get a quick summary of commissions for a user."""
        if month is None:
            month = date.today().month
        if year is None:
            year = date.today().year

        data = self.get_commissions_for_period(user_id, month, year)
        return {
            'user_id': user_id,
            'month': month,
            'year': year,
            'period': f'{year}-{month:02d}',
            'native_currency': data.get('native_currency', 'BRL'),
            'rate': data.get('rate', 0),
            'order_count': data['totals']['order_count'],
            'total_commission': data['totals']['total_commission'],
            'paid': data['totals']['paid'],
            'pending': data['totals']['pending']
        }

    def register_payment(
        self,
        user_id: int,
        order_ids: List[int],
        payment_reference: Optional[str] = None,
        admin_user_id: Optional[int] = None
    ) -> List[int]:
        """
        Register payment for commissions. Only creates Commission records when paid.

        Args:
            user_id: The seller's user ID
            order_ids: List of order IDs being paid
            payment_reference: Optional payment reference
            admin_user_id: ID of the admin registering the payment

        Returns:
            List of created commission IDs
        """
        rate_info = self.commission_rate_service.get_current_rate(user_id)
        rate = Decimal(str(rate_info['rate'])) if rate_info and rate_info.get('rate') else Decimal('0')

        created_ids = []

        with session_scope() as session:
            for order_id in order_ids:
                # Check if already paid
                existing = (
                    session.query(Commission)
                    .filter(Commission.order_id == order_id)
                    .first()
                )
                if existing:
                    continue

                # Get order
                order = session.get(Order, order_id)
                if not order or order.user_id != user_id:
                    continue

                # Calculate commission
                order_total = Decimal(str(order.total_amount or 0))
                commission_amount = (order_total * rate / Decimal('100')).quantize(Decimal('0.01'))

                # Convert to BRL if needed
                amount_brl = None
                if order.currency and order.currency.upper() != 'BRL':
                    brl_amount = self.exchange_rate_service.convert(
                        float(commission_amount),
                        order.currency,
                        'BRL',
                        order.order_date
                    )
                    if brl_amount:
                        amount_brl = Decimal(str(brl_amount)).quantize(Decimal('0.01'))

                # Create commission record
                commission = Commission(
                    user_id=user_id,
                    order_id=order_id,
                    amount=commission_amount,
                    amount_brl=amount_brl,
                    rate_applied=rate,
                    status='paid',
                    payment_date=date.today(),
                    payment_reference=payment_reference
                )
                session.add(commission)
                session.flush()
                created_ids.append(commission.id)

        return created_ids

    def get_paid_commissions(
        self,
        user_id: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """Get list of paid commissions (historical record)."""
        with session_scope() as session:
            query = session.query(Commission).filter(Commission.status == 'paid')

            if user_id:
                query = query.filter(Commission.user_id == user_id)

            if month and year:
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1)
                else:
                    end_date = date(year, month + 1, 1)
                query = query.filter(
                    Commission.payment_date >= start_date,
                    Commission.payment_date < end_date
                )

            commissions = query.order_by(Commission.payment_date.desc()).limit(limit).all()

            return [self._serialize_commission(c, session) for c in commissions]

    def _serialize_commission(self, commission: Commission, session) -> Dict[str, Any]:
        """Serialize a commission record."""
        order = session.get(Order, commission.order_id)
        user = session.get(CRMUser, commission.user_id)

        return {
            'id': commission.id,
            'user_id': commission.user_id,
            'username': user.username if user else None,
            'order_id': commission.order_id,
            'order_date': order.order_date.isoformat() if order and order.order_date else None,
            'order_total': float(order.total_amount) if order and order.total_amount else 0,
            'order_currency': order.currency if order else 'BRL',
            'amount': float(commission.amount),
            'amount_brl': float(commission.amount_brl) if commission.amount_brl else None,
            'rate_applied': float(commission.rate_applied),
            'status': commission.status,
            'payment_date': commission.payment_date.isoformat() if commission.payment_date else None,
            'payment_reference': commission.payment_reference
        }


__all__ = ['CommissionService']
