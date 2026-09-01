from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        FARMER = 'FARMER', 'Farmer'
        BUYER = 'BUYER', 'Buyer'
        BUSINESS_BUYER = 'BUSINESS_BUYER', 'Business Buyer'
        AGRO_DEALER = 'AGRO_DEALER', 'Agro Dealer'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.BUYER)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    village_or_city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    is_verified_farmer = models.BooleanField(default=False)

    @property
    def average_rating(self):
        if self.role != self.Role.FARMER:
            return None
        reviews = self.reviews_received.all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
