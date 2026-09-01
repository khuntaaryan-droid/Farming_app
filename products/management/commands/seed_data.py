import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from accounts.models import User
from products.models import Category, Product, PriceReference

class Command(BaseCommand):
    help = 'Seeds the database with initial data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 1. Create Users
        farmer, _ = User.objects.get_or_create(
            username='farmer1', 
            defaults={'email': 'farmer@example.com', 'role': 'FARMER', 'is_verified_farmer': True, 'village_or_city': 'Nashik', 'state': 'Maharashtra'}
        )
        farmer.set_password('password123')
        farmer.save()

        buyer, _ = User.objects.get_or_create(
            username='buyer1',
            defaults={'email': 'buyer@example.com', 'role': 'BUYER', 'village_or_city': 'Mumbai', 'state': 'Maharashtra'}
        )
        buyer.set_password('password123')
        buyer.save()

        biz_buyer, _ = User.objects.get_or_create(
            username='biz1',
            defaults={'email': 'biz@example.com', 'role': 'BUSINESS_BUYER', 'village_or_city': 'Pune', 'state': 'Maharashtra'}
        )
        biz_buyer.set_password('password123')
        biz_buyer.save()

        # 2. Create Categories
        cat_veg, _ = Category.objects.get_or_create(name='Vegetables', slug='vegetables')
        cat_grains, _ = Category.objects.get_or_create(name='Grains', slug='grains')
        cat_fruits, _ = Category.objects.get_or_create(name='Fruits', slug='fruits')

        # 3. Create Price References
        crops = [
            ('Tomato', 'Maharashtra', 25.00),
            ('Tomato', 'Gujarat', 22.00),
            ('Rice', 'Maharashtra', 45.00),
            ('Rice', 'Gujarat', 40.00),
            ('Wheat', 'Maharashtra', 35.00),
            ('Wheat', 'Gujarat', 32.00),
            ('Onion', 'Maharashtra', 18.00),
            ('Onion', 'Gujarat', 15.00),
            ('Potato', 'Maharashtra', 20.00),
            ('Potato', 'Gujarat', 19.00),
        ]
        
        for crop, region, price in crops:
            PriceReference.objects.update_or_create(
                crop_name=crop,
                region=region,
                defaults={'avg_price': Decimal(str(price)), 'unit': 'kg'}
            )

        # 4. Create Products
        Product.objects.get_or_create(
            farmer=farmer,
            category=cat_veg,
            name='Fresh Red Tomatoes',
            defaults={
                'description': 'Farm fresh organic tomatoes.',
                'price_per_unit': Decimal('22.00'),
                'unit': 'kg',
                'quantity_available': Decimal('500.00'),
                'is_organic': True,
                'quality_grade': 'A',
                'bulk_price_threshold': Decimal('50.00'),
                'bulk_price_per_unit': Decimal('18.00'),
            }
        )

        Product.objects.get_or_create(
            farmer=farmer,
            category=cat_grains,
            name='Basmati Rice',
            defaults={
                'description': 'Premium quality basmati rice from the fields of Maharashtra.',
                'price_per_unit': Decimal('50.00'),
                'unit': 'kg',
                'quantity_available': Decimal('1000.00'),
                'is_organic': False,
                'quality_grade': 'A',
                'bulk_price_threshold': Decimal('100.00'),
                'bulk_price_per_unit': Decimal('42.00'),
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database.'))
