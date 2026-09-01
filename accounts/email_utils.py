from django.core.mail import send_mail
from django.conf import settings

def send_welcome_email(user):
    subject = 'Welcome to Agri Shop!'
    message = f'''Hello {user.get_full_name() or user.username},

Welcome to Agri Shop - the direct farmer-to-buyer marketplace! 

We are thrilled to have you on board.
'''
    if user.role == 'FARMER':
        message += '\nYou can now start listing your fresh produce and selling directly to buyers.'
    else:
        message += '\nYou can now browse fresh produce directly from farmers in your area.'
        
    message += '\n\nThank you,\nThe Agri Shop Team'
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
