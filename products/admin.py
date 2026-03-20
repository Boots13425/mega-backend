from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'quantity_in_stock', 'low_stock_threshold', 'selling_price', 'is_low_stock', 'date_added']
    list_filter = ['category', 'date_added']
    search_fields = ['name', 'category', 'supplier_name']
    readonly_fields = ['date_added', 'is_low_stock', 'profit_per_unit', 'total_value_in_stock']
