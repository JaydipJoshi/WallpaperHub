# Fixing Google OAuth JWT Error in WallpaperHub

This document explains how to fix the JWT error that occurs when trying to sign in with Google in WallpaperHub.

## The Error

```
AttributeError: module 'jwt' has no attribute 'PyJWTError'
```

This error occurs because of a version mismatch between the PyJWT library and what django-allauth expects.

## Solution

We've implemented several fixes to resolve this issue:

### 1. Install the correct version of PyJWT

```bash
pip install PyJWT==1.7.1
```

This installs a version of PyJWT that is compatible with django-allauth.

### 2. Apply a patch to django-allauth

We've created a management command that patches the django-allauth library to work with different versions of PyJWT:

```bash
python manage.py patch_allauth_jwt
```

This command modifies the `jwtkit.py` file in django-allauth to handle the PyJWTError correctly.

### 3. Monkey patch at runtime

We've also added a monkey patch that is applied when the app starts:

- Created `accounts/jwt_patch.py` with a patched version of the JWT verification function
- Updated `accounts/apps.py` to apply the patch when the app starts

## How to Test

1. Make sure you've installed PyJWT 1.7.1:
   ```bash
   pip install PyJWT==1.7.1
   ```

2. Run the patch command:
   ```bash
   python manage.py patch_allauth_jwt
   ```

3. Start the development server:
   ```bash
   python manage.py runserver
   ```

4. Go to the login page and click "Sign in with Google"
   - You should now be able to sign in without the JWT error

## Troubleshooting

If you still encounter issues:

1. Check that the patch was applied successfully:
   ```bash
   python manage.py patch_allauth_jwt
   ```
   You should see "File already patched" or "Successfully patched".

2. Make sure you're using the correct version of PyJWT:
   ```bash
   pip show PyJWT
   ```
   The version should be 1.7.1.

3. Clear your browser cookies and cache before testing again.

4. If all else fails, you can manually edit the django-allauth library:
   - Open `venv/lib/site-packages/allauth/socialaccount/internal/jwtkit.py`
   - Add this line after the imports:
     ```python
     PyJWTError = getattr(jwt, "PyJWTError", Exception)
     ```
   - Replace all occurrences of `jwt.PyJWTError` with `PyJWTError`
