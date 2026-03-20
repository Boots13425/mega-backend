from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class RestockTodo(models.Model):
    """
    RestockTodo model for tracking products that need to be restocked.
    These are planned purchases, not yet in the system.
    Status progresses: pending -> completed or pending -> postponed -> pending/completed.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('postponed', 'Postponed'),
    ]
    
    product_name = models.CharField(
        max_length=200,
        help_text="Name of product to be restocked"
    )
    category = models.CharField(
        max_length=100,
        help_text="Product category"
    )
    quantity_needed = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of units to restock"
    )
    estimated_cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('1'))],
        help_text="Estimated cost price per unit in XAF"
    )
    supplier_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Supplier name (optional)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this restock task"
    )
    
    # Status management
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the restock task"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this todo was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time this todo was updated"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this task was marked completed"
    )
    
    class Meta:
        ordering = ['-created_at']  # Newest first
        verbose_name = "Restock Todo"
        verbose_name_plural = "Restock Todos"
    
    def __str__(self):
        return f"{self.product_name} ({self.quantity_needed} units) - {self.status}"
    
    @property
    def total_estimated_cost(self):
        """Calculate total estimated cost"""
        return self.estimated_cost_per_unit * self.quantity_needed
