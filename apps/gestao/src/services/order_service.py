"""Order service leveraging SQLAlchemy."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import joinedload

from ..db import session_scope
from ..models import Order, OrderItem, CRMLead


class OrderService:
    def list_orders(
        self,
        *,
        lead_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        coffee_id: Optional[int] = None,
        lead_name: Optional[str] = None,
        min_total: Optional[float] = None,
        max_total: Optional[float] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        with session_scope() as session:
            query = session.query(Order).options(joinedload(Order.lead))
            if lead_id:
                query = query.filter(Order.lead_id == lead_id)
            if start_date:
                query = query.filter(Order.order_date >= start_date)
            if end_date:
                query = query.filter(Order.order_date <= end_date)
            if coffee_id:
                query = query.filter(Order.items.any(OrderItem.coffee_id == coffee_id))
            if lead_name:
                pattern = f"%{lead_name.strip()}%"
                query = query.filter(Order.lead.has(CRMLead.name.ilike(pattern)))
            if min_total is not None:
                query = query.filter(Order.total_amount >= float(min_total))
            if max_total is not None:
                query = query.filter(Order.total_amount <= float(max_total))
            orders = (
                query.order_by(Order.order_date.desc(), Order.id.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [self._serialize_order(order, include_items=False) for order in orders]

    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            order = session.query(Order).options(joinedload(Order.items)).get(order_id)
            if not order:
                return None
            return self._serialize_order(order, include_items=True)

    def create_order(self, data: Dict[str, Any], items: List[Dict[str, Any]]) -> int:
        if not items:
            raise ValueError('Pedido precisa de pelo menos um item')

        order_date = data.get('order_date')
        if not order_date:
            order_date = date.today()
        elif isinstance(order_date, str):
            order_date = date.fromisoformat(order_date)

        with session_scope() as session:
            order = Order(
                lead_id=data.get('lead_id'),
                client_id=data.get('client_id'),
                order_date=order_date,
                currency=data.get('currency', 'BRL'),
                notes=data.get('notes'),
                source=data.get('source'),
            )
            session.add(order)
            session.flush()

            order.total_amount = self._apply_items(order, items)
            return order.id

    def update_order(self, order_id: int, data: Dict[str, Any], items: List[Dict[str, Any]]) -> None:
        if not items:
            raise ValueError('Pedido precisa de pelo menos um item')

        order_date = data.get('order_date')
        if not order_date:
            raise ValueError('Data do pedido é obrigatória')
        if isinstance(order_date, str):
            order_date = date.fromisoformat(order_date)

        with session_scope() as session:
            order = session.get(Order, order_id)
            if not order:
                raise ValueError('Pedido não encontrado')

            order.lead_id = data.get('lead_id')
            order.client_id = data.get('client_id')
            order.order_date = order_date
            order.currency = data.get('currency', 'BRL')
            order.notes = data.get('notes')
            order.source = data.get('source')

            # Clear existing items (delete-orphan ensures DB sync)
            order.items[:] = []
            order.total_amount = self._apply_items(order, items)

    def order_exists(self, lead_id: int, order_date: Optional[date], total_amount: float) -> bool:
        with session_scope() as session:
            query = session.query(Order.id).filter(Order.lead_id == lead_id)
            if order_date:
                query = query.filter(Order.order_date == order_date)
            if total_amount is not None:
                amount_decimal = Decimal(str(total_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                query = query.filter(Order.total_amount == amount_decimal)
            return query.first() is not None

    def delete_order(self, order_id: int) -> None:
        with session_scope() as session:
            order = session.get(Order, order_id)
            if order:
                session.delete(order)

    def delete_all_orders(self) -> int:
        """Delete all orders and their items. Returns count of deleted orders."""
        with session_scope() as session:
            count = session.query(Order).count()
            session.query(Order).delete()
            return count

    def import_simple_orders(self, rows: List[Dict[str, Any]], default_coffee_id: int, *, source: str = 'import_planilha') -> Dict[str, int]:
        created = 0
        skipped = 0
        for row in rows:
            try:
                order_date = row.get('order_month') or row.get('order_date')
                if order_date and isinstance(order_date, str) and len(order_date) == 7:
                    order_date = f"{order_date}-01"
                quantity = float(row.get('quantity_kg') or row.get('kg') or 0)
                value = float(row.get('value') or row.get('total') or 0)
            except (ValueError, TypeError):
                skipped += 1
                continue

            lead_id = row.get('lead_id')
            if isinstance(lead_id, str) and lead_id.isdigit():
                lead_id = int(lead_id)

            unit_price = value / quantity if quantity else value
            try:
                self.create_order(
                    {
                        'lead_id': lead_id,
                        'order_date': order_date,
                        'currency': row.get('currency', 'BRL'),
                        'notes': row.get('notes'),
                        'source': source,
                    },
                    [
                        {
                            'coffee_id': default_coffee_id,
                            'description': row.get('coffee') or 'Café padrão importado',
                            'package_size': row.get('package_size') or '1kg',
                            'quantity': quantity,
                            'unit_price': unit_price,
                        }
                    ]
                )
                created += 1
            except ValueError:
                skipped += 1

        return {'created': created, 'skipped': skipped}

    def _serialize_order(self, order: Order, *, include_items: bool) -> Dict[str, Any]:
        data = {
            'id': order.id,
            'lead_id': order.lead_id,
            'client_id': order.client_id,
            'order_date': order.order_date.isoformat() if order.order_date else None,
            'currency': order.currency,
            'notes': order.notes,
            'source': order.source,
            'total_amount': float(order.total_amount) if order.total_amount is not None else None,
            'lead_name': order.lead.name if order.lead else None,
            'client_name': None,  # TODO: Add client relationship when needed
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
        }
        if include_items:
            data['items'] = [
                {
                    'id': item.id,
                    'coffee_id': item.coffee_id,
                    'coffee_name': item.coffee.name if item.coffee else None,
                    'description': item.description,
                    'package_size': item.package_size,
                    'quantity': float(item.quantity) if item.quantity is not None else None,
                    'unit_price': float(item.unit_price) if item.unit_price is not None else None,
                    'line_total': float(item.line_total) if item.line_total is not None else None,
                }
                for item in order.items
            ]
        return data

    def _apply_items(self, order: Order, items: List[Dict[str, Any]]) -> Decimal:
        total = Decimal('0.00')
        for item in items:
            quantity = float(item.get('quantity', 0))
            unit_price = float(item.get('unit_price', 0))
            line_total = quantity * unit_price
            total += Decimal(str(line_total))
            order.items.append(
                OrderItem(
                    coffee_id=item.get('coffee_id'),
                    description=item.get('description'),
                    package_size=item.get('package_size'),
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


__all__ = ['OrderService']
