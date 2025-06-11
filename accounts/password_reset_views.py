"""
Password reset views for WallpaperHub
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import json
import re
from .models import PasswordResetOTP
from .models_user_extensions import UserProfile
from .sms_service import send_password_reset_sms, sms_service


def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def validate_phone_number(phone):
    """Validate phone number format using SMS service validation"""
    try:
        is_valid, result = sms_service.validate_phone_number(phone)
        return is_valid
    except Exception as e:
        print(f"Phone validation error: {e}")
        return False


def send_otp_email(otp_instance):
    """Send OTP via email"""
    try:
        context = {
            'otp_code': otp_instance.otp_code,
            'contact_value': otp_instance.contact_value,
            'expires_minutes': 10,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000',
        }
        
        html_message = render_to_string('email/password_reset_otp.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='WallpaperHub - Password Reset Code',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@wallpaperhub.com',
            recipient_list=[otp_instance.contact_value],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Error sending OTP email: {e}")
        return False


def send_otp_sms(otp_instance):
    """Send OTP via SMS using SMS service"""
    try:
        success, message = send_password_reset_sms(
            otp_instance.contact_value,
            otp_instance.otp_code
        )

        if success:
            print(f"SMS OTP sent successfully: {message}")
            return True
        else:
            print(f"SMS OTP failed: {message}")
            return False

    except Exception as e:
        print(f"Error sending OTP SMS: {e}")
        return False


def forgot_password(request):
    """Main forgot password page"""
    return render(request, 'forgot_password.html')


@csrf_protect
@require_http_methods(["POST"])
def forgot_password_step1(request):
    """Step 1: Handle contact input (email or phone)"""
    print("=" * 50)
    print("FORGOT PASSWORD STEP 1 REQUEST RECEIVED!")
    print("=" * 50)
    print(f"Request method: {request.method}")
    print(f"Request body: {request.body}")
    print(f"Content type: {request.content_type}")
    print(f"Request headers: {dict(request.headers)}")
    print("=" * 50)

    try:
        data = json.loads(request.body)
        contact_value = data.get('contact_value', '').strip()
        contact_type = data.get('contact_type', '').strip()
        print(f"Parsed data - Contact: {contact_value}, Type: {contact_type}")
        
        if not contact_value or not contact_type:
            return JsonResponse({
                'success': False,
                'error': 'Contact information is required.'
            }, status=400)
        
        # Validate contact based on type
        if contact_type == 'email':
            try:
                validate_email(contact_value)
                contact_value = contact_value.lower()
            except ValidationError:
                return JsonResponse({
                    'success': False,
                    'error': 'Please enter a valid email address.'
                }, status=400)
        elif contact_type == 'phone':
            if not validate_phone_number(contact_value):
                return JsonResponse({
                    'success': False,
                    'error': 'Please enter a valid phone number.'
                }, status=400)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid contact type.'
            }, status=400)
        
        # Check if user exists with this contact
        user = None
        if contact_type == 'email':
            try:
                user = User.objects.get(email=contact_value)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'No account found with this email address.'
                }, status=404)
        elif contact_type == 'phone':
            # Normalize phone number for lookup
            is_valid, normalized_phone = sms_service.validate_phone_number(contact_value)
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'error': 'Please enter a valid phone number.'
                }, status=400)

            try:
                # Look up user by phone number in UserProfile
                user_profile = UserProfile.objects.get(phone_number=normalized_phone)
                user = user_profile.user
                contact_value = normalized_phone  # Use normalized phone for OTP
            except UserProfile.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'No account found with this phone number.'
                }, status=404)
        
        # Generate OTP
        otp_instance = PasswordResetOTP.generate_otp(
            contact_value=contact_value,
            contact_type=contact_type,
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send OTP
        if contact_type == 'email':
            otp_sent = send_otp_email(otp_instance)
        else:
            otp_sent = send_otp_sms(otp_instance)
        
        if not otp_sent:
            return JsonResponse({
                'success': False,
                'error': 'Failed to send verification code. Please try again.'
            }, status=500)
        
        # Store OTP ID in session for verification
        request.session['password_reset_otp_id'] = otp_instance.id
        request.session['password_reset_contact'] = contact_value
        request.session['password_reset_type'] = contact_type
        
        return JsonResponse({
            'success': True,
            'message': f'Verification code sent to your {contact_type}.',
            'contact_masked': mask_contact(contact_value, contact_type)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format.'
        }, status=400)
    except Exception as e:
        print(f"Password reset step 1 error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again later.'
        }, status=500)


def mask_contact(contact_value, contact_type):
    """Mask contact information for display"""
    if contact_type == 'email':
        parts = contact_value.split('@')
        if len(parts) == 2:
            username = parts[0]
            domain = parts[1]
            if len(username) > 2:
                masked_username = username[:2] + '*' * (len(username) - 2)
            else:
                masked_username = '*' * len(username)
            return f"{masked_username}@{domain}"
    elif contact_type == 'phone':
        if len(contact_value) > 4:
            return contact_value[:2] + '*' * (len(contact_value) - 4) + contact_value[-2:]
    
    return contact_value


@csrf_protect
@require_http_methods(["POST"])
def forgot_password_step2(request):
    """Step 2: Verify OTP"""
    try:
        data = json.loads(request.body)
        otp_code = data.get('otp_code', '').strip()
        
        if not otp_code:
            return JsonResponse({
                'success': False,
                'error': 'Verification code is required.'
            }, status=400)
        
        # Get OTP from session
        otp_id = request.session.get('password_reset_otp_id')
        if not otp_id:
            return JsonResponse({
                'success': False,
                'error': 'Session expired. Please start over.'
            }, status=400)
        
        try:
            otp_instance = PasswordResetOTP.objects.get(id=otp_id)
        except PasswordResetOTP.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid verification session.'
            }, status=400)
        
        # Verify OTP
        if otp_instance.verify_otp(otp_code):
            request.session['password_reset_verified'] = True
            return JsonResponse({
                'success': True,
                'message': 'Verification successful! You can now reset your password.'
            })
        else:
            error_msg = 'Invalid verification code.'
            if otp_instance.is_expired():
                error_msg = 'Verification code has expired.'
            elif otp_instance.attempts >= 5:
                error_msg = 'Too many failed attempts. Please request a new code.'
            
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'attempts_remaining': max(0, 5 - otp_instance.attempts)
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format.'
        }, status=400)
    except Exception as e:
        print(f"Password reset step 2 error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again later.'
        }, status=500)


@csrf_protect
@require_http_methods(["POST"])
def forgot_password_resend_otp(request):
    """Resend OTP"""
    try:
        # Get current OTP from session
        otp_id = request.session.get('password_reset_otp_id')
        contact_value = request.session.get('password_reset_contact')
        contact_type = request.session.get('password_reset_type')
        
        if not all([otp_id, contact_value, contact_type]):
            return JsonResponse({
                'success': False,
                'error': 'Session expired. Please start over.'
            }, status=400)
        
        try:
            old_otp = PasswordResetOTP.objects.get(id=otp_id)
            user = old_otp.user
        except PasswordResetOTP.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid session.'
            }, status=400)
        
        # Generate new OTP
        otp_instance = PasswordResetOTP.generate_otp(
            contact_value=contact_value,
            contact_type=contact_type,
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send new OTP
        if contact_type == 'email':
            otp_sent = send_otp_email(otp_instance)
        else:
            otp_sent = send_otp_sms(otp_instance)
        
        if not otp_sent:
            return JsonResponse({
                'success': False,
                'error': 'Failed to send verification code. Please try again.'
            }, status=500)
        
        # Update session with new OTP ID
        request.session['password_reset_otp_id'] = otp_instance.id
        
        return JsonResponse({
            'success': True,
            'message': 'New verification code sent successfully.'
        })

    except Exception as e:
        print(f"Password reset resend OTP error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again later.'
        }, status=500)


@csrf_protect
@require_http_methods(["POST"])
def forgot_password_step3(request):
    """Step 3: Reset password"""
    try:
        data = json.loads(request.body)
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()

        if not new_password or not confirm_password:
            return JsonResponse({
                'success': False,
                'error': 'Both password fields are required.'
            }, status=400)

        if new_password != confirm_password:
            return JsonResponse({
                'success': False,
                'error': 'Passwords do not match.'
            }, status=400)

        # Validate password strength
        if len(new_password) < 8:
            return JsonResponse({
                'success': False,
                'error': 'Password must be at least 8 characters long.'
            }, status=400)

        # Check if OTP was verified
        if not request.session.get('password_reset_verified'):
            return JsonResponse({
                'success': False,
                'error': 'Please verify your identity first.'
            }, status=400)

        # Get OTP instance
        otp_id = request.session.get('password_reset_otp_id')
        if not otp_id:
            return JsonResponse({
                'success': False,
                'error': 'Session expired. Please start over.'
            }, status=400)

        try:
            otp_instance = PasswordResetOTP.objects.get(id=otp_id, is_verified=True)
            user = otp_instance.user
        except PasswordResetOTP.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid verification session.'
            }, status=400)

        # Update user password
        user.set_password(new_password)
        user.save()

        # Mark OTP as used
        otp_instance.is_used = True
        otp_instance.save()

        # Clear session data
        session_keys = [
            'password_reset_otp_id',
            'password_reset_contact',
            'password_reset_type',
            'password_reset_verified'
        ]
        for key in session_keys:
            request.session.pop(key, None)

        # Log the user in
        login(request, user)

        return JsonResponse({
            'success': True,
            'message': 'Password reset successful! You are now logged in.',
            'redirect_url': '/userHome/'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format.'
        }, status=400)
    except Exception as e:
        print(f"Password reset step 3 error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again later.'
        }, status=500)


def validate_password_strength(password):
    """Validate password strength and return feedback"""
    feedback = {
        'score': 0,
        'suggestions': [],
        'is_strong': False
    }

    if len(password) >= 8:
        feedback['score'] += 1
    else:
        feedback['suggestions'].append('Use at least 8 characters')

    if re.search(r'[a-z]', password):
        feedback['score'] += 1
    else:
        feedback['suggestions'].append('Include lowercase letters')

    if re.search(r'[A-Z]', password):
        feedback['score'] += 1
    else:
        feedback['suggestions'].append('Include uppercase letters')

    if re.search(r'\d', password):
        feedback['score'] += 1
    else:
        feedback['suggestions'].append('Include numbers')

    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        feedback['score'] += 1
    else:
        feedback['suggestions'].append('Include special characters')

    feedback['is_strong'] = feedback['score'] >= 4

    return feedback


@csrf_protect
@require_http_methods(["POST"])
def check_password_strength(request):
    """Check password strength for real-time feedback"""
    try:
        data = json.loads(request.body)
        password = data.get('password', '')

        feedback = validate_password_strength(password)

        return JsonResponse({
            'success': True,
            'feedback': feedback
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format.'
        }, status=400)
    except Exception as e:
        print(f"Password strength check error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred.'
        }, status=500)
