"""
Custom adapter for Google OAuth authentication
"""

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.conf import settings
import requests
import json

class CustomGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    """
    Custom adapter for Google OAuth2 that handles token verification differently
    """
    
    def complete_login(self, request, app, token, **kwargs):
        """
        Completes the login process by fetching user info directly from Google
        """
        try:
            # First try the standard approach
            return super().complete_login(request, app, token, **kwargs)
        except Exception as e:
            print(f"Standard Google OAuth login failed: {str(e)}")
            
            # Fallback: Get user info directly from Google API
            try:
                # Get the access token
                access_token = token.token
                
                # Use the access token to get user info directly from Google
                headers = {"Authorization": f"Bearer {access_token}"}
                resp = requests.get(
                    "https://www.googleapis.com/oauth2/v1/userinfo",
                    headers=headers
                )
                
                if resp.status_code != 200:
                    raise Exception(f"Failed to get user info: {resp.text}")
                
                # Parse the user info
                user_data = resp.json()
                
                # Create a login object
                from allauth.socialaccount.models import SocialLogin
                from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView, OAuth2CallbackView
                
                # Create a social account
                from allauth.socialaccount.providers.google.provider import GoogleProvider
                provider = GoogleProvider(request)
                
                # Create a social account
                from allauth.socialaccount.models import SocialAccount
                account = SocialAccount(provider=provider.id, uid=user_data["id"])
                
                # Set the extra data
                account.extra_data = user_data
                
                # Create a social login
                login = SocialLogin(account=account)
                
                # Set the user's email and name
                login.user = self.get_provider().sociallogin_from_response(
                    request, user_data
                ).user
                
                return login
            except Exception as inner_e:
                # If all else fails, raise the original error
                raise Exception(f"Google OAuth login failed: {str(e)}, Fallback failed: {str(inner_e)}")

def setup_custom_google_adapter():
    """
    Set up the custom Google OAuth adapter
    """
    try:
        # Import the Google OAuth views
        from allauth.socialaccount.providers.google import views as google_views
        
        # Replace the adapter with our custom one
        google_views.GoogleOAuth2Adapter = CustomGoogleOAuth2Adapter
        
        print("Successfully set up custom Google OAuth adapter")
        return True
    except Exception as e:
        print(f"Error setting up custom Google OAuth adapter: {str(e)}")
        return False
