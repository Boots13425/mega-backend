from django.contrib import admin
from .models import Sale


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_sold', 'total_amount', 'profit', 'sale_date']
    list_filter = ['sale_date', 'product__category']
    search_fields = ['product__name']
    readonly_fields = ['sale_date', 'total_amount', 'profit']
    date_hierarchy = 'sale_date'
