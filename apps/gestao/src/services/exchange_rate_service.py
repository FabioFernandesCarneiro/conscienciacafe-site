"""Exchange Rate Service - manages currency exchange rates."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc

from ..db import session_scope
from ..models import ExchangeRate


class ExchangeRateService:
    """Manages exchange rates between currencies."""

    def set_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        effective_date: date,
        created_by: Optional[int] = None
    ) -> int:
        """
        Set an exchange rate for a specific date.

        Args:
            from_currency: Source currency code (e.g., 'PYG')
            to_currency: Target currency code (e.g., 'BRL')
            rate: The exchange rate
            effective_date: When this rate becomes effective
            created_by: ID of the user who created this rate

        Returns:
            The ID of the new exchange rate record
        """
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        if rate <= 0:
            raise ValueError('Taxa de câmbio deve ser maior que zero')
        if from_currency == to_currency:
            raise ValueError('Moedas de origem e destino devem ser diferentes')

        with session_scope() as session:
            # Check if rate already exists for this date and currency pair
            existing = (
                session.query(ExchangeRate)
                .filter(
                    ExchangeRate.from_currency == from_currency,
                    ExchangeRate.to_currency == to_currency,
                    ExchangeRate.effective_date == effective_date
                )
                .first()
            )

            if existing:
                # Update existing rate
                existing.rate = Decimal(str(rate))
                existing.created_by = created_by
                return existing.id

            # Create new rate
            new_rate = ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=Decimal(str(rate)),
                effective_date=effective_date,
                created_by=created_by
            )
            session.add(new_rate)
            session.flush()
            return new_rate.id

    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        for_date: Optional[date] = None
    ) -> Optional[float]:
        """
        Get the exchange rate for a currency pair on a specific date.
        If no rate exists for the exact date, returns the most recent rate before that date.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            for_date: Date to get rate for (defaults to today)

        Returns:
            The exchange rate or None if not found
        """
        if for_date is None:
            for_date = date.today()

        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        # Same currency = rate of 1
        if from_currency == to_currency:
            return 1.0

        with session_scope() as session:
            rate = (
                session.query(ExchangeRate)
                .filter(
                    ExchangeRate.from_currency == from_currency,
                    ExchangeRate.to_currency == to_currency,
                    ExchangeRate.effective_date <= for_date
                )
                .order_by(desc(ExchangeRate.effective_date))
                .first()
            )

            if rate:
                return float(rate.rate)

            # Try reverse conversion
            reverse_rate = (
                session.query(ExchangeRate)
                .filter(
                    ExchangeRate.from_currency == to_currency,
                    ExchangeRate.to_currency == from_currency,
                    ExchangeRate.effective_date <= for_date
                )
                .order_by(desc(ExchangeRate.effective_date))
                .first()
            )

            if reverse_rate and float(reverse_rate.rate) != 0:
                return 1.0 / float(reverse_rate.rate)

            return None

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        for_date: Optional[date] = None
    ) -> Optional[float]:
        """
        Convert an amount from one currency to another.

        Args:
            amount: The amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            for_date: Date to use for exchange rate (defaults to today)

        Returns:
            The converted amount or None if no rate available
        """
        rate = self.get_rate(from_currency, to_currency, for_date)
        if rate is None:
            return None
        return amount * rate

    def list_rates(
        self,
        from_currency: Optional[str] = None,
        to_currency: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List exchange rate history.

        Args:
            from_currency: Filter by source currency (optional)
            to_currency: Filter by target currency (optional)
            limit: Maximum number of records to return

        Returns:
            List of exchange rate records
        """
        with session_scope() as session:
            query = session.query(ExchangeRate)

            if from_currency:
                query = query.filter(ExchangeRate.from_currency == from_currency.upper())
            if to_currency:
                query = query.filter(ExchangeRate.to_currency == to_currency.upper())

            rates = (
                query
                .order_by(desc(ExchangeRate.effective_date))
                .limit(limit)
                .all()
            )

            return [self._serialize_rate(rate) for rate in rates]

    def get_latest_rates(self) -> Dict[str, float]:
        """
        Get the latest exchange rates for all currency pairs.

        Returns:
            Dict mapping currency pairs to rates (e.g., {'PYG_BRL': 0.00072})
        """
        with session_scope() as session:
            # Get distinct currency pairs
            from sqlalchemy import func

            subquery = (
                session.query(
                    ExchangeRate.from_currency,
                    ExchangeRate.to_currency,
                    func.max(ExchangeRate.effective_date).label('max_date')
                )
                .group_by(ExchangeRate.from_currency, ExchangeRate.to_currency)
                .subquery()
            )

            latest_rates = (
                session.query(ExchangeRate)
                .join(
                    subquery,
                    (ExchangeRate.from_currency == subquery.c.from_currency) &
                    (ExchangeRate.to_currency == subquery.c.to_currency) &
                    (ExchangeRate.effective_date == subquery.c.max_date)
                )
                .all()
            )

            return {
                f"{rate.from_currency}_{rate.to_currency}": float(rate.rate)
                for rate in latest_rates
            }

    def _serialize_rate(self, rate: ExchangeRate) -> Dict[str, Any]:
        return {
            'id': rate.id,
            'from_currency': rate.from_currency,
            'to_currency': rate.to_currency,
            'rate': float(rate.rate),
            'effective_date': rate.effective_date.isoformat() if rate.effective_date else None,
            'created_at': rate.created_at.isoformat() if rate.created_at else None,
            'created_by': rate.created_by
        }


__all__ = ['ExchangeRateService']
