from django.core.management.base import BaseCommand
from accounts.direct_jwt_patch import apply_direct_patch
from accounts.google_jwt_patch import direct_patch_google_oauth
from accounts.google_adapter import setup_custom_google_adapter
from accounts.bypass_jwt import bypass_google_jwt_verification

class Command(BaseCommand):
    help = 'Apply all fixes for Google OAuth JWT verification issues'

    def handle(self, *args, **options):
        # Apply the direct patch to jwtkit.py
        if apply_direct_patch():
            self.stdout.write(self.style.SUCCESS("Successfully patched django-allauth JWT verification"))
        else:
            self.stdout.write(self.style.ERROR("Failed to patch django-allauth JWT verification"))
        
        # Apply the patch to Google OAuth provider
        if direct_patch_google_oauth():
            self.stdout.write(self.style.SUCCESS("Successfully patched Google OAuth provider"))
        else:
            self.stdout.write(self.style.ERROR("Failed to patch Google OAuth provider"))
        
        # Set up the custom Google OAuth adapter
        if setup_custom_google_adapter():
            self.stdout.write(self.style.SUCCESS("Successfully set up custom Google OAuth adapter"))
        else:
            self.stdout.write(self.style.ERROR("Failed to set up custom Google OAuth adapter"))
        
        # Bypass JWT verification
        if bypass_google_jwt_verification():
            self.stdout.write(self.style.SUCCESS("Successfully bypassed Google JWT verification"))
        else:
            self.stdout.write(self.style.ERROR("Failed to bypass Google JWT verification"))
