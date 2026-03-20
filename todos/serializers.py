from rest_framework import serializers
from .models import RestockTodo


class RestockTodoSerializer(serializers.ModelSerializer):
    total_estimated_cost = serializers.ReadOnlyField()
    
    class Meta:
        model = RestockTodo
        fields = [
            'id',
            'product_name',
            'category',
            'quantity_needed',
            'estimated_cost_per_unit',
            'supplier_name',
            'notes',
            'status',
            'created_at',
            'updated_at',
            'completed_at',
            'total_estimated_cost',
        ]
