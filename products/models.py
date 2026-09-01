from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('quintal', 'Quintal (100kg)'),
        ('dozen', 'Dozen'),
        ('litre', 'Litre'),
        ('piece', 'Piece'),
    ]

    QUALITY_CHOICES = [
        ('A', 'Grade A (Premium)'),
        ('B', 'Grade B (Standard)'),
        ('C', 'Grade C (Processing/Juice)'),
        ('organic', 'Certified Organic'),
        ('pesticide_free', 'Pesticide-Free'),
    ]

    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Bulk Pricing for Business Buyers
    bulk_price_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Minimum quantity for bulk pricing")
    bulk_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price per unit when threshold is met")
    
    is_organic = models.BooleanField(default=False)
    quality_grade = models.CharField(max_length=20, choices=QUALITY_CHOICES, blank=True)
    is_imperfect = models.BooleanField(default=False, help_text="Ugly veggies at discount")
    harvest_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PriceReference(models.Model):
    crop_name = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='kg')
    date_recorded = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.crop_name} in {self.region} - ₹{self.avg_price}/{self.unit}"

class CropDiseaseQuery(models.Model):
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disease_queries')
    crop_name = models.CharField(max_length=100)
    symptoms = models.TextField()
    image = models.ImageField(upload_to='disease_images/')
    ai_diagnosis = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Query: {self.crop_name} by {self.farmer.username}"

class ForumPost(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ForumComment(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

class GovernmentScheme(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    link = models.URLField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    required_documents = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class AgriMachinery(models.Model):
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='machinery')
    name = models.CharField(max_length=150)
    description = models.TextField()
    image = models.ImageField(upload_to='machinery_images/', blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.farmer.username}"

class FarmVisit(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_visits')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booked_visits')
    scheduled_date = models.DateField()
    guest_count = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visit to {self.farmer.username} by {self.buyer.username}"

class AgroProduct(models.Model):
    CATEGORY_CHOICES = [
        ('FERTILIZER', 'Fertilizer'),
        ('PESTICIDE', 'Pesticide / Medicine'),
        ('SEEDS', 'Seeds'),
        ('EQUIPMENT', 'Small Equipment'),
    ]
    dealer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agro_products')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='FERTILIZER')
    description = models.TextField()
    usage_guidance = models.TextField(help_text="How to use this product safely", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='agro_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
