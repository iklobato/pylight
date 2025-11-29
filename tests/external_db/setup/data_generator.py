"""Test data generation using Faker for realistic test data."""

import random
import json
from faker import Faker
from faker.providers import BaseProvider
import psycopg2
from psycopg2.extras import execute_batch, Json
from typing import List, Dict, Any
from decimal import Decimal


class ProductProvider(BaseProvider):
    """Custom Faker provider for product-related data."""
    
    def product_name(self) -> str:
        """Generate realistic product name."""
        categories = [
            "Laptop", "Smartphone", "Tablet", "Headphones", "Monitor",
            "Keyboard", "Mouse", "Speaker", "Camera", "Watch"
        ]
        brands = ["TechCorp", "DigitalPro", "SmartTech", "EliteGear", "ProDevice"]
        return f"{random.choice(brands)} {random.choice(categories)} {random.randint(100, 9999)}"
    
    def sku(self) -> str:
        """Generate SKU."""
        return f"SKU-{random.randint(10000, 99999)}"
    
    def product_price(self) -> Decimal:
        """Generate realistic product price."""
        return Decimal(str(round(random.uniform(10.0, 2000.0), 2)))


class OrderProvider(BaseProvider):
    """Custom Faker provider for order-related data."""
    
    def order_number(self) -> str:
        """Generate order number."""
        return f"ORD-{random.randint(100000, 999999)}"
    
    def order_status(self) -> str:
        """Generate order status."""
        return random.choice(['pending', 'processing', 'shipped', 'delivered', 'cancelled'])


class DataGenerator:
    """Generates realistic test data for all tables."""
    
    def __init__(self, connection_string: str, seed: int = 42):
        self.connection_string = connection_string
        self.fake = Faker()
        self.fake.add_provider(ProductProvider)
        self.fake.add_provider(OrderProvider)
        Faker.seed(seed)
        random.seed(seed)
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection."""
        self.conn = psycopg2.connect(self.connection_string)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def generate_users(self, count: int = 1000) -> List[int]:
        """Generate users and return list of user IDs."""
        user_ids = []
        roles = ['user', 'admin', 'moderator']
        
        data = []
        for i in range(count):
            user_ids.append(i + 1)
            data.append((
                f"user_{i+1}",
                self.fake.email(),
                self.fake.password(),
                self.fake.first_name(),
                self.fake.last_name(),
                random.choice(roles),
                random.choice([True, False])  # is_active
            ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {count} users")
        return user_ids
    
    def generate_categories(self, count: int = 50) -> List[int]:
        """Generate categories with hierarchy and return list of category IDs."""
        category_ids = []
        data = []
        
        # Generate root categories (no parent)
        root_count = count // 3
        for i in range(root_count):
            category_ids.append(i + 1)
            data.append((
                self.fake.word().capitalize() + " Category",
                f"category-{i+1}",
                self.fake.text(max_nb_chars=200),
                None,  # parent_id
                self.fake.url() if random.random() > 0.5 else None,
                True
            ))
        
        # Generate child categories
        for i in range(root_count, count):
            category_ids.append(i + 1)
            parent_id = random.choice(category_ids[:root_count])
            data.append((
                self.fake.word().capitalize() + " Subcategory",
                f"subcategory-{i+1}",
                self.fake.text(max_nb_chars=200),
                parent_id,
                None,
                True
            ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO categories (name, slug, description, parent_id, image_url, is_active)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {count} categories")
        return category_ids
    
    def generate_products(self, count: int = 1000, category_ids: List[int] = None) -> List[int]:
        """Generate products and return list of product IDs."""
        product_ids = []
        data = []
        
        if category_ids is None:
            category_ids = list(range(1, 51))
        
        for i in range(count):
            product_ids.append(i + 1)
            price = Decimal(str(round(random.uniform(10.0, 2000.0), 2)))
            cost = Decimal(str(round(price * Decimal('0.6'), 2)))  # Cost is 60% of price
            dimensions = {
                "width": round(random.uniform(5.0, 50.0), 2),
                "height": round(random.uniform(5.0, 50.0), 2),
                "depth": round(random.uniform(5.0, 50.0), 2)
            }
            
            data.append((
                self.fake.product_name(),
                self.fake.text(max_nb_chars=500),
                self.fake.sku(),
                price,
                cost,
                random.choice(category_ids),
                self.fake.company(),
                Decimal(str(round(random.uniform(0.1, 50.0), 2))),  # weight
                Json(dimensions),  # Use psycopg2 Json adapter for JSON fields
                True
            ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO products (name, description, sku, price, cost, category_id, brand, weight, dimensions, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {count} products")
        return product_ids
    
    def generate_addresses(self, user_ids: List[int], count_per_user: int = 2) -> List[int]:
        """Generate addresses for users and return list of address IDs."""
        address_ids = []
        data = []
        address_id = 1
        
        for user_id in user_ids:
            for _ in range(count_per_user):
                address_ids.append(address_id)
                address_id += 1
                data.append((
                    user_id,
                    random.choice(['shipping', 'billing', 'both']),
                    self.fake.street_address(),
                    self.fake.city(),
                    self.fake.state(),
                    self.fake.zipcode(),
                    self.fake.country()[:50],  # Truncate to fit VARCHAR(50)
                    random.choice([True, False])  # is_default
                ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO addresses (user_id, type, street_address, city, state, postal_code, country, is_default)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {len(address_ids)} addresses")
        return address_ids
    
    def generate_orders(
        self,
        user_ids: List[int],
        address_ids: List[int],
        count: int = 2000
    ) -> List[int]:
        """Generate orders and return list of order IDs."""
        order_ids = []
        data = []
        
        for i in range(count):
            order_ids.append(i + 1)
            user_id = random.choice(user_ids)
            # Find addresses for this user (simplified logic)
            user_index = user_ids.index(user_id) if user_id in user_ids else 0
            start_idx = user_index * 2
            end_idx = start_idx + 2
            user_addresses = address_ids[start_idx:end_idx] if end_idx <= len(address_ids) else []
            if not user_addresses:
                user_addresses = address_ids[:10]  # Fallback
            
            shipping_address_id = random.choice(user_addresses) if user_addresses else None
            billing_address_id = random.choice(user_addresses) if user_addresses else None
            
            subtotal = Decimal(str(round(random.uniform(10.0, 1000.0), 2)))
            tax = Decimal(str(round(subtotal * Decimal('0.1'), 2)))  # 10% tax
            shipping_cost = Decimal(str(round(random.uniform(5.0, 50.0), 2)))
            total = subtotal + tax + shipping_cost
            
            data.append((
                user_id,
                self.fake.order_number(),
                random.choice(['pending', 'processing', 'shipped', 'delivered', 'cancelled']),
                subtotal,
                tax,
                shipping_cost,
                total,
                shipping_address_id,
                billing_address_id
            ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO orders (user_id, order_number, status, subtotal, tax, shipping_cost, total, shipping_address_id, billing_address_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {count} orders")
        return order_ids
    
    def generate_order_items(
        self,
        order_ids: List[int],
        product_ids: List[int],
        items_per_order: int = 3
    ) -> List[int]:
        """Generate order items and return list of order item IDs."""
        order_item_ids = []
        data = []
        item_id = 1
        
        for order_id in order_ids:
            # Get order total to distribute across items
            self.cursor.execute("SELECT total FROM orders WHERE id = %s", (order_id,))
            order_total = Decimal(str(self.cursor.fetchone()[0]))
            
            num_items = random.randint(1, items_per_order)
            item_total = order_total / Decimal(str(num_items))
            
            for _ in range(num_items):
                order_item_ids.append(item_id)
                item_id += 1
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 5)
                unit_price = item_total / Decimal(str(quantity))
                total_price = unit_price * Decimal(str(quantity))
                
                data.append((
                    order_id,
                    product_id,
                    quantity,
                    unit_price,
                    total_price
                ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
               VALUES (%s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {len(order_item_ids)} order items")
        return order_item_ids
    
    def generate_reviews(
        self,
        user_ids: List[int],
        product_ids: List[int],
        count: int = 3000
    ) -> List[int]:
        """Generate reviews and return list of review IDs."""
        review_ids = []
        data = []
        used_combinations = set()
        
        for i in range(count):
            review_ids.append(i + 1)
            user_id = random.choice(user_ids)
            product_id = random.choice(product_ids)
            
            # Ensure unique user-product combination
            while (user_id, product_id) in used_combinations:
                user_id = random.choice(user_ids)
                product_id = random.choice(product_ids)
            used_combinations.add((user_id, product_id))
            
            data.append((
                product_id,
                user_id,
                random.randint(1, 5),
                self.fake.sentence() if random.random() > 0.3 else None,
                self.fake.text(max_nb_chars=500) if random.random() > 0.2 else None,
                random.choice([True, False]),  # is_verified_purchase
                random.choice([True, False])  # is_approved
            ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO reviews (product_id, user_id, rating, title, comment, is_verified_purchase, is_approved)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {count} reviews")
        return review_ids
    
    def generate_payments(self, order_ids: List[int]) -> List[int]:
        """Generate payments for orders and return list of payment IDs."""
        payment_ids = []
        data = []
        
        payment_methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer']
        statuses = ['pending', 'processing', 'completed', 'failed', 'refunded']
        
        for i, order_id in enumerate(order_ids):
            payment_ids.append(i + 1)
            self.cursor.execute("SELECT total FROM orders WHERE id = %s", (order_id,))
            amount = Decimal(str(self.cursor.fetchone()[0]))
            
            status = random.choice(statuses)
            processed_at = self.fake.date_time() if status in ['completed', 'failed'] else None
            
            data.append((
                order_id,
                random.choice(payment_methods),
                amount,
                status,
                f"TXN-{random.randint(100000, 999999)}" if random.random() > 0.3 else None,
                processed_at
            ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO payments (order_id, payment_method, amount, status, transaction_id, processed_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {len(payment_ids)} payments")
        return payment_ids
    
    def generate_shipments(self, order_ids: List[int]) -> List[int]:
        """Generate shipments for orders and return list of shipment IDs."""
        shipment_ids = []
        data = []
        
        carriers = ['usps', 'fedex', 'ups', 'dhl']
        statuses = ['pending', 'in_transit', 'delivered', 'lost']
        
        for i, order_id in enumerate(order_ids):
            shipment_ids.append(i + 1)
            status = random.choice(statuses)
            shipped_at = self.fake.date_time() if status in ['in_transit', 'delivered'] else None
            delivered_at = self.fake.date_time() if status == 'delivered' and shipped_at else None
            
            data.append((
                order_id,
                random.choice(carriers),
                f"TRACK-{random.randint(1000000, 9999999)}" if random.random() > 0.2 else None,
                status,
                shipped_at,
                delivered_at
            ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO shipments (order_id, carrier, tracking_number, status, shipped_at, delivered_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {len(shipment_ids)} shipments")
        return shipment_ids
    
    def generate_inventory(self, product_ids: List[int]) -> List[int]:
        """Generate inventory records for products and return list of inventory IDs."""
        inventory_ids = []
        data = []
        
        for i, product_id in enumerate(product_ids):
            inventory_ids.append(i + 1)
            quantity_available = random.randint(0, 1000)
            quantity_reserved = random.randint(0, min(100, quantity_available))
            quantity_sold = random.randint(0, 500)
            
            data.append((
                product_id,
                quantity_available,
                quantity_reserved,
                quantity_sold,
                random.randint(10, 50)  # reorder_level
            ))
        
        execute_batch(
            self.cursor,
            """INSERT INTO inventory (product_id, quantity_available, quantity_reserved, quantity_sold, reorder_level)
               VALUES (%s, %s, %s, %s, %s)""",
            data,
            page_size=100
        )
        self.conn.commit()
        print(f"Generated {len(inventory_ids)} inventory records")
        return inventory_ids
    
    def generate_all(
        self,
        users: int = 1000,
        categories: int = 50,
        products: int = 1000,
        orders: int = 2000,
        reviews: int = 3000
    ):
        """Generate all test data in correct order respecting relationships."""
        self.connect()
        
        try:
            # Generate in dependency order
            user_ids = self.generate_users(users)
            category_ids = self.generate_categories(categories)
            product_ids = self.generate_products(products, category_ids)
            address_ids = self.generate_addresses(user_ids, count_per_user=2)
            order_ids = self.generate_orders(user_ids, address_ids, orders)
            self.generate_order_items(order_ids, product_ids, items_per_order=3)
            self.generate_reviews(user_ids, product_ids, reviews)
            self.generate_payments(order_ids)
            self.generate_shipments(order_ids)
            self.generate_inventory(product_ids)
            
            print("All test data generated successfully")
        finally:
            self.close()

