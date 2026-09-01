from django.db import models
from django.conf import settings
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    SUBSCRIPTION_CHOICES = [
        ('ONE_TIME', 'One-time Purchase'),
        ('WEEKLY', 'Weekly Subscription'),
        ('MONTHLY', 'Monthly Subscription'),
    ]

    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
    ]

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    delivery_address = models.TextField()
    phone = models.CharField(max_length=15)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subscription_frequency = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, default='ONE_TIME')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='COD')
    is_paid = models.BooleanField(default=False)
    dispute_opened = models.BooleanField(default=False)
    transport_requested = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_amount(self):
        items_total = sum(item.total_price for item in self.items.all())
        return items_total + self.delivery_cost

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price_per_unit

    def __str__(self):
        product_name = self.product.name if self.product else "Deleted Product"
        return f"{self.quantity} of {product_name} in Order #{self.order.id}"

class Review(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('buyer', 'order')

    def __str__(self):
        return f"Review by {self.buyer.username} for {self.farmer.username} (Order #{self.order.id})"

class Negotiation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COUNTER', 'Counter Offer'),
    ]
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='negotiations_made')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='negotiations_received')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='negotiations')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    offered_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Offer by {self.buyer.username} for {self.product.name} at ₹{self.offered_price_per_unit}"

class AgroOrder(models.Model):
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agro_orders')
    phone = models.CharField(max_length=15)
    delivery_address = models.TextField()
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=Order.PAYMENT_CHOICES, default='COD')
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return f"Agro Order #{self.id} by {self.farmer.username}"

class AgroOrderItem(models.Model):
    order = models.ForeignKey(AgroOrder, on_delete=models.CASCADE, related_name='items')
    agro_product = models.ForeignKey('products.AgroProduct', on_delete=models.SET_NULL, null=True)
    dealer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agro_sales')
    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price_per_unit

    def __str__(self):
        product_name = self.agro_product.name if self.agro_product else "Deleted Product"
        return f"{self.quantity} of {product_name} in Agro Order #{self.order.id}"
