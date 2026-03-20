from django.contrib import admin
from .models import RestockTodo


@admin.register(RestockTodo)
class RestockTodoAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',
        'category',
        'quantity_needed',
        'status',
        'created_at',
        'completed_at',
    )
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('product_name', 'category', 'supplier_name')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product_name', 'category', 'quantity_needed')
        }),
        ('Cost Details', {
            'fields': ('estimated_cost_per_unit',)
        }),
        ('Supplier', {
            'fields': ('supplier_name',)
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
