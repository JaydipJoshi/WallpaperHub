"""
Newsletter subscription views for WallpaperHub
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
import json
import re
from .models import NewsletterSubscriber
from .email_utils import send_newsletter_welcome_email


def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_protect
@require_http_methods(["POST"])
def newsletter_subscribe(request):
    """
    Handle newsletter subscription via AJAX
    """
    print("=" * 50)
    print("NEWSLETTER SUBSCRIPTION REQUEST RECEIVED!")
    print("=" * 50)
    print(f"Request method: {request.method}")
    print(f"Request body: {request.body}")
    print(f"Content type: {request.content_type}")
    print(f"Request headers: {dict(request.headers)}")
    print("=" * 50)

    try:
        # Parse JSON data
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        print(f"Parsed email: {email}")
        
        # Validate email
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email address is required.'
            }, status=400)
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'error': 'Please enter a valid email address.'
            }, status=400)
        
        # Check if already subscribed
        existing_subscriber = NewsletterSubscriber.objects.filter(email=email).first()
        
        if existing_subscriber:
            if existing_subscriber.is_active:
                return JsonResponse({
                    'success': False,
                    'error': 'This email is already subscribed to our newsletter.'
                }, status=400)
            else:
                # Reactivate subscription
                existing_subscriber.is_active = True
                existing_subscriber.subscribed_at = timezone.now()
                existing_subscriber.ip_address = get_client_ip(request)
                existing_subscriber.user_agent = request.META.get('HTTP_USER_AGENT', '')
                existing_subscriber.save()
                
                # Send welcome email
                email_sent = send_newsletter_welcome_email(existing_subscriber)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Welcome back! Your subscription has been reactivated.',
                    'email_sent': email_sent
                })
        
        # Create new subscription
        subscriber = NewsletterSubscriber.objects.create(
            email=email,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            source='footer_form'
        )
        
        # Link to user if authenticated
        if request.user.is_authenticated:
            subscriber.user = request.user
            subscriber.save()
        
        # Send welcome email
        email_sent = send_newsletter_welcome_email(subscriber)
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for subscribing! Check your email for a welcome message.',
            'email_sent': email_sent
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format.'
        }, status=400)
    
    except Exception as e:
        print(f"Newsletter subscription error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again later.'
        }, status=500)


@cache_page(60 * 15)  # Cache for 15 minutes
def newsletter_unsubscribe(request, token):
    """
    Handle newsletter unsubscription
    """
    try:
        subscriber = get_object_or_404(NewsletterSubscriber, unsubscribe_token=token)
        
        if request.method == 'POST':
            subscriber.unsubscribe()
            messages.success(request, 'You have been successfully unsubscribed from our newsletter.')
            return render(request, 'newsletter/unsubscribe_success.html', {
                'subscriber': subscriber
            })
        
        return render(request, 'newsletter/unsubscribe_confirm.html', {
            'subscriber': subscriber
        })
        
    except Exception as e:
        print(f"Newsletter unsubscribe error: {e}")
        messages.error(request, 'Invalid unsubscribe link.')
        return render(request, 'newsletter/unsubscribe_error.html')


@vary_on_headers('User-Agent')
def newsletter_preferences(request, token):
    """
    Newsletter preferences page (for future enhancements)
    """
    try:
        subscriber = get_object_or_404(NewsletterSubscriber, unsubscribe_token=token)
        
        return render(request, 'newsletter/preferences.html', {
            'subscriber': subscriber
        })
        
    except Exception as e:
        print(f"Newsletter preferences error: {e}")
        messages.error(request, 'Invalid preferences link.')
        return render(request, 'newsletter/preferences_error.html')


def newsletter_stats(request):
    """
    Simple newsletter statistics (admin only)
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    total_subscribers = NewsletterSubscriber.objects.count()
    active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
    recent_subscribers = NewsletterSubscriber.objects.filter(
        subscribed_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    
    return JsonResponse({
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'recent_subscribers': recent_subscribers,
        'unsubscribed': total_subscribers - active_subscribers
    })
