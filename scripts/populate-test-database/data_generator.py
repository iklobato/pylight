"""Data generator for populating test database with realistic data."""

import random
from datetime import datetime, timedelta
from typing import Any

import psycopg2
from faker import Faker
from psycopg2.extras import Json, execute_batch

from .config import DataGenerationConfig
from .dependency_resolver import DependencyResolver
from .exceptions import DataGenerationError
from .utils import log_progress, log_success


class DataGenerator:
    """Generator for realistic test data using Faker."""

    def __init__(self, config: DataGenerationConfig) -> None:
        """Initialize data generator.

        Args:
            config: Data generation configuration
        """
        self.config = config
        self.connection_string = config.connection_string

        # Initialize Faker with seed
        if config.seed is not None:
            self.faker = Faker(seed=config.seed)
            random.seed(config.seed)
        else:
            self.faker = Faker()
            random.seed()

        self.generated_records: dict[str, int] = {}

    def generate_all(self) -> dict[str, int]:
        """Generate data for all tables in dependency order.

        Returns:
            Dictionary mapping table names to generated record counts

        Raises:
            DataGenerationError: If data generation fails
        """
        # Resolve dependency order dynamically
        try:
            resolver = DependencyResolver(self.connection_string)
            table_order = resolver.resolve_order()
        except Exception as e:
            # Fallback to hardcoded order if resolver fails
            table_order = [
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

        try:
            with psycopg2.connect(self.connection_string) as conn:
                # Start transaction
                conn.autocommit = False

                try:
                    for table_name in table_order:
                        count = self.generate_table(table_name, conn)
                        self.generated_records[table_name] = count

                    # Commit transaction
                    conn.commit()
                    log_success(
                        f"Data generation complete: {sum(self.generated_records.values())} records"
                    )
                except Exception as e:
                    # Rollback on failure
                    if self.config.cleanup_on_failure:
                        conn.rollback()
                        log_success("Transaction rolled back due to error")
                    raise DataGenerationError(
                        f"Failed to generate data: {e}",
                        table_name=getattr(e, "table_name", None),
                    ) from e

        except psycopg2.Error as e:
            raise DataGenerationError(f"Database error during data generation: {e}") from e

        return self.generated_records

    def generate_table(self, table_name: str, conn: psycopg2.extensions.connection) -> int:
        """Generate data for a single table.

        Args:
            table_name: Name of table to populate
            conn: Database connection

        Returns:
            Number of records generated

        Raises:
            DataGenerationError: If generation fails
        """
        count = self.config.get_record_count(table_name)

        if count == 0:
            return 0

        method_name = f"generate_{table_name}"
        if not hasattr(self, method_name):
            raise DataGenerationError(
                f"No generator method found for table '{table_name}'",
                table_name=table_name,
            )

        generator_method = getattr(self, method_name)
        records = generator_method(count, conn)

        log_progress(table_name, len(records), count)
        return len(records)

    def generate_users(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate user records.

        Args:
            count: Number of users to generate
            conn: Database connection

        Returns:
            List of generated user records
        """
        records = []
        seen_emails = set()
        max_retries = 10

        for i in range(count):
            retries = 0
            while retries < max_retries:
                try:
                    # Ensure unique email
                    email = self.faker.unique.email()
                    if email in seen_emails:
                        email = f"{self.faker.random_int(min=10000, max=99999)}.{email}"
                    seen_emails.add(email)

                    records.append(
                        {
                            "email": email,
                            "first_name": self.faker.first_name(),
                            "last_name": self.faker.last_name(),
                            "phone": self.faker.phone_number()[:20],  # Limit to 20 chars
                        }
                    )
                    break
                except Exception:
                    retries += 1
                    if retries >= max_retries:
                        raise DataGenerationError(
                            f"Failed to generate unique email after {max_retries} retries",
                            table_name="users",
                            record_number=i,
                        )

        # Bulk insert with retry on unique constraint violations
        with conn.cursor() as cur:
            try:
                execute_batch(
                    cur,
                    """
                    INSERT INTO users (email, first_name, last_name, phone)
                    VALUES (%(email)s, %(first_name)s, %(last_name)s, %(phone)s)
                    """,
                    records,
                    page_size=100,
                )
            except psycopg2.IntegrityError as e:
                if "unique" in str(e).lower():
                    # Retry individual inserts for failed records
                    for record in records:
                        retries = 0
                        while retries < max_retries:
                            try:
                                cur.execute(
                                    """
                                    INSERT INTO users (email, first_name, last_name, phone)
                                    VALUES (%(email)s, %(first_name)s, %(last_name)s, %(phone)s)
                                    """,
                                    record,
                                )
                                break
                            except psycopg2.IntegrityError:
                                # Generate new email
                                record["email"] = (
                                    f"{self.faker.random_int(min=10000, max=99999)}.{self.faker.email()}"
                                )
                                retries += 1
                                if retries >= max_retries:
                                    raise DataGenerationError(
                                        f"Failed to insert user after {max_retries} retries",
                                        table_name="users",
                                    )

        return records

    def generate_categories(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate category records.

        Args:
            count: Number of categories to generate
            conn: Database connection

        Returns:
            List of generated category records
        """
        records = []
        seen_names = set()

        for _ in range(count):
            # Ensure unique name
            name = self.faker.unique.word().capitalize() + " " + self.faker.word().capitalize()
            if len(name) > 100:
                name = name[:100]
            seen_names.add(name)

            records.append(
                {
                    "name": name,
                    "description": self.faker.text(max_nb_chars=500),
                    "parent_category_id": None,  # Will be updated later if needed
                }
            )

        # Bulk insert
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO categories (name, description, parent_category_id)
                VALUES (%(name)s, %(description)s, %(parent_category_id)s)
                """,
                records,
                page_size=100,
            )

        # Get inserted category IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories ORDER BY id")
            category_ids = [row[0] for row in cur.fetchall()]

        # Update some categories with parent references (optional)
        if len(category_ids) > 1:
            with conn.cursor() as cur:
                # Update 30% of categories to have parent
                num_with_parent = int(len(category_ids) * 0.3)
                for i in range(1, min(num_with_parent + 1, len(category_ids))):
                    parent_id = random.choice(category_ids[:i])
                    cur.execute(
                        "UPDATE categories SET parent_category_id = %s WHERE id = %s",
                        (parent_id, category_ids[i]),
                    )

        return records

    def generate_products(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate product records.

        Args:
            count: Number of products to generate
            conn: Database connection

        Returns:
            List of generated product records
        """
        # Get category IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories")
            category_ids = [row[0] for row in cur.fetchall()]

        if not category_ids:
            raise DataGenerationError(
                "No categories found. Categories must be generated before products.",
                table_name="products",
            )

        records = []
        seen_skus = set()

        for _ in range(count):
            # Ensure unique SKU
            sku = f"PROD-{self.faker.unique.random_int(min=10000, max=99999)}"
            seen_skus.add(sku)

            # Generate dimensions JSON
            dimensions = Json(
                {
                    "width": round(random.uniform(5.0, 50.0), 2),
                    "height": round(random.uniform(5.0, 50.0), 2),
                    "depth": round(random.uniform(5.0, 50.0), 2),
                }
            )

            records.append(
                {
                    "name": self.faker.catch_phrase()[:200],
                    "description": self.faker.text(max_nb_chars=1000),
                    "sku": sku,
                    "price": round(random.uniform(9.99, 999.99), 2),
                    "cost": round(random.uniform(5.0, 500.0), 2),
                    "category_id": random.choice(category_ids),
                    "brand": self.faker.company()[:100],
                    "is_active": self.faker.boolean(chance_of_getting_true=90),
                    "dimensions": dimensions,
                }
            )

        # Bulk insert with retry on unique constraint violations
        with conn.cursor() as cur:
            try:
                execute_batch(
                    cur,
                    """
                    INSERT INTO products (name, description, sku, price, cost, category_id, brand, is_active, dimensions)
                    VALUES (%(name)s, %(description)s, %(sku)s, %(price)s, %(cost)s, %(category_id)s, %(brand)s, %(is_active)s, %(dimensions)s)
                    """,
                    records,
                    page_size=100,
                )
            except psycopg2.IntegrityError as e:
                if "unique" in str(e).lower() and "sku" in str(e).lower():
                    # Retry individual inserts for failed records
                    max_retries = 10
                    for record in records:
                        retries = 0
                        while retries < max_retries:
                            try:
                                cur.execute(
                                    """
                                    INSERT INTO products (name, description, sku, price, cost, category_id, brand, is_active, dimensions)
                                    VALUES (%(name)s, %(description)s, %(sku)s, %(price)s, %(cost)s, %(category_id)s, %(brand)s, %(is_active)s, %(dimensions)s)
                                    """,
                                    record,
                                )
                                break
                            except psycopg2.IntegrityError:
                                # Generate new unique SKU
                                record["sku"] = (
                                    f"PROD-{self.faker.unique.random_int(min=10000, max=99999)}"
                                )
                                retries += 1
                                if retries >= max_retries:
                                    raise DataGenerationError(
                                        f"Failed to insert product after {max_retries} retries",
                                        table_name="products",
                                    )
                else:
                    raise

        return records

    def generate_addresses(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate address records.

        Args:
            count: Number of addresses to generate
            conn: Database connection

        Returns:
            List of generated address records
        """
        # Get user IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users")
            user_ids = [row[0] for row in cur.fetchall()]

        if not user_ids:
            raise DataGenerationError(
                "No users found. Users must be generated before addresses.",
                table_name="addresses",
            )

        records = []

        for _ in range(count):
            country = self.faker.country()
            if len(country) > 50:
                country = country[:50]

            records.append(
                {
                    "user_id": random.choice(user_ids),
                    "street_address": self.faker.street_address()[:200],
                    "city": self.faker.city()[:100],
                    "state": self.faker.state()[:50],
                    "postal_code": self.faker.zipcode()[:20],
                    "country": country,
                    "is_default": self.faker.boolean(chance_of_getting_true=20),
                }
            )

        # Bulk insert
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO addresses (user_id, street_address, city, state, postal_code, country, is_default)
                VALUES (%(user_id)s, %(street_address)s, %(city)s, %(state)s, %(postal_code)s, %(country)s, %(is_default)s)
                """,
                records,
                page_size=100,
            )

        return records

    def generate_orders(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate order records.

        Args:
            count: Number of orders to generate
            conn: Database connection

        Returns:
            List of generated order records
        """
        # Get user and address IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users")
            user_ids = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT id FROM addresses")
            address_ids = [row[0] for row in cur.fetchall()]

        if not user_ids or not address_ids:
            raise DataGenerationError(
                "No users or addresses found. Users and addresses must be generated before orders.",
                table_name="orders",
            )

        statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        records = []

        for _ in range(count):
            order_date = self.faker.date_time_between(start_date="-1y", end_date="now")

            records.append(
                {
                    "user_id": random.choice(user_ids),
                    "address_id": random.choice(address_ids),
                    "order_date": order_date,
                    "status": random.choice(statuses),
                    "total_amount": round(random.uniform(10.0, 1000.0), 2),
                }
            )

        # Bulk insert
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO orders (user_id, address_id, order_date, status, total_amount)
                VALUES (%(user_id)s, %(address_id)s, %(order_date)s, %(status)s, %(total_amount)s)
                """,
                records,
                page_size=100,
            )

        return records

    def generate_order_items(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate order item records.

        Args:
            count: Number of order items to generate
            conn: Database connection

        Returns:
            List of generated order item records
        """
        # Get order and product IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM orders")
            order_ids = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT id, price FROM products")
            products = [(row[0], float(row[1])) for row in cur.fetchall()]

        if not order_ids or not products:
            raise DataGenerationError(
                "No orders or products found. Orders and products must be generated before order_items.",
                table_name="order_items",
            )

        records = []

        for _ in range(count):
            order_id = random.choice(order_ids)
            product_id, product_price = random.choice(products)
            quantity = random.randint(1, 10)
            unit_price = round(product_price * random.uniform(0.9, 1.1), 2)
            subtotal = round(quantity * unit_price, 2)

            records.append(
                {
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "subtotal": subtotal,
                }
            )

        # Bulk insert
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
                VALUES (%(order_id)s, %(product_id)s, %(quantity)s, %(unit_price)s, %(subtotal)s)
                """,
                records,
                page_size=100,
            )

        return records

    def generate_reviews(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate review records.

        Args:
            count: Number of reviews to generate
            conn: Database connection

        Returns:
            List of generated review records
        """
        # Get user and product IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users")
            user_ids = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT id FROM products")
            product_ids = [row[0] for row in cur.fetchall()]

        if not user_ids or not product_ids:
            raise DataGenerationError(
                "No users or products found. Users and products must be generated before reviews.",
                table_name="reviews",
            )

        records = []

        for _ in range(count):
            records.append(
                {
                    "user_id": random.choice(user_ids),
                    "product_id": random.choice(product_ids),
                    "rating": random.randint(1, 5),
                    "title": self.faker.sentence(nb_words=6)[:200],
                    "comment": self.faker.text(max_nb_chars=500),
                }
            )

        # Bulk insert
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO reviews (user_id, product_id, rating, title, comment)
                VALUES (%(user_id)s, %(product_id)s, %(rating)s, %(title)s, %(comment)s)
                """,
                records,
                page_size=100,
            )

        return records

    def generate_payments(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate payment records.

        Args:
            count: Number of payments to generate
            conn: Database connection

        Returns:
            List of generated payment records
        """
        # Get order IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id, total_amount FROM orders")
            orders = [(row[0], float(row[1])) for row in cur.fetchall()]

        if not orders:
            raise DataGenerationError(
                "No orders found. Orders must be generated before payments.",
                table_name="payments",
            )

        payment_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
        statuses = ["pending", "completed", "failed", "refunded"]
        records = []
        seen_transaction_ids = set()

        for _ in range(count):
            order_id, order_amount = random.choice(orders)

            # Generate unique transaction ID
            transaction_id = None
            if random.random() > 0.1:  # 90% have transaction ID
                transaction_id = f"TXN-{self.faker.unique.random_int(min=100000, max=999999)}"
                seen_transaction_ids.add(transaction_id)

            status = random.choice(statuses)
            processed_at = None
            if status == "completed":
                processed_at = self.faker.date_time_between(start_date="-1y", end_date="now")

            records.append(
                {
                    "order_id": order_id,
                    "payment_method": random.choice(payment_methods),
                    "amount": round(order_amount, 2),
                    "status": status,
                    "transaction_id": transaction_id,
                    "processed_at": processed_at,
                }
            )

        # Bulk insert
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO payments (order_id, payment_method, amount, status, transaction_id, processed_at)
                VALUES (%(order_id)s, %(payment_method)s, %(amount)s, %(status)s, %(transaction_id)s, %(processed_at)s)
                """,
                records,
                page_size=100,
            )

        return records

    def generate_shipments(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate shipment records.

        Args:
            count: Number of shipments to generate
            conn: Database connection

        Returns:
            List of generated shipment records
        """
        # Get order IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM orders")
            order_ids = [row[0] for row in cur.fetchall()]

        if not order_ids:
            raise DataGenerationError(
                "No orders found. Orders must be generated before shipments.",
                table_name="shipments",
            )

        carriers = ["ups", "fedex", "usps", "dhl"]
        statuses = ["pending", "in_transit", "delivered", "lost"]
        records = []
        seen_tracking_numbers = set()

        for _ in range(count):
            order_id = random.choice(order_ids)

            # Generate unique tracking number
            tracking_number = None
            if random.random() > 0.1:  # 90% have tracking number
                tracking_number = f"TRACK-{self.faker.unique.random_int(min=1000000, max=9999999)}"
                seen_tracking_numbers.add(tracking_number)

            status = random.choice(statuses)
            shipped_at = None
            delivered_at = None

            if status in ["in_transit", "delivered"]:
                shipped_at = self.faker.date_time_between(start_date="-1y", end_date="now")
            if status == "delivered":
                delivered_at = (
                    shipped_at + timedelta(days=random.randint(1, 7)) if shipped_at else None
                )

            records.append(
                {
                    "order_id": order_id,
                    "carrier": random.choice(carriers),
                    "tracking_number": tracking_number,
                    "status": status,
                    "shipped_at": shipped_at,
                    "delivered_at": delivered_at,
                }
            )

        # Bulk insert
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO shipments (order_id, carrier, tracking_number, status, shipped_at, delivered_at)
                VALUES (%(order_id)s, %(carrier)s, %(tracking_number)s, %(status)s, %(shipped_at)s, %(delivered_at)s)
                """,
                records,
                page_size=100,
            )

        return records

    def generate_inventory(
        self, count: int, conn: psycopg2.extensions.connection
    ) -> list[dict[str, Any]]:
        """Generate inventory records.

        Args:
            count: Number of inventory records to generate
            conn: Database connection

        Returns:
            List of generated inventory records
        """
        # Get product IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products")
            product_ids = [row[0] for row in cur.fetchall()]

        if not product_ids:
            raise DataGenerationError(
                "No products found. Products must be generated before inventory.",
                table_name="inventory",
            )

        # Limit to available products (one-to-one relationship)
        count = min(count, len(product_ids))
        selected_product_ids = random.sample(product_ids, count)

        records = []

        for product_id in selected_product_ids:
            quantity_available = random.randint(0, 1000)
            quantity_reserved = random.randint(0, min(100, quantity_available))
            reorder_level = random.randint(10, 50)

            last_restocked_at = None
            if random.random() > 0.3:  # 70% have restock date
                last_restocked_at = self.faker.date_time_between(start_date="-6m", end_date="now")

            records.append(
                {
                    "product_id": product_id,
                    "quantity_available": quantity_available,
                    "quantity_reserved": quantity_reserved,
                    "reorder_level": reorder_level,
                    "last_restocked_at": last_restocked_at,
                }
            )

        # Bulk insert
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO inventory (product_id, quantity_available, quantity_reserved, reorder_level, last_restocked_at)
                VALUES (%(product_id)s, %(quantity_available)s, %(quantity_reserved)s, %(reorder_level)s, %(last_restocked_at)s)
                """,
                records,
                page_size=100,
            )

        return records
