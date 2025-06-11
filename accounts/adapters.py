from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import perform_login
from django.contrib import messages
from django.shortcuts import redirect
from .mongo_utils import save_user_to_mongo
from .email_utils import send_login_notification
import jwt
from jwt.exceptions import InvalidTokenError, PyJWTError

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for social accounts to improve the login/signup flow
    """

    def pre_social_login(self, request, sociallogin):
        """
        Called before the social login is attempted
        """
        # Check if this social account is already connected to a user
        if sociallogin.is_existing:
            # If it's already connected, we don't need to do anything special
            return

        # Check if we have a user with the same email address
        email = sociallogin.account.extra_data.get('email')
        if email:
            from django.contrib.auth.models import User
            try:
                # Try to find users with this email
                users = User.objects.filter(email=email)

                # Handle case where multiple users have the same email
                if users.count() > 1:
                    # Get the most recently created user
                    user = users.order_by('-date_joined').first()

                    # Log this issue for admin review
                    print(f"Warning: Multiple users found with email {email}. Using most recent user.")

                    # Add a message for the user
                    messages.warning(
                        request,
                        "Multiple accounts found with this email. Using the most recent account."
                    )
                else:
                    # Just one user found
                    user = users.first()

                # Connect the social account to this user
                sociallogin.connect(request, user)

                # Update user settings for Google login
                try:
                    from accounts.models_user_extensions import get_user_settings
                    settings = get_user_settings(user)
                    if settings:
                        settings.connected_google = True
                        settings.save()
                except Exception as e:
                    print(f"Error updating user settings: {e}")

                # Send login notification email
                try:
                    # Get IP address from request
                    ip_address = self.get_client_ip(request)
                    # Get user agent from request
                    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
                    # Send login notification
                    send_login_notification(
                        user=user,
                        login_type="Google",
                        ip_address=ip_address,
                        device=user_agent
                    )
                except Exception as e:
                    print(f"Error sending login notification: {e}")

                # Add a success message
                messages.success(
                    request,
                    f"Successfully connected your Google account with {email}."
                )

                # Return to prevent the default behavior
                return
            except User.DoesNotExist:
                # No user with this email, continue with normal signup
                pass

    def save_user(self, request, sociallogin, form=None):
        """
        Called when a new user is created from a social account
        """
        # Call the parent method to save the user
        user = super().save_user(request, sociallogin, form)

        # Save additional user data to MongoDB
        mongo_id = save_user_to_mongo(user)

        # If MongoDB connection fails, we can still proceed with Django auth
        if mongo_id is None:
            print("Warning: Could not save user data to MongoDB, but Django user was created")

        # Update user settings for Google login
        try:
            from accounts.models_user_extensions import get_user_settings
            settings = get_user_settings(user)
            if settings:
                settings.connected_google = True
                settings.save()
        except Exception as e:
            print(f"Error updating user settings: {e}")

        # Send login notification email
        try:
            # Get IP address from request
            ip_address = self.get_client_ip(request)
            # Get user agent from request
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            # Send login notification
            send_login_notification(
                user=user,
                login_type="Google",
                ip_address=ip_address,
                device=user_agent
            )
        except Exception as e:
            print(f"Error sending login notification: {e}")

        # Add a success message
        messages.success(
            request,
            f"Welcome! Your account has been created with {user.email}."
        )

        return user

    def populate_user(self, request, sociallogin, data):
        """
        Called to populate the user instance from the social account data
        """
        user = super().populate_user(request, sociallogin, data)

        # Get profile data from Google
        social_data = sociallogin.account.extra_data

        # Set username to email (or part of it) to avoid username conflicts
        if user.email:
            username = user.email.split('@')[0]
            # Make sure username is unique
            from django.contrib.auth.models import User
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user.username = username

        # Get profile picture if available
        if 'picture' in social_data:
            # We'll store this in the session to use later
            if request and hasattr(request, 'session'):
                request.session['social_profile_picture'] = social_data.get('picture')

        return user

    def get_client_ip(self, request):
        """Get the client IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip