from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_summary, name='dashboard-summary'),
    path('monthly-trend/', views.monthly_sales_trend, name='monthly-trend'),
    path('top-products/', views.top_selling_products, name='top-products'),
    path('dead-stock/', views.dead_stock_list, name='dead-stock'),
    path('daily-sales/', views.daily_sales_by_date, name='daily-sales'),
]
