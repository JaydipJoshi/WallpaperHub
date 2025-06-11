from django.shortcuts import redirect
from functools import wraps

def mongo_login_required(login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect(login_url or '/login/')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
