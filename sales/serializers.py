from rest_framework import serializers
from decimal import Decimal
from .models import Sale
from products.serializers import ProductSerializer


class SaleSerializer(serializers.ModelSerializer):
    """Serializer for Sale model"""
    product_detail = ProductSerializer(source='product', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id',
            'product',
            'product_detail',
            'product_name',
            'quantity_sold',
            'selling_price_at_time',
            'total_amount',
            'profit',
            'sale_date',
        ]
        read_only_fields = ['total_amount', 'profit', 'sale_date']
    
    def validate_selling_price_at_time(self, value):
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
        """Validate sale before creation"""
        product = data.get('product')
        quantity_sold = data.get('quantity_sold')
        selling_price_at_time = data.get('selling_price_at_time')
        
        # In DRF, ForeignKey fields are resolved to instances in validate()
        # But handle both cases for safety
        if product:
            # If product is an ID (int), fetch the Product instance
            if isinstance(product, int):
                from products.models import Product
                try:
                    product = Product.objects.get(pk=product)
                    data['product'] = product  # Update data with instance
                except Product.DoesNotExist:
                    raise serializers.ValidationError({
                        'product': 'Product not found.'
                    })
            
            # Now product should be a Product instance
            if hasattr(product, 'quantity_in_stock') and quantity_sold:
                # Check stock availability
                if product.quantity_in_stock < quantity_sold:
                    raise serializers.ValidationError({
                        'quantity_sold': f'Insufficient stock. Available: {product.quantity_in_stock}, Requested: {quantity_sold}'
                    })
                
                # If selling_price_at_time not provided, use current product price
                if not selling_price_at_time:
                    data['selling_price_at_time'] = product.selling_price
        
        return data
