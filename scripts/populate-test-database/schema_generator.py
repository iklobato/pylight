"""Schema generator for e-commerce database."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import declarative_base, sessionmaker

from .db_utils import validate_connection
from .exceptions import ConnectionError, SchemaError

Base = declarative_base()


class User(Base):
    """Users table model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class Category(Base):
    """Categories table model."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    parent_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class Product(Base):
    """Products table model."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    sku = Column(String(50), nullable=False, unique=True)
    price = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    brand = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("TRUE"))
    dimensions = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class Address(Base):
    """Addresses table model."""

    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    street_address = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False)
    is_default = Column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class Order(Base):
    """Orders table model."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    order_date = Column(DateTime, nullable=False, server_default=text("NOW()"))
    status = Column(String(50), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class OrderItem(Base):
    """Order items table model."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class Review(Base):
    """Reviews table model."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    title = Column(String(200), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class Payment(Base):
    """Payments table model."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    payment_method = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False)
    transaction_id = Column(String(100), nullable=True, unique=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class Shipment(Base):
    """Shipments table model."""

    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    carrier = Column(String(50), nullable=False)
    tracking_number = Column(String(100), nullable=True, unique=True)
    status = Column(String(50), nullable=False)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class Inventory(Base):
    """Inventory table model."""

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    quantity_available = Column(Integer, nullable=False, server_default=text("0"))
    quantity_reserved = Column(Integer, nullable=False, server_default=text("0"))
    reorder_level = Column(Integer, nullable=False, server_default=text("10"))
    last_restocked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class SchemaGenerator:
    """Generator for e-commerce database schema."""

    def __init__(self, connection_string: str) -> None:
        """Initialize schema generator.

        Args:
            connection_string: PostgreSQL connection string

        Raises:
            ConnectionError: If connection validation fails
        """
        self.connection_string = connection_string

        # Validate connection
        try:
            validate_connection(connection_string)
        except ConnectionError:
            raise

        # Create engine and session
        self.engine = create_engine(connection_string, echo=False)
        self.Session = sessionmaker(bind=self.engine)

    def create_schema(self, drop_existing: bool = False) -> None:
        """Create e-commerce schema.

        Args:
            drop_existing: Whether to drop existing tables first

        Raises:
            SchemaError: If schema creation fails
        """
        try:
            if drop_existing:
                self.drop_schema()

            # Create all tables
            Base.metadata.create_all(self.engine)
        except Exception as e:
            raise SchemaError(
                f"Failed to create schema: {e}",
                sql_statement="CREATE TABLE statements",
            ) from e

    def drop_schema(self) -> None:
        """Drop all tables in schema.

        Raises:
            SchemaError: If schema drop fails
        """
        try:
            Base.metadata.drop_all(self.engine)
        except Exception as e:
            raise SchemaError(
                f"Failed to drop schema: {e}",
                sql_statement="DROP TABLE statements",
            ) from e

    def schema_exists(self) -> bool:
        """Check if schema already exists.

        Returns:
            True if schema exists, False otherwise
        """
        from sqlalchemy import inspect

        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "users",
            "categories",
            "products",
            "addresses",
            "orders",
            "order_items",
            "reviews",
            "payments",
            "shipments",
            "inventory",
        ]

        return all(table in tables for table in expected_tables)
