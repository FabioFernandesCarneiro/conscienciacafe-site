"""Database-backed repository for B2B sales analytics."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import pandas as pd
from ..db import session_scope
from ..models import CRMLead, CoffeeProduct, Order, OrderItem

if TYPE_CHECKING:
    from ..services.exchange_rate_service import ExchangeRateService


class SalesRepository:
    """Provides tabular sales data sourced from orders stored in the database."""

    def __init__(
        self,
        session_factory=session_scope,
        exchange_rate_service: Optional['ExchangeRateService'] = None,
        target_currency: str = 'BRL'
    ) -> None:
        self._session_factory = session_factory
        self._exchange_rate_service = exchange_rate_service
        self._target_currency = target_currency.upper() if target_currency else 'BRL'

    def fetch_sales_dataframe(
        self,
        *,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[int] = None,
    ) -> pd.DataFrame:
        """Load order + item data for analytics as a pandas DataFrame."""
        rows = self._fetch_raw_rows(start_date=start_date, end_date=end_date, user_id=user_id)
        if not rows:
            return pd.DataFrame(
                columns=[
                    "order_id",
                    "item_id",
                    "date",
                    "value",
                    "currency",
                    "quantity",
                    "client_id",
                    "cliente",
                    "product",
                    "lead_status",
                    "lead_city",
                    "lead_state",
                    "lead_country",
                    "observacoes",
                ]
            )

        frame = pd.DataFrame(rows)
        frame["date"] = pd.to_datetime(frame["date"])
        frame["value"] = frame["value"].astype(float)
        frame["quantity"] = frame["quantity"].astype(float)

        # Normalized columns expected by existing analytics
        frame["client_id"] = frame.apply(self._resolve_client_id, axis=1)
        frame["cliente"] = frame.apply(self._resolve_client_name, axis=1)
        frame["product"] = frame["coffee_name"].fillna(frame["item_description"]).fillna("Produto não informado")
        frame["observacoes"] = frame.apply(self._build_observation, axis=1)

        frame["data"] = frame["date"]
        frame["quantidade"] = frame["quantity"]
        frame["produto"] = frame["product"]
        frame["pais"] = frame["lead_country"].fillna("Brasil")
        frame["moeda"] = frame["currency"].fillna("BRL")

        # Convert values to target currency for consistent metrics
        frame["valor"] = frame.apply(self._convert_to_target_currency, axis=1)
        frame["value"] = frame["valor"]  # Keep both columns in sync
        frame["display_currency"] = self._target_currency

        return frame

    def _convert_to_target_currency(self, row: pd.Series) -> float:
        """Convert value to target currency if in different currency."""
        value = float(row.get("value") or 0)
        currency = str(row.get("currency") or "BRL").upper().strip()

        # If already in target currency, no conversion needed
        if currency == self._target_currency:
            return value

        # If no exchange rate service, return original value
        if not self._exchange_rate_service:
            return value

        # Get order date for exchange rate lookup
        order_date = row.get("date")
        if isinstance(order_date, pd.Timestamp):
            order_date = order_date.date()
        elif isinstance(order_date, datetime):
            order_date = order_date.date()

        # Convert to target currency
        converted = self._exchange_rate_service.convert(
            value,
            currency,
            self._target_currency,
            order_date
        )

        if converted is not None:
            return float(converted)

        # If conversion fails, return original value (better than 0)
        print(f"⚠️ Falha na conversão {currency} -> {self._target_currency} para valor {value}")
        return value

    def _fetch_raw_rows(
        self,
        *,
        start_date: Optional[date],
        end_date: Optional[date],
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        with self._session_factory() as session:
            query = (
                session.query(
                    Order.id.label("order_id"),
                    OrderItem.id.label("item_id"),
                    Order.order_date.label("date"),
                    Order.total_amount.label("order_total"),
                    Order.currency.label("currency"),
                    Order.lead_id.label("lead_id"),
                    Order.client_id.label("client_id"),
                    Order.user_id.label("user_id"),
                    Order.source.label("order_source"),
                    Order.notes.label("order_notes"),
                    CRMLead.name.label("lead_name"),
                    CRMLead.city.label("lead_city"),
                    CRMLead.state.label("lead_state"),
                    CRMLead.country.label("lead_country"),
                    CRMLead.status.label("lead_status"),
                    CoffeeProduct.name.label("coffee_name"),
                    OrderItem.quantity.label("quantity"),
                    OrderItem.unit_price.label("unit_price"),
                    OrderItem.line_total.label("value"),
                    OrderItem.description.label("item_description"),
                )
                .join(OrderItem, OrderItem.order_id == Order.id)
                .outerjoin(CRMLead, CRMLead.id == Order.lead_id)
                .outerjoin(CoffeeProduct, CoffeeProduct.id == OrderItem.coffee_id)
            )

            if start_date:
                query = query.filter(Order.order_date >= start_date)
            if end_date:
                query = query.filter(Order.order_date <= end_date)
            if user_id:
                query = query.filter(Order.user_id == user_id)

            query = query.order_by(Order.order_date.desc(), Order.id.desc())
            results = query.all()

        rows: List[Dict[str, Any]] = []
        for record in results:
            row = dict(record._mapping)
            if row.get("value") is None:
                quantity = row.get("quantity") or 0
                unit_price = row.get("unit_price") or 0
                row["value"] = float(quantity) * float(unit_price)
            rows.append(row)
        return rows

    @staticmethod
    def _resolve_client_id(row: pd.Series) -> str:
        if pd.notna(row.get("lead_id")):
            return f"L{int(row['lead_id'])}"
        client_id = row.get("client_id")
        if pd.notna(client_id):
            return f"C{int(client_id)}"
        return "desconhecido"

    @staticmethod
    def _resolve_client_name(row: pd.Series) -> str:
        lead_name = row.get("lead_name")
        if isinstance(lead_name, str) and lead_name.strip():
            return lead_name.strip()
        client_id = row.get("client_id")
        if pd.notna(client_id):
            return f"Cliente #{int(client_id)}"
        return "Cliente não identificado"

    @staticmethod
    def _build_observation(row: pd.Series) -> str:
        order_date: datetime = row["date"]
        country = row.get("lead_country") or "Brasil"
        source = row.get("order_source")
        parts = [f"Venda {order_date.strftime('%m/%Y')} - {country}"]
        if source:
            parts.append(f"Origem: {source}")
        return " | ".join(parts)


__all__ = ["SalesRepository"]
