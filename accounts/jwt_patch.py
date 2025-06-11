"""
Monkey patch for django-allauth to fix JWT verification issues with newer versions of PyJWT
"""

import jwt
from jwt.exceptions import InvalidTokenError, PyJWTError

# Store the original decode function
original_decode = jwt.decode

def patched_verify_and_decode(token, key, verify_signature=True, **kwargs):
    """
    A patched version of the verify_and_decode function from allauth
    that works with both older and newer versions of PyJWT
    """
    try:
        # Use the original decode function with the correct parameters
        if verify_signature:
            return original_decode(
                token,
                key,
                algorithms=['RS256', 'HS256'],
                options={"verify_signature": verify_signature},
                **kwargs
            )
        else:
            return original_decode(
                token,
                key,
                options={"verify_signature": False},
                **kwargs
            )
    except (InvalidTokenError, PyJWTError) as e:
        # Handle both old and new exception types
        raise Exception(f"JWT verification failed: {str(e)}")

# Apply the monkey patch to allauth's jwtkit module
def apply_jwt_patch():
    """Apply the JWT patch to django-allauth"""
    try:
        from allauth.socialaccount.internal import jwtkit
        # Replace the verify_and_decode function with our patched version
        jwtkit.verify_and_decode = patched_verify_and_decode
        print("Successfully applied JWT patch to django-allauth")
    except ImportError:
        print("Could not apply JWT patch: allauth.socialaccount.internal.jwtkit not found")
