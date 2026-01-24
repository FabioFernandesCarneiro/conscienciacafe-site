"""SQLAlchemy models for Consciência Café."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, Date, DateTime, ForeignKey,
    UniqueConstraint, Numeric, Index
)
from sqlalchemy.orm import relationship, backref

from .db import Base

# Constants
CURRENCIES = ['BRL', 'PYG']
COUNTRIES = ['BR', 'PY']


class CoffeeProduct(Base):
    __tablename__ = 'coffee_products'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    variety = Column(String)
    farm_name = Column(String)
    region = Column(String)
    process = Column(String)
    sensorial_notes = Column(Text)
    sca_score = Column(Float)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prices = relationship('CoffeePackagingPrice', cascade='all, delete-orphan', back_populates='coffee')


class CoffeePackagingPrice(Base):
    __tablename__ = 'coffee_packaging_prices'
    __table_args__ = (
        UniqueConstraint('coffee_id', 'package_size', 'currency', name='uq_coffee_package_currency'),
    )

    id = Column(Integer, primary_key=True)
    coffee_id = Column(Integer, ForeignKey('coffee_products.id', ondelete='CASCADE'), nullable=False)
    package_size = Column(String, nullable=False)
    currency = Column(String(3), default='BRL', nullable=False)  # 'BRL' or 'PYG'
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    coffee = relationship('CoffeeProduct', back_populates='prices')


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('crm_leads.id'))
    client_id = Column(Integer)  # Foreign key removida temporariamente
    user_id = Column(Integer, ForeignKey('crm_users.id'), nullable=True)  # Owner/seller of the order
    order_date = Column(Date, nullable=False)
    currency = Column(String, default='BRL')
    notes = Column(Text)
    source = Column(String)
    total_amount = Column(Float, default=0)
    paid_amount = Column(Numeric(15, 2), default=0)  # Amount already paid
    payment_status = Column(String, default='pending')  # 'pending', 'partial', 'paid'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship('OrderItem', cascade='all, delete-orphan', back_populates='order')
    lead = relationship('CRMLead')
    user = relationship('CRMUser', back_populates='orders', foreign_keys=[user_id])
    commission = relationship('Commission', back_populates='order', uselist=False)


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    coffee_id = Column(Integer, ForeignKey('coffee_products.id'))
    description = Column(Text)
    package_size = Column(String)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship('Order', back_populates='items')
    coffee = relationship('CoffeeProduct')


class CRMUser(Base):
    __tablename__ = 'crm_users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String, default='admin')  # 'admin', 'user', 'vendedor'
    country = Column(String(2), nullable=True)  # 'BR' or 'PY' (required if role='vendedor')
    active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    leads = relationship('CRMLead', back_populates='user', foreign_keys='CRMLead.user_id')
    orders = relationship('Order', back_populates='user', foreign_keys='Order.user_id')
    commission_rates = relationship('CommissionRate', back_populates='user', foreign_keys='CommissionRate.user_id')
    commissions = relationship('Commission', back_populates='user', foreign_keys='Commission.user_id')

    @property
    def is_seller(self) -> bool:
        return self.role == 'vendedor'

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # checking, credit_card, cash
    bank_name = Column(String)
    account_number = Column(String)
    balance = Column(Numeric(15, 2), default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = relationship('Transaction', back_populates='account')


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # revenue, expense
    parent_category_id = Column(Integer, ForeignKey('categories.id'))
    ml_keywords = Column(Text)
    color = Column(String, default='#6c757d')
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship('Transaction', back_populates='category')
    children = relationship('Category', backref=backref('parent', remote_side=[id]))


class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    omie_id = Column(Integer, unique=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    document = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    type = Column(String, nullable=False)  # revenue, expense, transfer
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    # Transfer fields
    transfer_id = Column(Integer, ForeignKey('transactions.id'))
    
    # ML fields
    original_description = Column(Text)
    ml_confidence = Column(Numeric(3, 2))
    user_corrected = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship('Account', back_populates='transactions')
    category = relationship('Category', back_populates='transactions')
    transfer_pair = relationship('Transaction', remote_side=[id], post_update=True)


class ImportBatch(Base):
    __tablename__ = 'import_batches'

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    source_file = Column(String)
    import_date = Column(DateTime, default=datetime.utcnow)
    total_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    status = Column(String, default='processing')
    error_log = Column(Text)
    metadata_json = Column('metadata', Text)  # Renamed to avoid SQLAlchemy reserved word


class MLTrainingData(Base):
    __tablename__ = 'ml_training_data'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    original_description = Column(Text, nullable=False)
    normalized_description = Column(Text)
    predicted_category_id = Column(Integer, ForeignKey('categories.id'))
    actual_category_id = Column(Integer, ForeignKey('categories.id'))
    predicted_client_id = Column(Integer, ForeignKey('clients.id'))
    actual_client_id = Column(Integer, ForeignKey('clients.id'))
    confidence = Column(Numeric(3, 2))
    user_corrected = Column(Boolean, default=False)
    training_date = Column(DateTime, default=datetime.utcnow)


class CRMLead(Base):
    __tablename__ = 'crm_leads'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)
    status = Column(String, default='nao_contactado')
    source = Column(String)
    search_keyword = Column(String)
    search_city = Column(String)
    address_line = Column(String)
    address_number = Column(String)
    address_complement = Column(String)
    neighborhood = Column(String)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    phone = Column(String)
    whatsapp = Column(String)
    email = Column(String)
    instagram = Column(String)
    website = Column(String)
    primary_contact_name = Column(String)
    owner = Column(String)  # Legacy field, kept for backward compatibility
    user_id = Column(Integer, ForeignKey('crm_users.id'), nullable=True)  # Seller who owns this lead
    notes = Column(Text)
    google_place_id = Column(String, unique=True)
    is_customer = Column(Boolean, default=False)
    converted_account_id = Column(Integer, ForeignKey('clients.id'))
    last_stage_change = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interactions = relationship('CRMInteraction', cascade='all, delete-orphan', back_populates='lead')
    user = relationship('CRMUser', back_populates='leads', foreign_keys=[user_id])


class CRMInteraction(Base):
    __tablename__ = 'crm_interactions'

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('crm_leads.id', ondelete='CASCADE'), nullable=False)
    interaction_type = Column(String)
    channel = Column(String)
    subject = Column(String)
    notes = Column(Text)
    interaction_at = Column(DateTime, default=datetime.utcnow)
    follow_up_at = Column(DateTime)
    owner = Column(String)
    metadata_json = Column('metadata', Text)  # Renamed to avoid SQLAlchemy reserved word
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship('CRMLead', back_populates='interactions')


class CommissionRate(Base):
    """Commission rate per seller per period. The rate_applied is frozen when commission is created."""
    __tablename__ = 'commission_rates'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('crm_users.id'), nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)  # Percentage (e.g., 10.00 = 10%)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # NULL = currently active
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('crm_users.id'))

    user = relationship('CRMUser', foreign_keys=[user_id], back_populates='commission_rates')
    creator = relationship('CRMUser', foreign_keys=[created_by])

    __table_args__ = (
        Index('ix_commission_rates_user_date', 'user_id', 'start_date'),
    )


class Commission(Base):
    """Commission record with frozen amount at time of order payment."""
    __tablename__ = 'commissions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('crm_users.id'), nullable=False)  # Seller
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)  # Frozen commission amount
    amount_brl = Column(Numeric(15, 2))  # Converted to BRL if currency != BRL
    rate_applied = Column(Numeric(5, 2), nullable=False)  # Frozen rate at calculation time
    status = Column(String, default='pending')  # 'pending', 'paid'
    payment_date = Column(Date)
    payment_reference = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('CRMUser', back_populates='commissions', foreign_keys=[user_id])
    order = relationship('Order', back_populates='commission')

    __table_args__ = (
        Index('ix_commissions_user_status', 'user_id', 'status'),
        Index('ix_commissions_order', 'order_id'),
    )


class ExchangeRate(Base):
    """Exchange rate history for currency conversion."""
    __tablename__ = 'exchange_rates'

    id = Column(Integer, primary_key=True)
    from_currency = Column(String(3), nullable=False)  # e.g., 'PYG'
    to_currency = Column(String(3), nullable=False)    # e.g., 'BRL'
    rate = Column(Numeric(15, 6), nullable=False)
    effective_date = Column(Date, nullable=False)
    created_by = Column(Integer, ForeignKey('crm_users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship('CRMUser', foreign_keys=[created_by])

    __table_args__ = (
        UniqueConstraint('from_currency', 'to_currency', 'effective_date', name='uq_exchange_rate_date'),
        Index('ix_exchange_rates_currencies_date', 'from_currency', 'to_currency', 'effective_date'),
    )


__all__ = [
    'CoffeeProduct', 'CoffeePackagingPrice', 'Order', 'OrderItem',
    'CRMUser', 'Account', 'Category', 'Client', 'Transaction',
    'ImportBatch', 'MLTrainingData', 'CRMLead', 'CRMInteraction',
    'CommissionRate', 'Commission', 'ExchangeRate',
    'CURRENCIES', 'COUNTRIES'
]
