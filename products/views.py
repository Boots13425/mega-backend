from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models import Q, F
from django.http import HttpResponse
from .models import Product
from .serializers import ProductSerializer
from .services import check_and_alert_low_stock
from .excel_import import process_excel_upload

from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponse
from pathlib import Path
import os

class ReactAppView(TemplateView):
    """Serve the React app's index.html for all non-API routes"""
    template_name = "index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

def index(request):
    # Try to serve the built React app
    react_index = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist" / "index.html"
    if react_index.exists():
        with open(react_index, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    else:
        # Fallback if build doesn't exist yet
        return render(request, "index.html")


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations.
    Supports search and filtering.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        """
        Override to support search and filtering.
        """
        queryset = Product.objects.all()
        
        # Search by name or category
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(category__icontains=search)
            )
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__iexact=category)
        
        # Filter low stock items
        low_stock = self.request.query_params.get('low_stock', None)
        if low_stock == 'true':
            queryset = queryset.filter(quantity_in_stock__lte=F('low_stock_threshold'))
        
        return queryset
    
    def perform_create(self, serializer):
        """Override to check for low stock after creation"""
        product = serializer.save()
        # Check and alert if low stock
        check_and_alert_low_stock(product)
    
    def perform_update(self, serializer):
        """Override to check for low stock after update"""
        product = serializer.save()
        # Check and alert if low stock
        check_and_alert_low_stock(product)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of all unique categories"""
        categories = Product.objects.values_list('category', flat=True).distinct()
        return Response(list(categories))
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock products"""
        low_stock_products = Product.objects.filter(
            quantity_in_stock__lte=F('low_stock_threshold')
        )
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='import-excel', permission_classes=[IsAdminUser])
    def import_excel(self, request):
        """
        Accept an Excel file (field: file), validate, map columns, and import products.
        Returns imported count, skipped count, and list of row errors.
        """
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided. Use form field name: file'}, status=status.HTTP_400_BAD_REQUEST)
        upload = request.FILES['file']
        name = (upload.name or '').lower()
        if not (name.endswith('.xlsx') or name.endswith('.xls')):
            return Response({'error': 'Only .xlsx and .xls files are allowed'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = process_excel_upload(upload)
        except Exception as e:
            return Response({'error': f'Server error while processing file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if result['errors'] and len(result['errors']) == 1 and 'Missing required columns' in result['errors'][0].get('error', ''):
            return Response({'error': 'Missing required columns'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)

    @action(detail=False, methods=['get'], url_path='excel-template', permission_classes=[IsAdminUser])
    def excel_template(self, request):
        """Return a downloadable Excel template with expected column headers."""
        try:
            import openpyxl
            from io import BytesIO
        except ImportError:
            return Response({'error': 'Excel support not available'}, status=status.HTTP_501_NOT_IMPLEMENTED)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Products'
        # Match the actual Product fields used by this system.
        # description is accepted by the importer but ignored (there is no description field on Product).
        headers = [
            'product',
            'category',
            'cost_price',
            'selling_price',
            'stock',
            'low_stock_threshold',
            'supplier_name',
            'description',
        ]
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="products_import_template.xlsx"'
        return response
