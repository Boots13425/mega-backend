"""
Service layer for product-related business logic.
Includes low stock alert functionality (prepared for WhatsApp integration).
"""


def send_low_stock_alert(product):
    """
    Send low stock alert for a product.
    
    This is a placeholder function prepared for WhatsApp integration.
    Currently logs the alert. Can be extended to send WhatsApp messages.
    
    Args:
        product: Product instance that is low on stock
    
    Returns:
        dict: Status of alert sending
    """
    # TODO: Implement WhatsApp API integration here
    # Example structure for future implementation:
    # 
    # from twilio.rest import Client
    # 
    # message = (
    #     f"⚠️ LOW STOCK ALERT\n\n"
    #     f"Product: {product.name}\n"
    #     f"Category: {product.category}\n"
    #     f"Current Stock: {product.quantity_in_stock}\n"
    #     f"Threshold: {product.low_stock_threshold}\n"
    #     f"Please restock soon!"
    # )
    # 
    # client = Client(account_sid, auth_token)
    # client.messages.create(
    #     body=message,
    #     from_='whatsapp:+14155238886',
    #     to='whatsapp:+1234567890'
    # )
    
    # For now, just return a status dict
    return {
        'status': 'logged',
        'product_id': product.id,
        'product_name': product.name,
        'current_stock': product.quantity_in_stock,
        'threshold': product.low_stock_threshold,
        'message': f'Low stock alert logged for {product.name}',
    }


def check_and_alert_low_stock(product):
    """
    Check if product is low on stock and send alert if needed.
    
    Args:
        product: Product instance to check
    
    Returns:
        dict or None: Alert status if low stock, None otherwise
    """
    if product.is_low_stock:
        return send_low_stock_alert(product)
    return None
