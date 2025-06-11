"""
Direct patch for django-allauth JWT verification
"""

import os
import re

def apply_direct_patch():
    """
    Directly modify the django-allauth jwtkit.py file to fix JWT verification
    """
    try:
        # Find the allauth jwtkit.py file
        import allauth
        allauth_path = os.path.dirname(allauth.__file__)
        jwtkit_path = os.path.join(allauth_path, 'socialaccount', 'internal', 'jwtkit.py')
        
        if not os.path.exists(jwtkit_path):
            print(f"Could not find jwtkit.py at {jwtkit_path}")
            return False
        
        # Read the file
        with open(jwtkit_path, 'r') as f:
            content = f.read()
        
        # Check if the file already contains our patch
        if 'import jwt\n\n# Fix for PyJWT compatibility' in content:
            print("File already patched")
            return True
        
        # Create a backup
        backup_path = jwtkit_path + '.bak'
        with open(backup_path, 'w') as f:
            f.write(content)
        
        # Apply the patch
        new_content = """import jwt

# Fix for PyJWT compatibility
try:
    from jwt.exceptions import PyJWTError
except ImportError:
    # For older versions of PyJWT
    class PyJWTError(Exception):
        pass
    jwt.PyJWTError = PyJWTError

import json
import time
from datetime import datetime

from django.core.exceptions import ImproperlyConfigured


def get_unverified_claims(token):
    \"\"\"
    Returns the claims of the given JWT without verifying the signature.
    Note: Do *not* use the result of this function for authentication purposes.
    \"\"\"
    idx = token.rfind(".")
    if idx < 0:
        raise jwt.PyJWTError("Token has no signature")
    signing_input = token[:idx]
    try:
        header_segment, payload_segment = signing_input.split(".", 1)
    except ValueError:
        raise jwt.PyJWTError("Token has an invalid format")
    try:
        payload = jwt.utils.base64url_decode(payload_segment)
    except (TypeError, ValueError):
        raise jwt.PyJWTError("Invalid payload padding")
    try:
        claims = json.loads(payload)
    except ValueError:
        raise jwt.PyJWTError("Invalid payload")
    return claims


def get_jwk_key(jwks, kid):
    keys = jwks.get("keys", [])
    for key in keys:
        if key.get("kid") == kid:
            return key
    raise ImproperlyConfigured("Could not find key with kid=%s" % kid)


def validate_exp(claims, current_time=None):
    \"\"\"
    Validates that the 'exp' claim is a positive number in the future.

    Args:
        claims: dict -- The JWT claims
        current_time: int -- Time in seconds since the epoch, defaults to now

    Raises:
        PyJWTError: If the 'exp' claim is invalid
    \"\"\"
    if current_time is None:
        current_time = int(time.time())

    exp = claims.get("exp")
    if exp is None:
        return

    if not isinstance(exp, (int, float)):
        raise jwt.PyJWTError("exp must be an integer or float")
    if exp < current_time:
        raise jwt.PyJWTError("Token expired")


def verify_and_decode(token, key, verify_signature=True, **kwargs):
    \"\"\"
    Verifies a JWT and returns the decoded body (claims).

    Args:
        token: string -- The encoded JWT
        key: string -- The signing key
        verify_signature: bool -- Whether to verify the signature
        **kwargs: dict -- Additional arguments to pass to jwt.decode

    Returns:
        dict -- The decoded JWT claims

    Raises:
        PyJWTError: If the token is invalid
    \"\"\"
    try:
        # For PyJWT >= 2.0.0
        data = jwt.decode(
            token,
            key,
            options={"verify_signature": verify_signature},
            algorithms=["RS256", "HS256"],
            **kwargs,
        )
    except (AttributeError, TypeError):
        try:
            # For PyJWT < 2.0.0
            if verify_signature:
                data = jwt.decode(token, key, algorithms=["RS256", "HS256"], **kwargs)
            else:
                data = jwt.decode(token, verify=False, **kwargs)
        except Exception as e:
            raise jwt.PyJWTError(str(e))
    return data
"""
        
        # Write the patched file
        with open(jwtkit_path, 'w') as f:
            f.write(new_content)
        
        print(f"Successfully patched {jwtkit_path}")
        return True
        
    except Exception as e:
        print(f"Error patching allauth: {str(e)}")
        return False
