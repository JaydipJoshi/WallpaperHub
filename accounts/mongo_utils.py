import pymongo
from pymongo import MongoClient
import datetime

# MongoDB connection
def get_db_connection():
    """
    Get a connection to the MongoDB database
    """
    try:
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.server_info()

        # Database will be created automatically if it doesn't exist
        db = client['wallpaperhub_db']

        # Ensure the users collection exists
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
            print("Created users collection in wallpaperhub_db")

        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def get_users_collection():
    """
    Get the users collection from MongoDB
    """
    db = get_db_connection()
    if db is None:
        return None
    return db.users

def save_user_to_mongo(user):
    """
    Save Django user data to MongoDB
    """
    users = get_users_collection()
    if users is None:
        return None

    # Check if user already exists in MongoDB
    existing_user = users.find_one({'django_id': user.id})
    if existing_user:
        # Update existing user
        users.update_one(
            {'django_id': user.id},
            {'$set': {
                'username': user.username,
                'email': user.email,
                'last_login': datetime.datetime.now()
            }}
        )
        return existing_user['_id']
    else:
        # Create new user
        user_data = {
            'django_id': user.id,
            'username': user.username,
            'email': user.email,
            'date_joined': datetime.datetime.now(),
            'last_login': datetime.datetime.now(),
            'preferences': {},  # You can store additional user data here
            'favorites': []     # Example of additional data
        }
        result = users.insert_one(user_data)
        return result.inserted_id

def get_mongo_user(django_id):
    """
    Get user data from MongoDB by Django user ID
    """
    users = get_users_collection()
    if users is None:
        return None

    return users.find_one({'django_id': django_id})

def add_favorite(django_id, wallpaper_id):
    """
    Add a wallpaper to user's favorites
    """
    users = get_users_collection()
    if users is None:
        return False

    result = users.update_one(
        {'django_id': django_id},
        {'$addToSet': {'favorites': wallpaper_id}}
    )

    return result.modified_count > 0

def remove_favorite(django_id, wallpaper_id):
    """
    Remove a wallpaper from user's favorites
    """
    users = get_users_collection()
    if users is None:
        return False

    result = users.update_one(
        {'django_id': django_id},
        {'$pull': {'favorites': wallpaper_id}}
    )

    return result.modified_count > 0

def get_favorites(django_id):
    """
    Get user's favorite wallpapers
    """
    users = get_users_collection()
    if not users:
        return []

    user = users.find_one({'django_id': django_id})
    if user and 'favorites' in user:
        return user['favorites']

    return []
