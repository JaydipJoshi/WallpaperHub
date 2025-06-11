from django.core.management.base import BaseCommand
import os
import re

class Command(BaseCommand):
    help = 'Patch django-allauth to fix JWT verification issues'

    def handle(self, *args, **options):
        try:
            # Find the allauth jwtkit.py file
            import allauth
            allauth_path = os.path.dirname(allauth.__file__)
            jwtkit_path = os.path.join(allauth_path, 'socialaccount', 'internal', 'jwtkit.py')
            
            if not os.path.exists(jwtkit_path):
                self.stdout.write(self.style.ERROR(f"Could not find jwtkit.py at {jwtkit_path}"))
                return
            
            # Read the file
            with open(jwtkit_path, 'r') as f:
                content = f.read()
            
            # Check if the file already contains our patch
            if 'PyJWTError = getattr(jwt, "PyJWTError", Exception)' in content:
                self.stdout.write(self.style.SUCCESS("File already patched"))
                return
            
            # Apply the patch
            # Add import for InvalidTokenError
            content = re.sub(
                r'import jwt\n',
                'import jwt\nfrom jwt.exceptions import InvalidTokenError\n',
                content
            )
            
            # Add PyJWTError definition
            content = re.sub(
                r'import jwt\nfrom jwt.exceptions import InvalidTokenError\n',
                'import jwt\nfrom jwt.exceptions import InvalidTokenError\n\n# Compatibility for different PyJWT versions\nPyJWTError = getattr(jwt, "PyJWTError", InvalidTokenError)\n',
                content
            )
            
            # Replace jwt.PyJWTError with PyJWTError
            content = content.replace('jwt.PyJWTError', 'PyJWTError')
            
            # Write the patched file
            with open(jwtkit_path, 'w') as f:
                f.write(content)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully patched {jwtkit_path}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error patching allauth: {str(e)}"))
