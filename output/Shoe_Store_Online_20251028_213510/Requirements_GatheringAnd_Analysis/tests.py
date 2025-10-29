# Generated on: 2025-10-28 21:35:29

from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Customer, Product, Order, OrderItem, Inventory

class TestModels(TestCase):
    def test_customer_creation(self):
        customer = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.assertEqual(customer.username, 'testuser')
        self.assertEqual(customer.email, 'test@example.com')

    def test_product_creation(self):
        product = Product.objects.create(name='Test Product', price=10.99, brand='Test Brand', category='Test Category')
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.price, 10.99)
        self.assertEqual(product.brand, 'Test Brand')
        self.assertEqual(product.category, 'Test Category')

    def test_order_creation(self):
        customer = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        order = Order.objects.create(customer=customer, order_date='2022-01-01', total=10.99)
        self.assertEqual(order.customer, customer)
        self.assertEqual(order.order_date, '2022-01-01')
        self.assertEqual(order.total, 10.99)

    def test_order_item_creation(self):
        customer = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        order = Order.objects.create(customer=customer, order_date='2022-01-01', total=10.99)
        product = Product.objects.create(name='Test Product', price=10.99, brand='Test Brand', category='Test Category')
        order_item = OrderItem.objects.create(order=order, product=product, quantity=2)
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.product, product)
        self.assertEqual(order_item.quantity, 2)