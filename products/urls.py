from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/add/', views.product_create, name='product_create'),
    path('product/<int:pk>/edit/', views.product_update, name='product_update'),
    path('crop-doctor/', views.crop_doctor, name='crop_doctor'),
    
    # Forum URLs
    path('forum/', views.forum_list, name='forum_list'),
    path('forum/new/', views.forum_create, name='forum_create'),
    path('forum/<int:pk>/', views.forum_detail, name='forum_detail'),
    
    # Phase 7 URLs
    path('schemes/', views.schemes_list, name='schemes_list'),
    path('machinery/', views.machinery_list, name='machinery_list'),
    path('machinery/add/', views.machinery_create, name='machinery_create'),
    path('farmer/<str:farmer_username>/book-visit/', views.book_farm_visit, name='book_farm_visit'),
    
    # Static Pages
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
    path('faq/', views.faq, name='faq'),
    path('terms/', views.terms, name='terms'),
    path('return-policy/', views.return_policy, name='return_policy'),
    
    # Phase 9 Advanced Features
    path('map/', views.farm_map, name='farm_map'),
    path('live/', views.live_streams, name='live_streams'),
    path('live/start/', views.start_live, name='start_live'),
    path('api/chatbot/', views.ai_chatbot, name='ai_chatbot'),
    
    # Phase 10 Agro Store
    path('agro/', views.agro_store, name='agro_store'),
    path('agro/product/<int:pk>/', views.agro_product_detail, name='agro_product_detail'),
    
    # Phase 10.1 Agro Dealer Dashboard
    path('agro/dashboard/', views.agro_dashboard, name='agro_dashboard'),
    path('agro/product/add/', views.agro_product_create, name='agro_product_create'),
    path('agro/product/<int:pk>/edit/', views.agro_product_update, name='agro_product_update'),
    path('agro/product/<int:pk>/delete/', views.agro_product_delete, name='agro_product_delete'),
]
