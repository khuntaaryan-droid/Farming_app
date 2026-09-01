from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from accounts.models import User
from products.models import Product, Category
from orders.models import Order, OrderItem

class RoleAccessControlTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.buyer = User.objects.create_user(username='buyer', password='password', role=User.Role.BUYER)
        self.farmer = User.objects.create_user(username='farmer', password='password', role=User.Role.FARMER)
        
        # Create product
        self.category = Category.objects.create(name='Veg', slug='veg')
        self.product = Product.objects.create(
            farmer=self.farmer,
            category=self.category,
            name='Test Tomato',
            price_per_unit='20.00',
            quantity_available='100.00'
        )

    def test_buyer_cannot_add_product(self):
        self.client.login(username='buyer', password='password')
        response = self.client.get(reverse('product_create'))
        self.assertRedirects(response, reverse('product_list'))

    def test_farmer_cannot_access_cart(self):
        self.client.login(username='farmer', password='password')
        response = self.client.get(reverse('cart_view'))
        self.assertRedirects(response, reverse('product_list'))

    def test_farmer_cannot_add_to_cart(self):
        self.client.login(username='farmer', password='password')
        response = self.client.post(reverse('add_to_cart', args=[self.product.id]), {'quantity': 1})
        self.assertRedirects(response, reverse('product_detail', args=[self.product.id]))
        # Cart should be empty in session
        self.assertNotIn('cart', self.client.session)


class FlowVerificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.farmer = User.objects.create_user(username='farmer1', password='password', role=User.Role.FARMER)
        self.biz = User.objects.create_user(username='biz1', password='password', role=User.Role.BUSINESS_BUYER, address='123 Biz St', phone='555-1234')
        self.category = Category.objects.create(name='Grains', slug='grains')
        
        # Product with bulk pricing
        self.rice = Product.objects.create(
            farmer=self.farmer,
            category=self.category,
            name='Rice',
            price_per_unit=Decimal('50.00'),
            quantity_available=Decimal('1000.00'),
            bulk_price_threshold=Decimal('100.00'),
            bulk_price_per_unit=Decimal('42.00')
        )

    def test_business_buyer_bulk_checkout_flow(self):
        # 1. Login as business buyer
        self.client.login(username='biz1', password='password')
        
        # 2. Add 100 kg to cart (hits bulk threshold)
        self.client.post(reverse('add_to_cart', args=[self.rice.id]), {'quantity': '100'})
        
        # Verify cart session
        session = self.client.session
        self.assertIn(str(self.rice.id), session['cart'])
        self.assertEqual(session['cart'][str(self.rice.id)], '100')
        
        # 3. Checkout
        checkout_data = {
            'delivery_address': '123 Biz St',
            'phone': '555-1234'
        }
        response = self.client.post(reverse('checkout'), checkout_data)
        
        # Should redirect to buyer orders
        self.assertRedirects(response, reverse('buyer_orders'))
        
        # 4. Verify DB Records & Stock Decrement
        # Stock should be 1000 - 100 = 900
        self.rice.refresh_from_db()
        self.assertEqual(self.rice.quantity_available, Decimal('900.00'))
        
        # Order and OrderItem
        order = Order.objects.get(buyer=self.biz)
        self.assertEqual(order.status, 'PENDING')
        
        item = OrderItem.objects.get(order=order)
        self.assertEqual(item.quantity, Decimal('100.00'))
        # Crucial check: the price saved should be the bulk price, not regular
        self.assertEqual(item.price_per_unit, Decimal('42.00'))
        
        # 5. Verify Farmer can update status
        self.client.logout()
        self.client.login(username='farmer1', password='password')
        
        status_update_data = {'status': 'SHIPPED'}
        response = self.client.post(reverse('update_order_status', args=[order.id]), status_update_data)
        
        order.refresh_from_db()
        self.assertEqual(order.status, 'SHIPPED')

class TrustAndRatingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.farmer = User.objects.create_user(username='farmer2', password='password', role=User.Role.FARMER)
        self.buyer = User.objects.create_user(username='buyer2', password='password', role=User.Role.BUYER)
        
        self.category = Category.objects.create(name='Veg', slug='veg')
        self.product = Product.objects.create(
            farmer=self.farmer,
            category=self.category,
            name='Test Veg',
            price_per_unit=Decimal('10.00'),
            quantity_available=Decimal('100.00')
        )
        
        # Create a delivered order
        self.order = Order.objects.create(
            buyer=self.buyer,
            delivery_address='123 Test St',
            phone='555-1234',
            status='DELIVERED'
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            farmer=self.farmer,
            quantity=Decimal('2.00'),
            price_per_unit=Decimal('10.00')
        )

    def test_post_review_and_average(self):
        self.client.login(username='buyer2', password='password')
        
        # Post a 4-star review
        response = self.client.post(reverse('post_review', args=[self.order.id]), {
            'rating': 4,
            'comment': 'Good quality!'
        })
        self.assertRedirects(response, reverse('order_detail', args=[self.order.id]))
        
        # Check average rating
        self.farmer.refresh_from_db()
        self.assertEqual(self.farmer.average_rating, 4.0)

    def test_prevent_duplicate_review(self):
        self.client.login(username='buyer2', password='password')
        
        # First review
        self.client.post(reverse('post_review', args=[self.order.id]), {'rating': 5, 'comment': 'Great!'})
        
        # Second review on same order
        response = self.client.post(reverse('post_review', args=[self.order.id]), {'rating': 1, 'comment': 'Changed my mind'})
        
        # Should catch IntegrityError in view and add error message, but still redirect
        self.assertRedirects(response, reverse('order_detail', args=[self.order.id]))
        
        # Check that only one review exists and average is still 5.0
        self.assertEqual(self.farmer.reviews_received.count(), 1)
        self.farmer.refresh_from_db()
        self.assertEqual(self.farmer.average_rating, 5.0)

    def test_open_dispute(self):
        self.client.login(username='buyer2', password='password')
        
        response = self.client.post(reverse('open_dispute', args=[self.order.id]))
        self.assertRedirects(response, reverse('order_detail', args=[self.order.id]))
        
        self.order.refresh_from_db()
        self.assertTrue(self.order.dispute_opened)
