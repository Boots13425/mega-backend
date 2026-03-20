from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .models import Product
import pandas as pd
from io import BytesIO
import openpyxl


class ExcelImportTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.token = Token.objects.create(user=self.user)
        
    def create_test_excel(self, data):
        """Create a test Excel file with the given data"""
        df = pd.DataFrame(data)
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        return SimpleUploadedFile(
            "test_products.xlsx",
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    def test_excel_import_success(self):
        """Test successful Excel import"""
        # Create test data
        test_data = {
            'product': ['Lipstick Red', 'Mascara Black'],
            'category': ['Lipstick', 'Mascara'],
            'cost_price': [1500, 2000],
            'selling_price': [2000, 2500],
            'stock': [50, 30],
            'low_stock_threshold': [10, 5],
            'supplier_name': ['Supplier A', 'Supplier B']
        }
        
        excel_file = self.create_test_excel(test_data)
        
        response = self.client.post(
            '/api/products/import-excel/',
            {'file': excel_file},
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['imported'], 2)
        self.assertEqual(result['skipped'], 0)
        self.assertEqual(len(result['errors']), 0)
        
        # Check products were created
        self.assertEqual(Product.objects.count(), 2)
        
    def test_excel_import_missing_required_columns(self):
        """Test Excel import with missing required columns"""
        # Create test data with missing required columns
        test_data = {
            'product': ['Lipstick Red'],
            'category': ['Lipstick'],
            # Missing cost_price and stock
        }
        
        excel_file = self.create_test_excel(test_data)
        
        response = self.client.post(
            '/api/products/import-excel/',
            {'file': excel_file},
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertIn('Missing required columns', result['error'])
        
    def test_excel_import_invalid_file(self):
        """Test Excel import with invalid file"""
        # Create a text file instead of Excel
        text_file = SimpleUploadedFile(
            "test.txt",
            b"This is not an Excel file",
            content_type="text/plain"
        )
        
        response = self.client.post(
            '/api/products/import-excel/',
            {'file': text_file},
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertIn('Only .xlsx and .xls files are allowed', result['error'])