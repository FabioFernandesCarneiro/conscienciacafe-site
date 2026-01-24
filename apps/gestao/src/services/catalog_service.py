"""New service layer using SQLAlchemy for catalog/orders."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..db import session_scope
from ..models import CoffeeProduct, CoffeePackagingPrice, CURRENCIES

PACKAGE_SIZES = ['250g', '500g', '1kg']


class CatalogService:
    def list_coffees(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        with session_scope() as session:
            query = session.query(CoffeeProduct)
            if not include_inactive:
                query = query.filter(CoffeeProduct.active.is_(True))
            # Ordenar: ativos primeiro (desc), depois por nome alfabético
            coffees = query.order_by(CoffeeProduct.active.desc(), CoffeeProduct.name).all()
            return [self._serialize_coffee(coffee) for coffee in coffees]

    def get_coffee(self, coffee_id: int) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            coffee = session.get(CoffeeProduct, coffee_id)
            return self._serialize_coffee(coffee) if coffee else None

    def get_price(
        self,
        coffee_id: int,
        package_size: str,
        currency: str = 'BRL'
    ) -> Optional[float]:
        """
        Get the price for a specific coffee, package size, and currency.

        Args:
            coffee_id: The coffee product ID
            package_size: Package size (e.g., '250g', '500g', '1kg')
            currency: Currency code (default 'BRL')

        Returns:
            The price or None if not found
        """
        with session_scope() as session:
            price = (
                session.query(CoffeePackagingPrice)
                .filter(
                    CoffeePackagingPrice.coffee_id == coffee_id,
                    CoffeePackagingPrice.package_size == package_size,
                    CoffeePackagingPrice.currency == currency.upper()
                )
                .first()
            )
            return float(price.price) if price else None

    def create_coffee(self, data: Dict[str, Any], prices: Dict[str, Any]) -> int:
        """
        Create a new coffee product.

        Args:
            data: Coffee product data
            prices: Prices by currency and size. Can be:
                   - Simple format (BRL only): {'250g': 50, '500g': 90, '1kg': 160}
                   - Multi-currency format: {'BRL': {'250g': 50, ...}, 'PYG': {'250g': 35000, ...}}

        Returns:
            The new coffee product ID
        """
        with session_scope() as session:
            coffee = CoffeeProduct(
                name=data['name'],
                variety=data.get('variety'),
                farm_name=data.get('farm_name'),
                region=data.get('region'),
                process=data.get('process'),
                sensorial_notes=data.get('sensorial_notes'),
                sca_score=data.get('sca_score'),
                active=bool(data.get('active', True))
            )
            session.add(coffee)
            session.flush()
            self._persist_prices(session, coffee, prices)
            return coffee.id

    def update_coffee(self, coffee_id: int, data: Dict[str, Any], prices: Dict[str, Any]) -> None:
        """
        Update a coffee product.

        Args:
            coffee_id: The coffee product ID
            data: Coffee product data
            prices: Prices by currency and size (same format as create_coffee)
        """
        with session_scope() as session:
            coffee = session.get(CoffeeProduct, coffee_id)
            if not coffee:
                raise ValueError('Café não encontrado')
            for field in ['name', 'variety', 'farm_name', 'region', 'process', 'sensorial_notes', 'sca_score']:
                if field in data:
                    setattr(coffee, field, data[field])
            if 'active' in data:
                coffee.active = bool(data['active'])
            self._persist_prices(session, coffee, prices)

    def ensure_default_product(self, name: str = 'Café Padrão Importação') -> int:
        """Always return product ID 1 (default product for imports)."""
        return 1

    def _persist_prices(self, session: Session, coffee: CoffeeProduct, prices: Dict[str, Any]) -> None:
        """
        Persist prices for a coffee product.

        Supports two formats:
        - Simple (BRL only): {'250g': 50, '500g': 90}
        - Multi-currency: {'BRL': {'250g': 50}, 'PYG': {'250g': 35000}}
        """
        # Detect format: if first value is a dict, it's multi-currency
        is_multi_currency = any(
            isinstance(v, dict) for v in prices.values() if v is not None
        )

        if is_multi_currency:
            self._persist_multi_currency_prices(session, coffee, prices)
        else:
            # Legacy single-currency format (assume BRL)
            self._persist_single_currency_prices(session, coffee, prices, 'BRL')

    def _persist_single_currency_prices(
        self,
        session: Session,
        coffee: CoffeeProduct,
        prices: Dict[str, Any],
        currency: str
    ) -> None:
        """Persist prices for a single currency."""
        existing = {
            price.package_size: price
            for price in coffee.prices
            if price.currency == currency
        }

        for size in PACKAGE_SIZES:
            raw_value = prices.get(size)
            if raw_value is None or raw_value == '':
                continue
            value = float(raw_value)
            if size in existing:
                existing[size].price = value
            else:
                session.add(CoffeePackagingPrice(
                    coffee_id=coffee.id,
                    package_size=size,
                    currency=currency,
                    price=value
                ))

    def _persist_multi_currency_prices(
        self,
        session: Session,
        coffee: CoffeeProduct,
        prices: Dict[str, Dict[str, Any]]
    ) -> None:
        """Persist prices for multiple currencies."""
        # Build map of existing prices by (currency, size)
        existing = {
            (price.currency, price.package_size): price
            for price in coffee.prices
        }

        for currency in CURRENCIES:
            currency_prices = prices.get(currency, {})
            if not currency_prices:
                continue

            for size in PACKAGE_SIZES:
                raw_value = currency_prices.get(size)
                if raw_value is None or raw_value == '':
                    continue

                value = float(raw_value)
                key = (currency, size)

                if key in existing:
                    existing[key].price = value
                else:
                    session.add(CoffeePackagingPrice(
                        coffee_id=coffee.id,
                        package_size=size,
                        currency=currency,
                        price=value
                    ))

    def _serialize_coffee(self, coffee: CoffeeProduct) -> Dict[str, Any]:
        """
        Serialize a coffee product.

        Returns prices in both formats for backward compatibility:
        - prices_map: Legacy format (BRL only): {'250g': 50, ...}
        - prices_by_currency: Multi-currency format: {'BRL': {'250g': 50}, 'PYG': {...}}
        """
        # Build multi-currency prices map
        prices_by_currency: Dict[str, Dict[str, float]] = {currency: {} for currency in CURRENCIES}

        for price in coffee.prices:
            currency = price.currency or 'BRL'
            if currency in prices_by_currency:
                prices_by_currency[currency][price.package_size] = price.price

        # Legacy prices_map (BRL only for backward compatibility)
        prices_map = prices_by_currency.get('BRL', {})

        return {
            'id': coffee.id,
            'name': coffee.name,
            'variety': coffee.variety,
            'farm_name': coffee.farm_name,
            'region': coffee.region,
            'process': coffee.process,
            'sensorial_notes': coffee.sensorial_notes,
            'sca_score': coffee.sca_score,
            'active': coffee.active,
            'prices_map': prices_map,  # Legacy: BRL only
            'prices_map_brl': prices_by_currency.get('BRL', {}),
            'prices_map_pyg': prices_by_currency.get('PYG', {}),
            'prices_by_currency': prices_by_currency,  # New: all currencies
        }


__all__ = ['CatalogService', 'PACKAGE_SIZES', 'CURRENCIES']
