from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
from .mongodb_utils import get_user_by_id
import bson

def get_user(request):
    """
    Get the user from the session
    """
    user_id = request.session.get('user_id')

    if not user_id:
        return AnonymousUser()

    try:
        # Convert string to ObjectId if needed
        if isinstance(user_id, str):
            user_id = bson.ObjectId(user_id)

        user = get_user_by_id(user_id)
        if user is not None:
            return user
    except Exception as e:
        print(f"Error getting user: {e}")

    return AnonymousUser()

class MongoDBAuthenticationMiddleware:
    """
    Middleware that adds the user to the request object.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        if not hasattr(request, 'user'):
            request.user = SimpleLazyObject(lambda: get_user(request))

        response = self.get_response(request)

        # Process the response
        return response
