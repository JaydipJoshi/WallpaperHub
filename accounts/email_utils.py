"""
Email utilities for the accounts app
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import datetime

def send_login_notification(user, login_type="standard", ip_address=None, device=None):
    """
    Send a login notification email to the user
    
    Args:
        user: The user who logged in
        login_type: The type of login (standard, google, etc.)
        ip_address: The IP address of the login
        device: The device used for login
    """
    try:
        # Get the current time
        now = datetime.datetime.now()
        formatted_time = now.strftime("%B %d, %Y at %I:%M %p")
        
        # Prepare the context for the email template
        context = {
            'user': user,
            'login_type': login_type.capitalize(),
            'login_time': formatted_time,
            'ip_address': ip_address or 'Unknown',
            'device': device or 'Unknown',
            'year': datetime.datetime.now().year,
            'site_name': 'WallpaperHub',
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000',
        }
        
        # Render the HTML email template
        html_message = render_to_string('email/login_notification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send the email
        send_mail(
            subject=f'[WallpaperHub] New Login to Your Account',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@wallpaperhub.com',
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Error sending login notification email: {e}")
        return False


def send_newsletter_welcome_email(subscriber):
    """
    Send a welcome email to newsletter subscribers
    """
    print(f"Attempting to send welcome email to: {subscriber.email}")
    try:
        # Email context
        context = {
            'subscriber': subscriber,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000',
            'unsubscribe_url': subscriber.get_unsubscribe_url(),
            'current_year': datetime.datetime.now().year,
            'categories': [
                {'name': 'Nature', 'url': '/category/nature/'},
                {'name': 'Abstract', 'url': '/category/abstract/'},
                {'name': 'City', 'url': '/category/city/'},
                {'name': 'Space', 'url': '/category/space/'},
                {'name': 'Animals', 'url': '/category/animals/'},
                {'name': 'Technology', 'url': '/category/technology/'},
            ]
        }

        # Render the HTML email template
        html_message = render_to_string('email/newsletter_welcome.html', context)
        plain_message = strip_tags(html_message)

        # Send the email
        print(f"Sending email with subject: Welcome to WallpaperHub Newsletter! 🎨")
        print(f"To: {subscriber.email}")
        print(f"From: {settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@wallpaperhub.com'}")

        send_mail(
            subject='Welcome to WallpaperHub Newsletter! 🎨',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@wallpaperhub.com',
            recipient_list=[subscriber.email],
            html_message=html_message,
            fail_silently=False,
        )

        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending newsletter welcome email: {e}")
        return False
