from rest_framework import serializers
from decimal import Decimal
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    is_low_stock = serializers.ReadOnlyField()
    profit_per_unit = serializers.ReadOnlyField()
    total_value_in_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'category',
            'cost_price',
            'selling_price',
            'quantity_in_stock',
            'low_stock_threshold',
            'date_added',
            'last_restocked_date',
            'supplier_name',
            'is_low_stock',
            'profit_per_unit',
            'total_value_in_stock',
        ]
        read_only_fields = ['date_added']
    
    def validate_cost_price(self, value):
        """Round cost price to whole number (CFA Franc uses no decimals)"""
        from decimal import Decimal, ROUND_HALF_UP
        if value:
            # Round to nearest whole number
            rounded = Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            if rounded < 1:
                raise serializers.ValidationError('Cost price must be at least 1 XAF.')
            return rounded
        return value
    
    def validate_selling_price(self, value):
        """Round selling price to whole number (CFA Franc uses no decimals)"""
        from decimal import Decimal, ROUND_HALF_UP
        if value:
            # Round to nearest whole number
            rounded = Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            if rounded < 1:
                raise serializers.ValidationError('Selling price must be at least 1 XAF.')
            return rounded
        return value
    
    def validate(self, data):
        """Validate that selling price is greater than cost price"""
        cost_price = data.get('cost_price', self.instance.cost_price if self.instance else None)
        selling_price = data.get('selling_price', self.instance.selling_price if self.instance else None)
        
        if cost_price and selling_price:
            if selling_price < cost_price:
                raise serializers.ValidationError({
                    'selling_price': 'Selling price should be greater than or equal to cost price.'
                })
        
        return data
