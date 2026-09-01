from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserChangeForm, RoleAuthenticationForm
from .models import User

from django.urls import reverse

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = RoleAuthenticationForm
    
    def get_success_url(self):
        user = self.request.user
        if user.role == 'AGRO_DEALER':
            return reverse('agro_dashboard')
        elif user.role == 'FARMER':
            return reverse('farmer_sales')
        return '/'

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Send welcome email
            try:
                from .email_utils import send_welcome_email
                send_welcome_email(user)
            except Exception as e:
                # Log or handle exception silently so user login doesn't crash if email fails
                pass
                
            messages.success(request, 'Registration successful! Welcome to Agri Shop.')
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
        
    return render(request, 'accounts/profile.html', {'form': form})

def farmer_profile(request, username):
    farmer = get_object_or_404(User, username=username, role=User.Role.FARMER)
    products = farmer.products.filter(is_active=True)
    reviews = farmer.reviews_received.all().order_by('-created_at')
    
    return render(request, 'accounts/farmer_profile.html', {
        'farmer': farmer,
        'products': products,
        'reviews': reviews
    })

from django.http import JsonResponse

@login_required
def get_unread_notifications(request):
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'message': notif.message,
            'link': notif.link,
            'created_at': notif.created_at.strftime('%b %d, %I:%M %p')
        })
    return JsonResponse({'notifications': data, 'count': len(data)})

@login_required
def mark_notification_read(request, notif_id):
    if request.method == 'POST':
        notif = get_object_or_404(request.user.notifications, id=notif_id)
        notif.is_read = True
        notif.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
