from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from products.models import Product
from sales.models import Sale


@api_view(['GET'])
def dashboard_summary(request):
    """
    Get dashboard summary with:
    - Total Sales Today
    - Total Profit Today
    - Total Low Stock Items
    - Total Dead Stock Items
    """
    today = timezone.now().date()
    
    # Today's sales
    today_sales = Sale.objects.filter(sale_date__date=today)
    today_total_sales = today_sales.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    today_total_profit = today_sales.aggregate(
        total=Sum('profit')
    )['total'] or 0
    
    # Low stock items
    low_stock_count = Product.objects.filter(
        quantity_in_stock__lte=F('low_stock_threshold')
    ).count()
    
    # Dead stock items (not sold in last 60 days)
    sixty_days_ago = timezone.now() - timedelta(days=60)
    products_with_recent_sales = Sale.objects.filter(
        sale_date__gte=sixty_days_ago
    ).values_list('product_id', flat=True).distinct()
    
    dead_stock_products = Product.objects.exclude(
        id__in=products_with_recent_sales
    ).filter(quantity_in_stock__gt=0)  # Only products with stock
    
    dead_stock_count = dead_stock_products.count()
    dead_stock_value = sum(
        product.total_value_in_stock for product in dead_stock_products
    )
    
    return Response({
        'today_sales': float(today_total_sales),
        'today_profit': float(today_total_profit),
        'low_stock_count': low_stock_count,
        'dead_stock_count': dead_stock_count,
        'dead_stock_value': float(dead_stock_value),
    })


@api_view(['GET'])
def monthly_sales_trend(request):
    """
    Get monthly sales trend for the last 12 months.
    """
    from datetime import datetime
    from calendar import monthrange
    
    monthly_data = []
    now = timezone.now()
    
    for i in range(11, -1, -1):  # Last 12 months, newest first
        # Calculate month start and end properly
        target_month = now.month - i
        target_year = now.year
        
        # Handle year rollover
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        # Get first and last day of month
        first_day = datetime(target_year, target_month, 1, tzinfo=timezone.get_current_timezone())
        last_day_num = monthrange(target_year, target_month)[1]
        last_day = datetime(target_year, target_month, last_day_num, 23, 59, 59, tzinfo=timezone.get_current_timezone())
        
        month_sales = Sale.objects.filter(
            sale_date__gte=first_day,
            sale_date__lte=last_day
        )
        
        total_sales = month_sales.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        total_profit = month_sales.aggregate(
            total=Sum('profit')
        )['total'] or 0
        
        monthly_data.append({
            'month': first_day.strftime('%Y-%m'),
            'month_name': first_day.strftime('%B %Y'),
            'total_sales': float(total_sales),
            'total_profit': float(total_profit),
            'count': month_sales.count()
        })
    
    return Response(monthly_data)


@api_view(['GET'])
def top_selling_products(request):
    """
    Get top 5 selling products (by quantity sold).
    """
    top_products = Sale.objects.values(
        'product__id',
        'product__name',
        'product__category'
    ).annotate(
        total_quantity=Sum('quantity_sold'),
        total_revenue=Sum('total_amount'),
        total_profit=Sum('profit')
    ).order_by('-total_quantity')[:5]
    
    return Response(list(top_products))


@api_view(['GET'])
def dead_stock_list(request):
    """
    Get list of dead stock products (not sold in last 60 days).
    Includes days since last sale and money locked.
    """
    sixty_days_ago = timezone.now() - timedelta(days=60)
    
    # Get all products
    all_products = Product.objects.filter(quantity_in_stock__gt=0)
    
    dead_stock_list = []
    for product in all_products:
        # Get last sale date for this product
        last_sale = Sale.objects.filter(product=product).order_by('-sale_date').first()
        
        if not last_sale or last_sale.sale_date < sixty_days_ago:
            days_since_last_sale = (
                (timezone.now() - last_sale.sale_date).days if last_sale 
                else (timezone.now() - product.date_added).days
            )
            
            dead_stock_list.append({
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'quantity_remaining': product.quantity_in_stock,
                'days_since_last_sale': days_since_last_sale,
                'money_locked': float(product.total_value_in_stock),
                'cost_price': float(product.cost_price),
            })
    
    # Sort by days since last sale (oldest first)
    dead_stock_list.sort(key=lambda x: x['days_since_last_sale'], reverse=True)
    
    return Response(dead_stock_list)


@api_view(['GET'])
def daily_sales_by_date(request):
    """
    Return sales for a specific date and totals.
    Query params:
      - date: YYYY-MM-DD (optional, defaults to today)
    Response:
      - sales: list of sales with product name, quantity, unit price, total, profit, timestamp
      - total_sales: sum of total_amount
      - total_profit: sum of profit
    """
    from datetime import datetime

    date_str = request.query_params.get('date')
    try:
        if date_str:
            target_date = datetime.fromisoformat(date_str).date()
        else:
            target_date = timezone.now().date()
    except Exception:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    sales_qs = Sale.objects.filter(sale_date__date=target_date).order_by('-sale_date')

    sales_list = []
    for s in sales_qs:
        sales_list.append({
            'id': s.id,
            'product_id': s.product.id,
            'product_name': s.product.name,
            'quantity_sold': s.quantity_sold,
            'selling_price_at_time': float(s.selling_price_at_time),
            'total_amount': float(s.total_amount),
            'profit': float(s.profit),
            'sale_date': s.sale_date,
        })

    total_sales = sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    total_profit = sales_qs.aggregate(total=Sum('profit'))['total'] or 0

    return Response({
        'date': target_date.isoformat(),
        'sales': sales_list,
        'total_sales': float(total_sales),
        'total_profit': float(total_profit),
        'count': sales_qs.count(),
    })
