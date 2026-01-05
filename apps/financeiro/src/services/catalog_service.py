"""New service layer using SQLAlchemy for catalog/orders."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..db import session_scope
from ..models import CoffeeProduct, CoffeePackagingPrice

PACKAGE_SIZES = ['250g', '500g', '1kg']


class CatalogService:
    def list_coffees(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        with session_scope() as session:
            query = session.query(CoffeeProduct)
            if not include_inactive:
                query = query.filter(CoffeeProduct.active.is_(True))
            coffees = query.order_by(CoffeeProduct.name).all()
            return [self._serialize_coffee(coffee) for coffee in coffees]

    def get_coffee(self, coffee_id: int) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            coffee = session.get(CoffeeProduct, coffee_id)
            return self._serialize_coffee(coffee) if coffee else None

    def create_coffee(self, data: Dict[str, Any], prices: Dict[str, Any]) -> int:
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
        existing = {price.package_size: price for price in coffee.prices}
        for size in PACKAGE_SIZES:
            raw_value = prices.get(size)
            if raw_value is None or raw_value == '':
                continue
            value = float(raw_value)
            if size in existing:
                existing[size].price = value
            else:
                session.add(CoffeePackagingPrice(coffee_id=coffee.id, package_size=size, price=value))

    def _serialize_coffee(self, coffee: CoffeeProduct) -> Dict[str, Any]:
        prices_map = {price.package_size: price.price for price in coffee.prices}
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
            'prices_map': prices_map,
        }


__all__ = ['CatalogService', 'PACKAGE_SIZES']
