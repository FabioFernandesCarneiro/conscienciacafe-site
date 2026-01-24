"""Commission Rate Service - manages seller commission rates."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..db import session_scope
from ..models import CommissionRate, CRMUser


class CommissionRateService:
    """Manages commission rates for sellers."""

    def set_rate(
        self,
        user_id: int,
        rate: float,
        start_date: date,
        created_by: Optional[int] = None
    ) -> int:
        """
        Set a new commission rate for a user.
        Closes any existing open rate period before creating the new one.

        Args:
            user_id: The seller's user ID
            rate: Commission percentage (e.g., 10.0 for 10%)
            start_date: When this rate becomes effective
            created_by: ID of the admin who created this rate

        Returns:
            The ID of the new commission rate record
        """
        if rate < 0 or rate > 100:
            raise ValueError('Taxa de comissão deve estar entre 0 e 100%')

        with session_scope() as session:
            # Verify user exists and is a seller
            user = session.get(CRMUser, user_id)
            if not user:
                raise ValueError('Usuário não encontrado')

            # Close any existing open rate (set end_date to day before new start)
            existing_open = (
                session.query(CommissionRate)
                .filter(
                    CommissionRate.user_id == user_id,
                    CommissionRate.end_date.is_(None)
                )
                .first()
            )

            if existing_open:
                # Close the previous period (day before new start)
                from datetime import timedelta
                existing_open.end_date = start_date - timedelta(days=1)

            # Create new rate
            new_rate = CommissionRate(
                user_id=user_id,
                rate=Decimal(str(rate)),
                start_date=start_date,
                end_date=None,
                created_by=created_by
            )
            session.add(new_rate)
            session.flush()
            return new_rate.id

    def get_current_rate(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the currently active commission rate for a user.

        Args:
            user_id: The seller's user ID

        Returns:
            Dict with rate info or None if no rate is set
        """
        return self.get_rate_for_date(user_id, date.today())

    def get_rate_for_date(self, user_id: int, for_date: date) -> Optional[Dict[str, Any]]:
        """
        Get the commission rate that was active on a specific date.

        Args:
            user_id: The seller's user ID
            for_date: The date to check

        Returns:
            Dict with rate info or None if no rate was active
        """
        with session_scope() as session:
            rate = (
                session.query(CommissionRate)
                .filter(
                    CommissionRate.user_id == user_id,
                    CommissionRate.start_date <= for_date,
                    (CommissionRate.end_date.is_(None) | (CommissionRate.end_date >= for_date))
                )
                .order_by(CommissionRate.start_date.desc())
                .first()
            )

            if not rate:
                return None

            return self._serialize_rate(rate)

    def list_rates(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get the complete history of commission rates for a user.

        Args:
            user_id: The seller's user ID

        Returns:
            List of rate records ordered by start_date desc
        """
        with session_scope() as session:
            rates = (
                session.query(CommissionRate)
                .filter(CommissionRate.user_id == user_id)
                .order_by(CommissionRate.start_date.desc())
                .all()
            )
            return [self._serialize_rate(rate) for rate in rates]

    def list_all_current_rates(self) -> List[Dict[str, Any]]:
        """
        Get current commission rates for all sellers.

        Returns:
            List of dicts with user info and their current rate
        """
        with session_scope() as session:
            # Get all sellers
            sellers = (
                session.query(CRMUser)
                .filter(CRMUser.role == 'vendedor', CRMUser.active.is_(True))
                .all()
            )

            result = []
            today = date.today()

            for seller in sellers:
                # Get current rate for this seller
                rate = (
                    session.query(CommissionRate)
                    .filter(
                        CommissionRate.user_id == seller.id,
                        CommissionRate.start_date <= today,
                        (CommissionRate.end_date.is_(None) | (CommissionRate.end_date >= today))
                    )
                    .order_by(CommissionRate.start_date.desc())
                    .first()
                )

                result.append({
                    'user_id': seller.id,
                    'username': seller.username,
                    'country': seller.country,
                    'current_rate': float(rate.rate) if rate else None,
                    'rate_start_date': rate.start_date.isoformat() if rate else None
                })

            return result

    def _serialize_rate(self, rate: CommissionRate) -> Dict[str, Any]:
        return {
            'id': rate.id,
            'user_id': rate.user_id,
            'rate': float(rate.rate),
            'start_date': rate.start_date.isoformat() if rate.start_date else None,
            'end_date': rate.end_date.isoformat() if rate.end_date else None,
            'created_at': rate.created_at.isoformat() if rate.created_at else None,
            'created_by': rate.created_by
        }


__all__ = ['CommissionRateService']
