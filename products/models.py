from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Product(models.Model):
    """
    Product model for cosmetic shop inventory.
    Stores all product information including pricing and stock levels.
    """
    name = models.CharField(max_length=200, help_text="Product name (e.g., 'Rose Lipstick - Shade 12')")
    category = models.CharField(max_length=100, help_text="Product category (e.g., 'Lipstick', 'Foundation', 'Mascara')")
    
    # Pricing fields - using Decimal for precise money calculations
    # CFA Franc (XAF) uses whole numbers only (no decimals)
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=0,
        validators=[MinValueValidator(Decimal('1'))],
        help_text="Cost price per unit in XAF (what you paid to buy this product)"
    )
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=0,
        validators=[MinValueValidator(Decimal('1'))],
        help_text="Selling price per unit in XAF (what customers pay)"
    )
    
    # Stock management
    quantity_in_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current number of units in stock"
    )
    low_stock_threshold = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Alert when stock falls to this number or below"
    )
    
    # Dates
    date_added = models.DateTimeField(auto_now_add=True, help_text="When this product was first added")
    last_restocked_date = models.DateField(null=True, blank=True, help_text="Last time stock was replenished")
    
    # Optional supplier information
    supplier_name = models.CharField(max_length=200, blank=True, null=True, help_text="Name of supplier (optional)")
    
    class Meta:
        ordering = ['-date_added']  # Newest first
        verbose_name = "Product"
        verbose_name_plural = "Products"
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return self.quantity_in_stock <= self.low_stock_threshold
    
    @property
    def profit_per_unit(self):
        """Calculate profit per unit"""
        return self.selling_price - self.cost_price
    
    @property
    def total_value_in_stock(self):
        """Calculate total value of stock (cost price × quantity)"""
        return self.cost_price * self.quantity_in_stock
