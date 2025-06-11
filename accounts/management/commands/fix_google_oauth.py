from django.core.management.base import BaseCommand
from accounts.direct_jwt_patch import apply_direct_patch
from accounts.google_jwt_patch import direct_patch_google_oauth

class Command(BaseCommand):
    help = 'Fix Google OAuth JWT verification issues'

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
