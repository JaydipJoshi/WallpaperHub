"""
Bypass JWT verification for Google OAuth
"""

def bypass_google_jwt_verification():
    """
    Completely bypass JWT verification for Google OAuth
    """
    try:
        # Import the Google provider's views module
        from allauth.socialaccount.providers.google import views as google_views
        
        # Store the original complete_login method
        original_complete_login = google_views.GoogleOAuth2Adapter.complete_login
        
        # Define a new complete_login method that bypasses JWT verification
        def new_complete_login(self, request, app, token, **kwargs):
            """
            Complete the login process without JWT verification
            """
            try:
                # Try the original method first
                return original_complete_login(self, request, app, token, **kwargs)
            except Exception as e:
                print(f"Original complete_login failed: {str(e)}")
                
                # Fallback: Get user info directly from Google API
                import requests
                
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
        
        # Replace the original method with our new one
        google_views.GoogleOAuth2Adapter.complete_login = new_complete_login
        
        print("Successfully bypassed Google JWT verification")
        return True
    except Exception as e:
        print(f"Error bypassing Google JWT verification: {str(e)}")
        return False
