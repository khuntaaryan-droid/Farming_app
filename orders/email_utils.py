from django.core.mail import send_mail
from django.conf import settings

def send_buyer_order_confirmation(order):
    subject = f'Order Confirmation #{order.id} - Agri Shop'
    message = f'''Hello {order.buyer.get_full_name() or order.buyer.username},

Thank you for your order!

Order ID: #{order.id}
Status: {order.get_status_display()}
Grand Total: ₹{order.total_amount} (including delivery)

Items Ordered:
'''
    for item in order.items.all():
        message += f"- {item.product.name} (Qty: {item.quantity}) - ₹{item.total_price}\n"
        
    message += '\nWe will notify you when your order status updates.\n\nThank you,\nThe Agri Shop Team'
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.buyer.email],
        fail_silently=False,
    )

def send_farmer_new_order_alert(order):
    # Group items by farmer so we can send individual emails to each farmer involved
    farmers_dict = {}
    for item in order.items.all():
        if item.farmer not in farmers_dict:
            farmers_dict[item.farmer] = []
        farmers_dict[item.farmer].append(item)
        
    for farmer, items in farmers_dict.items():
        subject = f'New Order Alert! #{order.id} - Agri Shop'
        message = f'''Hello {farmer.get_full_name() or farmer.username},

You have received a new order!

Order ID: #{order.id}
Buyer: {order.buyer.get_full_name() or order.buyer.username}
Phone: {order.phone}
Delivery Address: {order.delivery_address}

Items to Fulfill:
'''
        for item in items:
            message += f"- {item.product.name} (Qty: {item.quantity})\n"
            
        message += '\nPlease check your My Sales dashboard to update the order status.\n\nThank you,\nThe Agri Shop Team'
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [farmer.email],
            fail_silently=False,
        )

def send_order_status_update(order):
    subject = f'Order Status Update #{order.id} - Agri Shop'
    message = f'''Hello {order.buyer.get_full_name() or order.buyer.username},

Your order #{order.id} status has been updated.

New Status: {order.get_status_display()}

Thank you,
The Agri Shop Team
'''
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.buyer.email],
        fail_silently=False,
    )
