from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.urls import reverse
from .mongo_utils import save_user_to_mongo, get_mongo_user
from .models_user_extensions import UserProfile
from .sms_service import send_welcome_sms, sms_service

# Create your views here.

def register_user(request):
    # Check if user is already authenticated
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('user_home')

    # Add social login context
    context = {
        'google_login_url': '/accounts/google/login/?process=login',
        'google_signup_url': '/accounts/google/login/?process=signup',
    }

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        phone_number = request.POST.get('phone_number', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'signUpPage.html', context)

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'signUpPage.html', context)

        # Validate and check phone number if provided
        if phone_number:
            is_valid, normalized_phone = sms_service.validate_phone_number(phone_number)
            if not is_valid:
                messages.error(request, f'Please enter a valid Indian mobile number. {normalized_phone}')
                return render(request, 'signUpPage.html', context)

            # Check if phone number already exists
            if UserProfile.objects.filter(phone_number=normalized_phone).exists():
                messages.error(request, 'Phone number already registered!')
                return render(request, 'signUpPage.html', context)

            phone_number = normalized_phone

        try:
            # Create the Django user
            user = User.objects.create_user(
                username=email,  # Using email as username
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Update user profile with phone number (UserProfile is created automatically via signal)
            if phone_number:
                user_profile = UserProfile.objects.get(user=user)
                user_profile.phone_number = phone_number
                user_profile.first_name = first_name
                user_profile.last_name = last_name
                user_profile.save()

                # Send welcome SMS if phone number provided
                try:
                    send_welcome_sms(phone_number, user.username)
                except Exception as e:
                    print(f"Failed to send welcome SMS: {e}")

            # Save additional user data to MongoDB
            mongo_id = save_user_to_mongo(user)

            # If MongoDB connection fails, we can still proceed with Django auth
            if mongo_id is None:
                print("Warning: Could not save user data to MongoDB, but Django user was created")

            # Log the user in with the ModelBackend
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Set success message in session
            success_msg = 'Account created successfully! Welcome to WallpaperHub.'
            if phone_number:
                success_msg += ' A welcome message has been sent to your phone.'
            messages.success(request, success_msg)

            # Redirect to home page with success parameter
            return redirect(reverse('user_home') + '?registered=success')
        except Exception as e:
            print(f"Error creating account: {str(e)}")
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'signUpPage.html', context)

    return render(request, 'signUpPage.html', context)

def login_user(request):
    # Check if user is already authenticated
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('user_home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate user with Django
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Log the user in with Django
            login(request, user)

            # Update MongoDB data
            mongo_result = save_user_to_mongo(user)
            if mongo_result is None:
                print("Warning: Could not update user data in MongoDB, but login successful")

            # Add success message
            messages.success(request, 'Login successful! Welcome back.')

            # Check if there's a next parameter in the URL
            next_url = request.GET.get('next', 'user_home')
            return redirect(next_url)  # Redirect to next URL or user_home
        else:
            messages.error(request, 'Invalid email or password!')
            return redirect('login')

    # Add social login context
    context = {
        'google_login_url': '/accounts/google/login/?process=login',
        'google_signup_url': '/accounts/google/login/?process=signup',
    }

    return render(request, 'loginPage.html', context)

def logout_user(request):
    # Log the user out with Django
    logout(request)

    # Add success message
    messages.success(request, 'Logout successful! See you soon.')
    return redirect('landing_page')

@login_required(login_url='/login/')
def profile(request):
    # Get additional user data from MongoDB
    mongo_user = get_mongo_user(request.user.id)

    return render(request, 'profile.html', {'mongo_user': mongo_user})

def check_oauth_urls(request):
    """View to display OAuth callback URLs for configuration"""
    current_site = Site.objects.get_current()
    return render(request, 'check_oauth_urls.html', {
        'current_site': current_site
    })
