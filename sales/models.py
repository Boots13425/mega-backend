from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from products.models import Product


class Sale(models.Model):
    """
    Sale model for recording product sales.
    Stores historical selling price to preserve accuracy even if product price changes.
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='sales',
        help_text="Product that was sold"
    )
    quantity_sold = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of units sold"
    )
    
    # Store historical price at time of sale
    # CFA Franc (XAF) uses whole numbers only (no decimals)
    selling_price_at_time = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('1'))],
        help_text="Selling price per unit in XAF at the time of sale"
    )
    
    # Calculated fields
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text="Total sale amount in XAF (selling_price × quantity)"
    )
    profit = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text="Profit in XAF from this sale ((selling_price - cost_price) × quantity)"
    )
    
    # Auto timestamp
    sale_date = models.DateTimeField(auto_now_add=True, help_text="Date and time of sale")
    
    class Meta:
        ordering = ['-sale_date']  # Newest sales first
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
    
    def __str__(self):
        return f"{self.quantity_sold}x {self.product.name} - {self.sale_date.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """
        Override save to:
        1. Calculate total_amount and profit
        2. Validate stock availability
        3. Reduce stock automatically
        """
        # Validate stock availability before saving
        if self.product.quantity_in_stock < self.quantity_sold:
            raise ValueError(f"Insufficient stock. Available: {self.product.quantity_in_stock}, Requested: {self.quantity_sold}")
        
        # Calculate total amount
        self.total_amount = self.selling_price_at_time * self.quantity_sold
        
        # Calculate profit (selling_price - cost_price) × quantity
        cost_price = self.product.cost_price
        self.profit = (self.selling_price_at_time - cost_price) * self.quantity_sold
        
        # Save the sale first
        super().save(*args, **kwargs)
        
        # Reduce stock after sale is saved
        self.product.quantity_in_stock -= self.quantity_sold
        self.product.save(update_fields=['quantity_in_stock'])
