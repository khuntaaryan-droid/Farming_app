import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Case, When, Value, IntegerField
from .models import Product, Category, PriceReference, AgroProduct
from .forms import ProductForm, AgroProductForm

def product_list(request):
    if request.user.is_authenticated:
        if request.user.role == 'AGRO_DEALER':
            return redirect('agro_dashboard')
        elif request.user.role == 'FARMER':
            return redirect('farmer_sales')
            
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    is_organic = request.GET.get('organic', '')
    quality = request.GET.get('quality', '')

    products = Product.objects.filter(is_active=True)

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        products = products.filter(category_id=category_id)
    if is_organic:
        products = products.filter(is_organic=True)
    if quality:
        products = products.filter(quality_grade=quality)

    sort_by = request.GET.get('sort', '')
    if sort_by == 'nearest' and request.user.is_authenticated:
        user_city = request.user.village_or_city.lower().strip()
        user_state = request.user.state.lower().strip()
        
        products = products.annotate(
            location_rank=Case(
                When(farmer__village_or_city__iexact=user_city, farmer__state__iexact=user_state, then=Value(1)),
                When(farmer__state__iexact=user_state, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('location_rank', '-created_at')
    else:
        products = products.order_by('-created_at')

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'quality_choices': Product.QUALITY_CHOICES,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return render(request, 'products/product_detail.html', {'product': product})

@login_required
def product_create(request):
    if request.user.role != 'FARMER':
        messages.error(request, 'Only farmers can add products.')
        return redirect('product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.farmer = request.user
            product.save()
            messages.success(request, 'Product added successfully.')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm()

    price_refs = {ref.crop_name.lower(): float(ref.avg_price) for ref in PriceReference.objects.all()}

    return render(request, 'products/product_form.html', {
        'form': form, 
        'title': 'Add Product',
        'price_refs_json': json.dumps(price_refs)
    })

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, farmer=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)

    price_refs = {ref.crop_name.lower(): float(ref.avg_price) for ref in PriceReference.objects.all()}

    return render(request, 'products/product_form.html', {
        'form': form, 
        'title': 'Edit Product',
        'price_refs_json': json.dumps(price_refs)
    })

import random

@login_required
def crop_doctor(request):
    from .forms import CropDiseaseQueryForm
    
    # Only farmers or anyone can use this? Let's say farmers.
    if request.user.role != 'FARMER':
        messages.error(request, 'Only farmers can use the AI Crop Doctor.')
        return redirect('product_list')
        
    result = None
    
    if request.method == 'POST':
        form = CropDiseaseQueryForm(request.POST, request.FILES)
        if form.is_valid():
            query = form.save(commit=False)
            query.farmer = request.user
            
            # Simulate AI processing based on crop name and symptoms
            symptoms = query.symptoms.lower()
            if 'yellow' in symptoms or 'spot' in symptoms:
                diagnosis = "Detected: Early Blight (Fungal Infection). Recommendation: Apply Copper-based Fungicide immediately. Ensure proper spacing between plants for air circulation."
            elif 'dry' in symptoms or 'brown' in symptoms:
                diagnosis = "Detected: Drought Stress / Heat Damage. Recommendation: Increase irrigation frequency and apply organic mulch to retain soil moisture."
            elif 'white' in symptoms or 'powder' in symptoms:
                diagnosis = "Detected: Powdery Mildew. Recommendation: Spray neem oil or sulfur-based organic fungicide. Remove severely affected leaves."
            else:
                diseases = [
                    "Detected: Leaf Miner Infestation. Recommendation: Use Spinosad or Neem oil spray.",
                    "Detected: Aphids. Recommendation: Spray insecticidal soap or release ladybugs.",
                    "Detected: Nutrient Deficiency (Nitrogen/Potassium). Recommendation: Apply a balanced NPK fertilizer."
                ]
                diagnosis = random.choice(diseases)
                
            query.ai_diagnosis = diagnosis
            query.save()
            result = query
    else:
        form = CropDiseaseQueryForm()
        
    return render(request, 'products/crop_doctor.html', {'form': form, 'result': result})

@login_required
def forum_list(request):
    from .models import ForumPost
    posts = ForumPost.objects.all().order_by('-created_at')
    return render(request, 'products/forum_list.html', {'posts': posts})

@login_required
def forum_detail(request, pk):
    from .models import ForumPost, ForumComment
    post = get_object_or_404(ForumPost, pk=pk)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            ForumComment.objects.create(post=post, author=request.user, content=content)
            messages.success(request, 'Your comment was added.')
            return redirect('forum_detail', pk=pk)
            
    return render(request, 'products/forum_detail.html', {'post': post})

@login_required
def forum_create(request):
    from .models import ForumPost
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        if title and content:
            post = ForumPost.objects.create(author=request.user, title=title, content=content)
            messages.success(request, 'Post created successfully.')
            return redirect('forum_detail', pk=post.id)
    return render(request, 'products/forum_create.html')

def schemes_list(request):
    from .models import GovernmentScheme
    schemes = GovernmentScheme.objects.all().order_by('-created_at')
    # If empty, create some mock schemes for demo
    if not schemes.exists():
        GovernmentScheme.objects.create(
            title="PM-Kisan Samman Nidhi", 
            description="Get ₹6000 per year as income support.", 
            link="https://pmkisan.gov.in/"
        )
        GovernmentScheme.objects.create(
            title="Sub-Mission on Agricultural Mechanization (SMAM)", 
            description="Subsidy on purchase of agricultural machinery and tractors.", 
            link="https://agrimachinery.nic.in/"
        )
        schemes = GovernmentScheme.objects.all().order_by('-created_at')
        
    return render(request, 'products/schemes.html', {'schemes': schemes})

@login_required
def machinery_list(request):
    from .models import AgriMachinery
    machinery = AgriMachinery.objects.filter(is_available=True).order_by('-created_at')
    return render(request, 'products/machinery_list.html', {'machinery': machinery})

@login_required
def machinery_create(request):
    if request.user.role != 'FARMER':
        messages.error(request, 'Only farmers can list machinery for rent.')
        return redirect('machinery_list')
        
    from .models import AgriMachinery
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        hourly_rate = request.POST.get('hourly_rate')
        image = request.FILES.get('image')
        
        if name and hourly_rate:
            AgriMachinery.objects.create(
                farmer=request.user,
                name=name,
                description=description,
                hourly_rate=hourly_rate,
                image=image
            )
            messages.success(request, 'Machinery listed for rent successfully!')
            return redirect('machinery_list')
            
    return render(request, 'products/machinery_create.html')

@login_required
def book_farm_visit(request, farmer_username):
    from django.contrib.auth import get_user_model
    CustomUser = get_user_model()
    from .models import FarmVisit
    farmer = get_object_or_404(CustomUser, username=farmer_username, role='FARMER')
    
    if request.user == farmer:
        messages.error(request, 'You cannot book a visit to your own farm.')
        return redirect('product_list')
        
    if request.method == 'POST':
        date = request.POST.get('scheduled_date')
        guests = request.POST.get('guest_count', 1)
        
        if date:
            FarmVisit.objects.create(
                farmer=farmer,
                buyer=request.user,
                scheduled_date=date,
                guest_count=guests
            )
            messages.success(request, f'Visit request sent to {farmer.get_full_name()}!')
            return redirect('product_list')
            
    return render(request, 'products/book_visit.html', {'farmer': farmer})

# Static Pages
def about_us(request):
    return render(request, 'pages/about.html')

def contact_us(request):
    return render(request, 'pages/contact.html')

def faq(request):
    return render(request, 'pages/faq.html')

def terms(request):
    return render(request, 'pages/terms.html')

def return_policy(request):
    return render(request, 'pages/return_policy.html')

def farm_map(request):
    from django.contrib.auth import get_user_model
    CustomUser = get_user_model()
    # Fetch all active farmers
    farmers = CustomUser.objects.filter(role='FARMER', is_active=True)
    
    # We will pass farmer data to the frontend to render pins on the map
    farmer_data = []
    # Using some dummy coordinates centered around Gujarat for demo purposes
    # Latitude: 21.0 to 24.0, Longitude: 70.0 to 74.0
    for f in farmers:
        lat = 22.2587 + (hash(f.username) % 200 - 100) / 100.0  # Random spread around Gujarat
        lng = 71.1924 + (hash(f.village_or_city) % 200 - 100) / 100.0 if f.village_or_city else 71.1924 + (hash(f.username) % 200 - 100) / 100.0
        
        farmer_data.append({
            'username': f.username,
            'name': f.get_full_name() or f.username,
            'city': f.village_or_city or 'Gujarat',
            'lat': lat,
            'lng': lng
        })
        
    return render(request, 'products/map.html', {'farmer_data_json': json.dumps(farmer_data)})

def live_streams(request):
    # Simulated live streams data
    streams = [
        {
            'id': 1,
            'farmer_name': 'Ramesh Bhai',
            'title': 'Fresh Organic Tomatoes Harvesting LIVE',
            'viewers': random.randint(50, 300),
            'thumbnail': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500&q=80',
            'product_id': Product.objects.filter(name__icontains='tomato').first().id if Product.objects.filter(name__icontains='tomato').exists() else None
        },
        {
            'id': 2,
            'farmer_name': 'Suresh Patel',
            'title': 'Farm Tour & Mango Orchards',
            'viewers': random.randint(100, 500),
            'thumbnail': 'https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?w=500&q=80',
            'product_id': Product.objects.filter(name__icontains='mango').first().id if Product.objects.filter(name__icontains='mango').exists() else None
        }
    ]
    return render(request, 'products/live.html', {'streams': streams})

@login_required
def start_live(request):
    if request.user.role != 'FARMER':
        messages.error(request, 'Only farmers can start a live stream.')
        return redirect('product_list')
        
    my_products = Product.objects.filter(farmer=request.user, is_active=True)
    return render(request, 'products/start_live.html', {'my_products': my_products})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import google.generativeai as genai

@csrf_exempt
def ai_chatbot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            
            # Configure Gemini API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Create the model
            generation_config = {
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
            }
            
            model = genai.GenerativeModel(
                model_name="gemini-3.5-flash",
                generation_config=generation_config,
                system_instruction="You are an expert AI Assistant for an AgTech platform named 'Agri Shop'. Your users are either Indian farmers asking for agricultural advice (crop disease, fertilizer, weather, market trends) or buyers asking for recipes and tips for fresh produce. Provide concise, helpful, and friendly answers. You can speak English, Hindi, or Gujarati depending on the user's language."
            )
            
            # Generate response
            response = model.generate_content(message)
            ai_reply = response.text
                
            return JsonResponse({'reply': ai_reply})
        except Exception as e:
            # Fallback for API issues
            return JsonResponse({'error': str(e), 'reply': 'I am currently experiencing technical difficulties connecting to my brain. Please try again later.'}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Phase 10: Agro Store
def agro_store(request):
    category = request.GET.get('category', '')
    query = request.GET.get('q', '')
    
    products = AgroProduct.objects.filter(is_active=True)
    
    if query:
        products = products.filter(name__icontains=query)
    if category:
        products = products.filter(category=category)
        
    return render(request, 'products/agro_store.html', {'products': products})

def agro_product_detail(request, pk):
    product = get_object_or_404(AgroProduct, pk=pk)
    return render(request, 'products/agro_product_detail.html', {'product': product})

# Phase 10.1: Agro Dealer Dashboard
@login_required
def agro_dashboard(request):
    if request.user.role != 'AGRO_DEALER':
        messages.error(request, 'Access denied. You are not registered as an Agro Dealer.')
        return redirect('product_list')
    
    products = request.user.agro_products.all().order_by('-created_at')
    
    # Fetch Agro Orders for this dealer
    from orders.models import AgroOrderItem
    agro_order_items = AgroOrderItem.objects.filter(dealer=request.user).order_by('-order__created_at')
    
    # We want unique orders to display in the dashboard
    orders = []
    seen_orders = set()
    for item in agro_order_items:
        if item.order.id not in seen_orders:
            orders.append(item.order)
            seen_orders.add(item.order.id)
            
    return render(request, 'products/agro_dashboard.html', {'products': products, 'orders': orders})

@login_required
def agro_product_create(request):
    if request.user.role != 'AGRO_DEALER':
        return redirect('product_list')
        
    if request.method == 'POST':
        form = AgroProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.dealer = request.user
            product.save()
            messages.success(request, 'Agro product added successfully!')
            return redirect('agro_dashboard')
    else:
        form = AgroProductForm()
    return render(request, 'products/agro_product_form.html', {'form': form, 'is_edit': False})

@login_required
def agro_product_update(request, pk):
    product = get_object_or_404(AgroProduct, pk=pk, dealer=request.user)
    if request.method == 'POST':
        form = AgroProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agro product updated successfully!')
            return redirect('agro_dashboard')
    else:
        form = AgroProductForm(instance=product)
    return render(request, 'products/agro_product_form.html', {'form': form, 'is_edit': True})

@login_required
def agro_product_delete(request, pk):
    product = get_object_or_404(AgroProduct, pk=pk, dealer=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('agro_dashboard')
    return render(request, 'products/agro_product_confirm_delete.html', {'product': product})

