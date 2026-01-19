"""SQLAlchemy models for Consciência Café."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, Date, DateTime, ForeignKey,
    UniqueConstraint, Numeric
)
from sqlalchemy.orm import relationship, backref

from .db import Base


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
    __table_args__ = (UniqueConstraint('coffee_id', 'package_size', name='uq_coffee_package'),)

    id = Column(Integer, primary_key=True)
    coffee_id = Column(Integer, ForeignKey('coffee_products.id', ondelete='CASCADE'), nullable=False)
    package_size = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    coffee = relationship('CoffeeProduct', back_populates='prices')


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('crm_leads.id'))
    client_id = Column(Integer)  # Foreign key removida temporariamente
    order_date = Column(Date, nullable=False)
    currency = Column(String, default='BRL')
    notes = Column(Text)
    source = Column(String)
    total_amount = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship('OrderItem', cascade='all, delete-orphan', back_populates='order')
    lead = relationship('CRMLead')


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
    role = Column(String, default='admin')
    active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
    owner = Column(String)
    notes = Column(Text)
    google_place_id = Column(String, unique=True)
    is_customer = Column(Boolean, default=False)
    converted_account_id = Column(Integer, ForeignKey('clients.id'))
    last_stage_change = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interactions = relationship('CRMInteraction', cascade='all, delete-orphan', back_populates='lead')


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


__all__ = [
    'CoffeeProduct', 'CoffeePackagingPrice', 'Order', 'OrderItem',
    'CRMUser', 'Account', 'Category', 'Client', 'Transaction',
    'ImportBatch', 'MLTrainingData', 'CRMLead', 'CRMInteraction'
]
