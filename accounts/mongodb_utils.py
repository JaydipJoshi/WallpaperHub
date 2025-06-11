import pymongo
from pymongo import MongoClient
import datetime
import hashlib
import os

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

def hash_password(password):
    """
    Hash a password for storing
    """
    salt = os.urandom(32)  # A new salt for this user
    key = hashlib.pbkdf2_hmac(
        'sha256',  # The hash digest algorithm for HMAC
        password.encode('utf-8'),  # Convert the password to bytes
        salt,  # Provide the salt
        100000  # It is recommended to use at least 100,000 iterations of SHA-256
    )
    # Store the salt with the password
    return {
        'salt': salt,
        'key': key
    }

def verify_password(stored_password, provided_password):
    """
    Verify a stored password against one provided by user
    """
    salt = stored_password['salt']
    stored_key = stored_password['key']

    # Use the same hash function to check the provided password
    key = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode('utf-8'),
        salt,
        100000
    )

    # Compare the keys
    return key == stored_key

def create_user(email, password, **extra_fields):
    """
    Create a new user in MongoDB
    """
    users = get_users_collection()
    if users is None:
        return None

    # Check if user already exists
    if users.find_one({'email': email}):
        return None

    # Hash the password
    password_hash = hash_password(password)

    # Create user document
    user = {
        'email': email,
        'password': {
            'salt': password_hash['salt'],
            'key': password_hash['key']
        },
        'is_active': True,
        'date_joined': datetime.datetime.now(),
        **extra_fields
    }

    # Insert the user
    result = users.insert_one(user)

    # Return the user with the MongoDB _id
    user['_id'] = result.inserted_id
    return user

def authenticate_user(email, password):
    """
    Authenticate a user with email and password
    """
    users = get_users_collection()
    if users is None:
        return None

    user = users.find_one({'email': email})

    if not user:
        return None

    if verify_password(user['password'], password):
        return user

    return None

def get_user_by_id(user_id):
    """
    Get a user by MongoDB _id
    """
    users = get_users_collection()
    if users is None:
        return None
    return users.find_one({'_id': user_id})

def get_user_by_email(email):
    """
    Get a user by email
    """
    users = get_users_collection()
    if users is None:
        return None
    return users.find_one({'email': email})
