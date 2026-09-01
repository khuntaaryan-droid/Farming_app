from django.urls import path
from . import views

urlpatterns = [
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/<int:pk>/update/', views.update_order_status, name='update_order_status'),
    path('order/<int:pk>/dispute/', views.open_dispute, name='open_dispute'),
    path('order/<int:pk>/review/', views.post_review, name='post_review'),
    path('order/<int:pk>/request-transport/', views.request_transport, name='request_transport'),
    path('buyer/orders/', views.buyer_orders, name='buyer_orders'),
    path('farmer/sales/', views.farmer_sales, name='farmer_sales'),
    path('mock-payment/', views.mock_payment, name='mock_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('order/<int:pk>/invoice/', views.invoice_view, name='invoice'),
    
    # Negotiation URLs
    path('product/<int:product_id>/make-offer/', views.make_offer, name='make_offer'),
    path('offers/', views.manage_offers, name='manage_offers'),
    path('offers/<int:offer_id>/accept/', views.accept_offer, name='accept_offer'),
    path('offers/<int:offer_id>/reject/', views.reject_offer, name='reject_offer'),
    
    path('build-basket/', views.build_basket, name='build_basket'),
    
    # Agro Store Orders URLs
    path('agro-cart/add/<int:product_id>/', views.add_to_agro_cart, name='add_to_agro_cart'),
    path('agro-cart/remove/<int:product_id>/', views.remove_from_agro_cart, name='remove_from_agro_cart'),
    path('agro-cart/', views.agro_cart_view, name='agro_cart_view'),
    path('agro-checkout/', views.agro_checkout, name='agro_checkout'),
    path('agro-order/<int:pk>/', views.agro_order_detail, name='agro_order_detail'),
    path('agro-order/<int:pk>/update/', views.update_agro_order_status, name='update_agro_order_status'),
]
