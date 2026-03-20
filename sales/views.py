from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from .models import Sale
from .serializers import SaleSerializer
from products.models import Product


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sale operations.
    Handles sale creation with automatic stock reduction.
    """
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    
    def get_queryset(self):
        """
        Override to support filtering by date range.
        """
        queryset = Sale.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(sale_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(sale_date__lte=end_date)
        
        # Filter by product
        product_id = self.request.query_params.get('product', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Override create to handle validation errors gracefully.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    'message': 'Sale recorded successfully!',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get all sales for today"""
        today = datetime.now().date()
        today_sales = Sale.objects.filter(sale_date__date=today)
        serializer = self.get_serializer(today_sales, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get sales statistics"""
        # Today's stats
        today = datetime.now().date()
        today_sales = Sale.objects.filter(sale_date__date=today)
        today_total = today_sales.aggregate(
            total_sales=Sum('total_amount'),
            total_profit=Sum('profit')
        ) or {'total_sales': 0, 'total_profit': 0}
        
        # Monthly stats (last 12 months)
        monthly_stats = []
        for i in range(12):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_sales = Sale.objects.filter(
                sale_date__gte=month_start,
                sale_date__lte=month_end
            )
            month_total = month_sales.aggregate(
                total=Sum('total_amount')
            ) or {'total': 0}
            monthly_stats.append({
                'month': month_start.strftime('%Y-%m'),
                'total': float(month_total['total'] or 0)
            })
        
        monthly_stats.reverse()  # Oldest to newest
        
        return Response({
            'today': {
                'total_sales': float(today_total['total_sales'] or 0),
                'total_profit': float(today_total['total_profit'] or 0),
                'count': today_sales.count()
            },
            'monthly_trend': monthly_stats
        })
