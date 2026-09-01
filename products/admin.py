from django.contrib import admin
from .models import Category, Product, PriceReference

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'farmer', 'category', 'price_per_unit', 'quantity_available', 'is_active']
    list_filter = ['is_active', 'is_organic', 'category', 'quality_grade']
    search_fields = ['name', 'description']

@admin.register(PriceReference)
class PriceReferenceAdmin(admin.ModelAdmin):
    list_display = ['crop_name', 'region', 'avg_price', 'unit', 'date_recorded']
    list_filter = ['region']
    search_fields = ['crop_name']
