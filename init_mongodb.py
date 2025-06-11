import pymongo
from pymongo import MongoClient
import datetime

def initialize_mongodb():
    """
    Initialize MongoDB database and collections for WallpaperHub
    """
    try:
        # Connect to MongoDB
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        
        # Test the connection
        client.server_info()
        print("Successfully connected to MongoDB")
        
        # Create or get the database
        db = client['wallpaperhub_db']
        print("Created/accessed database: wallpaperhub_db")
        
        # Create users collection if it doesn't exist
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
            print("Created users collection")
        else:
            print("Users collection already exists")
        
        # Create an index on django_id for faster lookups
        db.users.create_index('django_id', unique=True)
        print("Created index on django_id field")
        
        print("MongoDB initialization complete!")
        return True
    except Exception as e:
        print(f"Error initializing MongoDB: {e}")
        return False

if __name__ == "__main__":
    initialize_mongodb()
