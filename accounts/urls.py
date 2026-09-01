from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

from .forms import RoleAuthenticationForm

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('farmer/<str:username>/', views.farmer_profile, name='farmer_profile'),
    
    # Notifications API
    path('api/notifications/unread/', views.get_unread_notifications, name='get_unread_notifications'),
    path('api/notifications/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]
