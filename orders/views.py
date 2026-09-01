from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from decimal import Decimal
from products.models import Product
from products.utils import get_crop_recommendations
from .models import Order, OrderItem, Review
from .forms import ReviewForm
from .utils import calculate_delivery_cost
from .email_utils import send_buyer_order_confirmation, send_farmer_new_order_alert, send_order_status_update
import razorpay
from django.conf import settings
from accounts.models import Notification

def get_effective_price(product, user, quantity):
    if product.bulk_price_threshold and product.bulk_price_per_unit:
        if quantity >= product.bulk_price_threshold:
            return product.bulk_price_per_unit
    return product.price_per_unit

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        if request.user.role == 'FARMER':
            messages.error(request, 'Farmers cannot buy products using their farmer account.')
            return redirect('product_detail', pk=product_id)

        product = get_object_or_404(Product, pk=product_id, is_active=True)
        quantity = Decimal(request.POST.get('quantity', '1'))
        
        if quantity <= 0:
            messages.error(request, 'Invalid quantity.')
            return redirect('product_detail', pk=product_id)
            
        if quantity > product.quantity_available:
            messages.error(request, f'Only {product.quantity_available} {product.get_unit_display()} available.')
            return redirect('product_detail', pk=product_id)

        cart = request.session.get('cart', {})
        pid = str(product_id)
        
        current_qty = Decimal(str(cart.get(pid, '0')))
        new_qty = current_qty + quantity
        
        if new_qty > product.quantity_available:
             messages.error(request, f'Cannot add {quantity} more. You already have {current_qty} in cart and only {product.quantity_available} are available.')
        else:
            cart[pid] = str(new_qty)
            request.session['cart'] = cart
            messages.success(request, f'Added {quantity} {product.get_unit_display()} of {product.name} to cart.')
            
    return redirect('product_detail', pk=product_id)

@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        request.session['cart'] = cart
        messages.success(request, 'Item removed from cart.')
    return redirect('cart_view')

@login_required
def cart_view(request):
    if request.user.role == 'FARMER':
        messages.error(request, 'Farmers cannot access the cart.')
        return redirect('product_list')

    cart = request.session.get('cart', {})
    cart_items = []
    total_cost = Decimal('0.00')
    farmers = set()

    for pid, qty_str in cart.items():
        try:
            product = Product.objects.get(pk=pid)
            qty = Decimal(qty_str)
            effective_price = get_effective_price(product, request.user, qty)
            item_total = qty * effective_price
            total_cost += item_total
            farmers.add(product.farmer)
            cart_items.append({
                'product': product,
                'quantity': qty,
                'effective_price': effective_price,
                'total': item_total,
            })
        except Product.DoesNotExist:
            continue

    delivery_cost = calculate_delivery_cost(request.user, farmers)
    grand_total = total_cost + delivery_cost

    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'total_cost': total_cost,
        'delivery_cost': delivery_cost,
        'grand_total': grand_total
    })

@login_required
def checkout(request):
    if request.user.role == 'FARMER':
        return redirect('product_list')

    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('product_list')

    if request.method == 'POST':
        address = request.POST.get('delivery_address')
        phone = request.POST.get('phone')
        subscription_frequency = request.POST.get('subscription_frequency', 'ONE_TIME')
        payment_method = request.POST.get('payment_method', 'COD')
        promo_code = request.POST.get('promo_code', '').strip().upper()
        
        if not address or not phone:
            messages.error(request, 'Address and phone number are required.')
            return redirect('checkout')

        # Compute delivery cost before saving order
        farmers = set()
        for pid in cart.keys():
            try:
                farmers.add(Product.objects.get(pk=pid).farmer)
            except Product.DoesNotExist:
                pass
        
        delivery_cost = calculate_delivery_cost(request.user, farmers)

        with transaction.atomic():
            order = Order.objects.create(
                buyer=request.user,
                delivery_address=address,
                phone=phone,
                delivery_cost=delivery_cost,
                subscription_frequency=subscription_frequency,
                payment_method=payment_method,
                is_paid=False
            )
            
            total_cost = Decimal('0.00')
            for pid, qty_str in cart.items():
                product = Product.objects.get(pk=pid)
                qty = Decimal(qty_str)
                
                # Check stock again before finalizing
                if qty > product.quantity_available:
                    raise ValueError(f"Not enough stock for {product.name}")
                    
                # Deduct stock
                product.quantity_available -= qty
                product.save()
                
                effective_price = get_effective_price(product, request.user, qty)
                
                # Apply Imperfect discount if applicable
                if getattr(product, 'is_imperfect', False):
                    effective_price = effective_price * Decimal('0.5') # 50% off
                
                # Apply promo code discount (Group buying)
                if promo_code == 'GROUP20':
                    effective_price = effective_price * Decimal('0.8') # 20% off
                
                total_cost += effective_price * qty
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    farmer=product.farmer,
                    quantity=qty,
                    price_per_unit=effective_price
                )
            
            grand_total = total_cost + delivery_cost
            
            if payment_method == 'ONLINE':
                # Create Razorpay Order
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                payment_data = {
                    "amount": int(grand_total * 100), # amount in paise
                    "currency": "INR",
                    "receipt": f"order_rcptid_{order.id}",
                    "payment_capture": 1
                }
                razorpay_order = client.order.create(data=payment_data)
                
                # Pass details to context instead of redirecting to mock payment
                context = {
                    'order': order,
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_amount': payment_data['amount'],
                    'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                }
                # Keep cart in session until payment succeeds
                return render(request, 'orders/razorpay_checkout.html', context)

            # Clear cart and send emails for COD
            request.session['cart'] = {}
            
            # Create Notification for farmers and send emails
            try:
                for item in order.items.all():
                    Notification.objects.create(
                        user=item.farmer,
                        message=f"New COD Order from {request.user.get_full_name()} for {item.product.name}!",
                        link=f"/orders/detail/{order.id}/"
                    )
                send_buyer_order_confirmation(order)
                send_farmer_new_order_alert(order)
            except Exception as e:
                pass
                
            messages.success(request, 'Order placed successfully (Cash on Delivery)!')
            return redirect('buyer_orders')

    # Pass delivery cost to GET request as well
    farmers = set()
    for pid in cart.keys():
        try:
            farmers.add(Product.objects.get(pk=pid).farmer)
        except Product.DoesNotExist:
            pass
    delivery_cost = calculate_delivery_cost(request.user, farmers)

    return render(request, 'orders/checkout.html', {'delivery_cost': delivery_cost})

@login_required
def mock_payment(request):
    # This view is now deprecated in favor of payment_callback, 
    # but we'll leave it routing back just in case.
    return redirect('buyer_orders')
    
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        order_id_db = request.POST.get('shopping_order_id', '')
        agro_order_id = request.POST.get('agro_order_id', '')
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            
            # Payment Successful
            if agro_order_id:
                order = AgroOrder.objects.get(id=agro_order_id)
                order.is_paid = True
                order.save()
                
                try:
                    for item in order.items.all():
                        Notification.objects.create(
                            user=item.dealer,
                            message=f"New Paid Agro Order from {order.farmer.get_full_name()} for {item.agro_product.name}!",
                            link=f"/agro/dashboard/"
                        )
                except Exception:
                    pass
                    
                messages.success(request, 'Agro Payment Successful! Your order has been placed.')
                if 'agro_cart' in request.session:
                    request.session['agro_cart'] = {}
                return redirect('farmer_sales')
            
            elif order_id_db:
                order = Order.objects.get(id=order_id_db)
                order.is_paid = True
                order.save()
                
                # Create Notification for farmers and send emails
                try:
                    for item in order.items.all():
                        Notification.objects.create(
                            user=item.farmer,
                            message=f"New Paid Order from {order.buyer.get_full_name()} for {item.product.name}!",
                            link=f"/orders/detail/{order.id}/"
                        )
                    send_buyer_order_confirmation(order)
                    send_farmer_new_order_alert(order)
                except Exception:
                    pass
                    
                messages.success(request, 'Payment Successful! Your order has been placed.')
                if 'cart' in request.session:
                    request.session['cart'] = {}
                return redirect('buyer_orders')
                
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, 'Payment Signature Verification Failed!')
            
        return redirect('buyer_orders')
    return redirect('product_list')

@login_required
def invoice_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Check permissions
    if request.user != order.buyer and request.user.role != 'FARMER':
        return redirect('product_list')
        
    # If farmer, check if they have items in this order
    if request.user.role == 'FARMER' and not order.items.filter(farmer=request.user).exists():
        return redirect('farmer_sales')
        
    return render(request, 'orders/invoice.html', {'order': order})

@login_required
def buyer_orders(request):
    orders = request.user.orders.all().order_by('-created_at')
    return render(request, 'orders/buyer_orders.html', {'orders': orders})

@login_required
def farmer_sales(request):
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Sum

    if request.user.role != 'FARMER':
        return redirect('product_list')

    # Get all unique orders that contain at least one item from this farmer
    orders = Order.objects.filter(items__farmer=request.user).distinct().order_by('-created_at')
    
    # Chart logic: Sales in last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_items = OrderItem.objects.filter(farmer=request.user, order__created_at__gte=seven_days_ago)
    
    # Aggregate sales by crop name for Pie Chart
    crop_sales = {}
    for item in recent_items:
        crop_name = item.product.name
        if crop_name in crop_sales:
            crop_sales[crop_name] += float(item.total_price)
        else:
            crop_sales[crop_name] = float(item.total_price)

    # Get crop recommendations for the dashboard widget
    recommendations = get_crop_recommendations()
    
    # Get farmer's own listed products
    my_products = request.user.products.all().order_by('-created_at')
    
    # Get farmer's agro purchases
    agro_purchases = request.user.agro_orders.all().order_by('-created_at')
    
    return render(request, 'orders/farmer_sales.html', {
        'orders': orders,
        'recommendations': recommendations,
        'crop_sales_labels': list(crop_sales.keys()),
        'crop_sales_data': list(crop_sales.values()),
        'my_products': my_products,
        'agro_purchases': agro_purchases
    })

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Check permissions
    if request.user == order.buyer:
        items = order.items.all()
    elif request.user.role == 'FARMER':
        items = order.items.filter(farmer=request.user)
        if not items.exists():
            messages.error(request, 'You have no items in this order.')
            return redirect('farmer_sales')
    else:
        return redirect('product_list')

    review_form = None
    if request.user == order.buyer and order.status == 'DELIVERED':
        review_form = ReviewForm()
        # Ensure we only show form if there's no review yet
        if Review.objects.filter(buyer=request.user, order=order).exists():
            review_form = None

    return render(request, 'orders/order_detail.html', {
        'order': order, 
        'items': items,
        'review_form': review_form
    })

@login_required
def update_order_status(request, pk):
    if request.method == 'POST' and request.user.role == 'FARMER':
        order = get_object_or_404(Order, pk=pk)
        if order.items.filter(farmer=request.user).exists():
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save()
                
                # Send status update email if not pending
                if new_status != 'PENDING':
                    try:
                        send_order_status_update(order)
                    except Exception:
                        pass
                
                # Notify Buyer
                Notification.objects.create(
                    user=order.buyer,
                    message=f"Your Order #{order.id} status was updated to {new_status}.",
                    link=f"/orders/order/{order.id}/"
                )
                        
                messages.success(request, f'Order status updated to {new_status}.')
        return redirect('order_detail', pk=pk)
    return redirect('product_list')

@login_required
def open_dispute(request, pk):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk, buyer=request.user)
        order.dispute_opened = True
        order.save()
        messages.warning(request, 'A dispute has been opened for this order. An admin will review it.')
    return redirect('order_detail', pk=pk)

@login_required
def post_review(request, pk):
    order = get_object_or_404(Order, pk=pk, buyer=request.user)
    
    if request.method == 'POST' and order.status == 'DELIVERED':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.buyer = request.user
            review.order = order
            
            # For simplicity, assign review to the first farmer in the order items
            # In a more complex system, we'd review per farmer/item.
            first_item = order.items.first()
            if first_item:
                review.farmer = first_item.farmer
                try:
                    with transaction.atomic():
                        review.save()
                    messages.success(request, 'Review submitted successfully!')
                except IntegrityError:
                    messages.error(request, 'You have already reviewed this order.')
    return redirect('order_detail', pk=pk)

@login_required
def request_transport(request, pk):
    if request.method == 'POST' and request.user.role == 'FARMER':
        order = get_object_or_404(Order, pk=pk)
        if order.items.filter(farmer=request.user).exists():
            order.transport_requested = True
            order.save()
            messages.success(request, 'Your transport request has been sent to local drivers! A truck/tempo will be assigned soon.')
    return redirect('order_detail', pk=pk)

@login_required
def make_offer(request, product_id):
    from .models import Negotiation
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    
    if request.user.role == 'FARMER':
        messages.error(request, 'Farmers cannot make offers.')
        return redirect('product_detail', pk=product_id)
        
    if request.method == 'POST':
        offered_price = request.POST.get('offered_price')
        quantity = request.POST.get('quantity')
        
        if not offered_price or not quantity:
            messages.error(request, 'Price and quantity are required.')
            return redirect('make_offer', product_id=product_id)
            
        try:
            offered_price = Decimal(offered_price)
            quantity = Decimal(quantity)
        except:
            messages.error(request, 'Invalid input.')
            return redirect('make_offer', product_id=product_id)
            
        if quantity > product.quantity_available:
            messages.error(request, f'Only {product.quantity_available} available.')
            return redirect('make_offer', product_id=product_id)
            
        Negotiation.objects.create(
            buyer=request.user,
            farmer=product.farmer,
            product=product,
            quantity=quantity,
            offered_price_per_unit=offered_price
        )
        messages.success(request, 'Your offer has been sent to the farmer!')
        return redirect('product_detail', pk=product_id)
        
    return render(request, 'orders/make_offer.html', {'product': product})

@login_required
def manage_offers(request):
    from .models import Negotiation
    if request.user.role == 'FARMER':
        offers = Negotiation.objects.filter(farmer=request.user).order_by('-created_at')
        return render(request, 'orders/manage_offers.html', {'offers': offers, 'is_farmer': True})
    else:
        offers = Negotiation.objects.filter(buyer=request.user).order_by('-created_at')
        return render(request, 'orders/manage_offers.html', {'offers': offers, 'is_farmer': False})

@login_required
def accept_offer(request, offer_id):
    from .models import Negotiation
    offer = get_object_or_404(Negotiation, pk=offer_id, farmer=request.user, status='PENDING')
    
    if request.method == 'POST':
        offer.status = 'ACCEPTED'
        offer.save()
        
        Notification.objects.create(
            user=offer.buyer,
            message=f"Your offer for {offer.product.name} was ACCEPTED by {request.user.username}!",
            link="/orders/offers/"
        )
        
        messages.success(request, f'You accepted the offer from {offer.buyer.username}.')
        
    return redirect('manage_offers')

@login_required
def reject_offer(request, offer_id):
    from .models import Negotiation
    offer = get_object_or_404(Negotiation, pk=offer_id, farmer=request.user, status='PENDING')
    
    if request.method == 'POST':
        offer.status = 'REJECTED'
        offer.save()
        
        Notification.objects.create(
            user=offer.buyer,
            message=f"Your offer for {offer.product.name} was REJECTED by {request.user.username}.",
            link="/orders/offers/"
        )
        
        messages.success(request, 'Offer rejected.')
        
    return redirect('manage_offers')

@login_required
def build_basket(request):
    if request.user.role == 'FARMER':
        messages.error(request, 'Farmers cannot build baskets.')
        return redirect('product_list')
        
    products = Product.objects.filter(is_active=True).order_by('-quantity_available')[:20]
    
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        added_any = False
        for product in products:
            qty_str = request.POST.get(f'qty_{product.id}')
            if qty_str and float(qty_str) > 0:
                qty = Decimal(qty_str)
                if qty <= product.quantity_available:
                    pid = str(product.id)
                    current_qty = Decimal(str(cart.get(pid, '0')))
                    cart[pid] = str(current_qty + qty)
                    added_any = True
                
        if added_any:
            request.session['cart'] = cart
            messages.success(request, 'Custom Basket built! We recommend selecting "Weekly Subscription" below.')
            return redirect('checkout')
        else:
            messages.warning(request, 'You must add at least one item to build a basket.')
            
    return render(request, 'orders/build_basket.html', {'products': products})


# ==========================================
# AGRO STORE ORDERS
# ==========================================
from products.models import AgroProduct
from .models import AgroOrder, AgroOrderItem

@login_required
def add_to_agro_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(AgroProduct, pk=product_id, is_active=True)
        quantity = int(request.POST.get('quantity', '1'))
        
        if quantity <= 0:
            messages.error(request, 'Invalid quantity.')
            return redirect('agro_product_detail', pk=product_id)
            
        cart = request.session.get('agro_cart', {})
        pid = str(product_id)
        
        current_qty = int(cart.get(pid, '0'))
        new_qty = current_qty + quantity
        
        cart[pid] = str(new_qty)
        request.session['agro_cart'] = cart
        messages.success(request, f'Added {quantity} of {product.name} to cart.')
            
    return redirect('agro_product_detail', pk=product_id)

@login_required
def agro_cart_view(request):
    cart = request.session.get('agro_cart', {})
    cart_items = []
    total_cost = Decimal('0.00')
    
    for pid, qty_str in cart.items():
        try:
            product = AgroProduct.objects.get(pk=pid)
            qty = int(qty_str)
            item_total = product.price * Decimal(qty)
            total_cost += item_total
            
            cart_items.append({
                'product': product,
                'quantity': qty,
                'total': item_total
            })
        except AgroProduct.DoesNotExist:
            continue
            
    return render(request, 'orders/agro_cart.html', {
        'cart_items': cart_items,
        'total_cost': total_cost
    })

@login_required
def remove_from_agro_cart(request, product_id):
    cart = request.session.get('agro_cart', {})
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        request.session['agro_cart'] = cart
        messages.success(request, 'Item removed from cart.')
    return redirect('agro_cart_view')

@login_required
@transaction.atomic
def agro_checkout(request):
    cart = request.session.get('agro_cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('agro_store')
        
    total_cost = Decimal('0.00')
    cart_items = []
    
    for pid, qty_str in cart.items():
        try:
            product = AgroProduct.objects.get(pk=pid)
            qty = int(qty_str)
            item_total = product.price * Decimal(qty)
            total_cost += item_total
            cart_items.append({'product': product, 'quantity': qty})
        except AgroProduct.DoesNotExist:
            pass
            
    if request.method == 'POST':
        delivery_address = request.POST.get('delivery_address', '')
        phone = request.POST.get('phone', '')
        payment_method = request.POST.get('payment_method', 'COD')
        
        if not delivery_address or not phone:
            messages.error(request, 'Please provide delivery address and phone number.')
            return redirect('agro_checkout')
            
        order = AgroOrder.objects.create(
            farmer=request.user,
            phone=phone,
            delivery_address=delivery_address,
            payment_method=payment_method
        )
        
        for item in cart_items:
            AgroOrderItem.objects.create(
                order=order,
                agro_product=item['product'],
                dealer=item['product'].dealer,
                quantity=item['quantity'],
                price_per_unit=item['product'].price
            )
            
        if payment_method == 'ONLINE':
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            payment_data = {
                "amount": int(total_cost * 100),
                "currency": "INR",
                "receipt": f"agro_rcptid_{order.id}",
                "payment_capture": 1
            }
            razorpay_order = client.order.create(data=payment_data)
            
            context = {
                'order': order,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_amount': payment_data['amount'],
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            }
            return render(request, 'orders/agro_razorpay_checkout.html', context)
            
        # Create notification for dealers on COD order
        try:
            for item in order.items.all():
                Notification.objects.create(
                    user=item.dealer,
                    message=f"New COD Agro Order from {order.farmer.get_full_name()} for {item.agro_product.name}!",
                    link=f"/agro/dashboard/"
                )
        except Exception:
            pass

        request.session['agro_cart'] = {}
        messages.success(request, 'Order placed successfully (Cash on Delivery)!')
        return redirect('farmer_sales')
        
    return render(request, 'orders/agro_checkout.html', {'total_cost': total_cost})

@login_required
def agro_order_detail(request, pk):
    order = get_object_or_404(AgroOrder, pk=pk)
    
    # Check permissions (only farmer who bought or dealer who sold can view)
    is_buyer = request.user == order.farmer
    is_dealer = AgroOrderItem.objects.filter(order=order, dealer=request.user).exists()
    
    if not (is_buyer or is_dealer):
        messages.error(request, 'Access denied.')
        return redirect('product_list')
        
    return render(request, 'orders/agro_order_detail.html', {'order': order, 'is_dealer': is_dealer})

@login_required
def update_agro_order_status(request, pk):
    order = get_object_or_404(AgroOrder, pk=pk)
    
    is_dealer = AgroOrderItem.objects.filter(order=order, dealer=request.user).exists()
    
    if request.method == 'POST' and is_dealer:
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            
            Notification.objects.create(
                user=order.farmer,
                message=f"Your Agro Order #{order.id} status was updated to {new_status}.",
                link=f"/orders/agro-order/{order.id}/"
            )
                    
            messages.success(request, f'Order status updated to {new_status}.')
            
    return redirect('agro_order_detail', pk=pk)
