"""Database schema generation for test database."""

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Text,
    Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint, CheckConstraint,
    JSON, Index
)
from sqlalchemy.sql import func
from typing import Optional


def create_schema(connection_string: str, drop_existing: bool = True) -> None:
    """Create database schema with all tables, relationships, and constraints."""
    engine = create_engine(connection_string)
    metadata = MetaData()
    
    # Users table
    users = Table(
        'users', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('username', String(50), unique=True, nullable=False),
        Column('email', String(100), unique=True, nullable=False),
        Column('password_hash', String(255), nullable=False),
        Column('first_name', String(50)),
        Column('last_name', String(50)),
        Column('role', String(20), default='user', nullable=False),
        Column('is_active', Boolean, default=True, nullable=False),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now(), nullable=False),
        CheckConstraint("role IN ('user', 'admin', 'moderator')", name='check_user_role'),
        Index('idx_users_email', 'email'),
        Index('idx_users_username', 'username')
    )
    
    # Categories table (self-referential)
    categories = Table(
        'categories', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('name', String(100), nullable=False),
        Column('slug', String(100), unique=True, nullable=False),
        Column('description', Text),
        Column('parent_id', Integer, ForeignKey('categories.id'), nullable=True),
        Column('image_url', String(255)),
        Column('is_active', Boolean, default=True, nullable=False),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        Index('idx_categories_slug', 'slug'),
        Index('idx_categories_parent', 'parent_id')
    )
    
    # Products table
    products = Table(
        'products', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('name', String(255), nullable=False),
        Column('description', Text),
        Column('sku', String(50), unique=True, nullable=False),
        Column('price', Numeric(10, 2), nullable=False),
        Column('cost', Numeric(10, 2)),
        Column('category_id', Integer, ForeignKey('categories.id'), nullable=True),
        Column('brand', String(100)),
        Column('weight', Numeric(8, 2)),
        Column('dimensions', JSON),
        Column('is_active', Boolean, default=True, nullable=False),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now(), nullable=False),
        CheckConstraint("price > 0", name='check_product_price'),
        Index('idx_products_sku', 'sku'),
        Index('idx_products_category', 'category_id'),
        Index('idx_products_name', 'name')
    )
    
    # Addresses table
    addresses = Table(
        'addresses', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
        Column('type', String(20), nullable=False),
        Column('street_address', String(255), nullable=False),
        Column('city', String(100), nullable=False),
        Column('state', String(50)),
        Column('postal_code', String(20), nullable=False),
        Column('country', String(50), nullable=False),
        Column('is_default', Boolean, default=False, nullable=False),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        CheckConstraint("type IN ('shipping', 'billing', 'both')", name='check_address_type'),
        Index('idx_addresses_user', 'user_id')
    )
    
    # Orders table
    orders = Table(
        'orders', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
        Column('order_number', String(50), unique=True, nullable=False),
        Column('status', String(20), default='pending', nullable=False),
        Column('subtotal', Numeric(10, 2), nullable=False),
        Column('tax', Numeric(10, 2), default=0, nullable=False),
        Column('shipping_cost', Numeric(10, 2), default=0, nullable=False),
        Column('total', Numeric(10, 2), nullable=False),
        Column('shipping_address_id', Integer, ForeignKey('addresses.id'), nullable=True),
        Column('billing_address_id', Integer, ForeignKey('addresses.id'), nullable=True),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now(), nullable=False),
        CheckConstraint("status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')", name='check_order_status'),
        Index('idx_orders_user', 'user_id'),
        Index('idx_orders_number', 'order_number'),
        Index('idx_orders_status', 'status')
    )
    
    # OrderItems table
    order_items = Table(
        'order_items', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('order_id', Integer, ForeignKey('orders.id'), nullable=False),
        Column('product_id', Integer, ForeignKey('products.id'), nullable=False),
        Column('quantity', Integer, nullable=False, default=1),
        Column('unit_price', Numeric(10, 2), nullable=False),
        Column('total_price', Numeric(10, 2), nullable=False),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        CheckConstraint("quantity > 0", name='check_order_item_quantity'),
        Index('idx_order_items_order', 'order_id'),
        Index('idx_order_items_product', 'product_id')
    )
    
    # Reviews table
    reviews = Table(
        'reviews', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('product_id', Integer, ForeignKey('products.id'), nullable=False),
        Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
        Column('rating', Integer, nullable=False),
        Column('title', String(255)),
        Column('comment', Text),
        Column('is_verified_purchase', Boolean, default=False, nullable=False),
        Column('is_approved', Boolean, default=False, nullable=False),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now(), nullable=False),
        CheckConstraint("rating >= 1 AND rating <= 5", name='check_review_rating'),
        UniqueConstraint('product_id', 'user_id', name='unique_user_product_review'),
        Index('idx_reviews_product', 'product_id'),
        Index('idx_reviews_user', 'user_id')
    )
    
    # Payments table
    payments = Table(
        'payments', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('order_id', Integer, ForeignKey('orders.id'), unique=True, nullable=False),
        Column('payment_method', String(50), nullable=False),
        Column('amount', Numeric(10, 2), nullable=False),
        Column('status', String(20), default='pending', nullable=False),
        Column('transaction_id', String(100), unique=True, nullable=True),
        Column('processed_at', DateTime, nullable=True),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        CheckConstraint("payment_method IN ('credit_card', 'debit_card', 'paypal', 'bank_transfer')", name='check_payment_method'),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'refunded')", name='check_payment_status'),
        Index('idx_payments_order', 'order_id'),
        Index('idx_payments_transaction', 'transaction_id')
    )
    
    # Shipments table
    shipments = Table(
        'shipments', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('order_id', Integer, ForeignKey('orders.id'), unique=True, nullable=False),
        Column('carrier', String(50), nullable=False),
        Column('tracking_number', String(100), unique=True, nullable=True),
        Column('status', String(20), default='pending', nullable=False),
        Column('shipped_at', DateTime, nullable=True),
        Column('delivered_at', DateTime, nullable=True),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        CheckConstraint("carrier IN ('usps', 'fedex', 'ups', 'dhl')", name='check_shipment_carrier'),
        CheckConstraint("status IN ('pending', 'in_transit', 'delivered', 'lost')", name='check_shipment_status'),
        Index('idx_shipments_order', 'order_id'),
        Index('idx_shipments_tracking', 'tracking_number')
    )
    
    # Inventory table
    inventory = Table(
        'inventory', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('product_id', Integer, ForeignKey('products.id'), unique=True, nullable=False),
        Column('quantity_available', Integer, nullable=False, default=0),
        Column('quantity_reserved', Integer, nullable=False, default=0),
        Column('quantity_sold', Integer, nullable=False, default=0),
        Column('reorder_level', Integer, default=10, nullable=False),
        Column('last_restocked_at', DateTime, nullable=True),
        Column('created_at', DateTime, server_default=func.now(), nullable=False),
        Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now(), nullable=False),
        CheckConstraint("quantity_available >= 0", name='check_inventory_available'),
        CheckConstraint("quantity_reserved >= 0", name='check_inventory_reserved'),
        CheckConstraint("quantity_sold >= 0", name='check_inventory_sold'),
        Index('idx_inventory_product', 'product_id')
    )
    
    # Create all tables
    if drop_existing:
        metadata.drop_all(engine, checkfirst=True)
    
    metadata.create_all(engine)
    print(f"Schema created successfully in database")


def get_schema_sql(connection_string: str) -> str:
    """Generate SQL DDL statements for schema creation."""
    # This would generate SQL from the schema definition
    # For now, we use SQLAlchemy to create directly
    # This function can be extended to export SQL if needed
    pass

