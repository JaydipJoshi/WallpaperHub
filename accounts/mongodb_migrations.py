import pymongo
from pymongo import MongoClient
import datetime
import os
import json
import sys

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
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def create_migration_collection():
    """
    Create a collection to track migrations
    """
    db = get_db_connection()
    if db is None:
        print("Failed to connect to MongoDB")
        return False

    if 'migrations' not in db.list_collection_names():
        db.create_collection('migrations')
        print("Created migrations collection")

    return True

def get_applied_migrations():
    """
    Get a list of migrations that have already been applied
    """
    db = get_db_connection()
    if db is None:
        return []

    migrations = db.migrations.find({}, {'name': 1, '_id': 0})
    return [m['name'] for m in migrations]

def apply_migration(migration_name, migration_function):
    """
    Apply a migration and record it in the migrations collection
    """
    db = get_db_connection()
    if db is None:
        print(f"Failed to apply migration {migration_name}")
        return False

    # Check if migration has already been applied
    if db.migrations.find_one({'name': migration_name}):
        print(f"Migration {migration_name} already applied")
        return True

    # Apply the migration
    try:
        migration_function(db)

        # Record the migration
        db.migrations.insert_one({
            'name': migration_name,
            'applied_at': datetime.datetime.now()
        })

        print(f"Successfully applied migration: {migration_name}")
        return True
    except Exception as e:
        print(f"Error applying migration {migration_name}: {e}")
        return False

# Define migrations
def migration_001_create_users_collection(db):
    """
    Create the users collection and add indexes
    """
    if 'users' not in db.list_collection_names():
        db.create_collection('users')

    # Create indexes
    db.users.create_index('django_id', unique=True)
    db.users.create_index('email')

def migration_002_add_preferences_field(db):
    """
    Add preferences field to existing users
    """
    db.users.update_many(
        {'preferences': {'$exists': False}},
        {'$set': {'preferences': {}}}
    )

def migration_003_add_favorites_field(db):
    """
    Add favorites field to existing users
    """
    db.users.update_many(
        {'favorites': {'$exists': False}},
        {'$set': {'favorites': []}}
    )

def migration_004_add_settings_fields(db):
    """
    Add settings fields to existing users
    """
    default_settings = {
        'settings': {
            'appearance': {
                'theme': 'light',
                'accent_color': '#65558F',
                'layout_density': 'medium'
            },
            'privacy': {
                'show_email': True,
                'show_activity': True,
                'allow_data_collection': True
            },
            'notifications': {
                'email_notifications': True,  # Enabled by default
                'site_notifications': True
            },
            'connected_accounts': {
                'google': False
            }
        },
        'analytics': {
            'time_spent': {
                'total_minutes': 0,
                'weekly_data': [0, 0, 0, 0, 0, 0, 0]  # Sun, Mon, Tue, Wed, Thu, Fri, Sat
            },
            'categories': {
                'abstract': 0,
                'nature': 0,
                'city': 0,
                'space': 0,
                'minimal': 0,
                'neon': 0,
                'landscape': 0,
                'sunset': 0,
                'other': 0
            },
            'downloads': {
                'total': 0,
                'monthly_data': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Jan to Dec
            }
        },
        'sessions': []
    }

    # Add settings to users that don't have them
    db.users.update_many(
        {'settings': {'$exists': False}},
        {'$set': default_settings}
    )

def migration_005_enable_email_notifications(db):
    """
    Enable email notifications for all users
    """
    # Update all users to enable email notifications
    db.users.update_many(
        {},
        {'$set': {'settings.notifications.email_notifications': True}}
    )

    # Also update the UserSettings collection if it exists
    if 'user_settings' in db.list_collection_names():
        db.user_settings.update_many(
            {},
            {'$set': {'email_notifications': True}}
        )

# List of all migrations
MIGRATIONS = [
    ('001_create_users_collection', migration_001_create_users_collection),
    ('002_add_preferences_field', migration_002_add_preferences_field),
    ('003_add_favorites_field', migration_003_add_favorites_field),
    ('004_add_settings_fields', migration_004_add_settings_fields),
    ('005_enable_email_notifications', migration_005_enable_email_notifications),
]

def run_migrations():
    """
    Run all pending migrations
    """
    # Create migrations collection if it doesn't exist
    if not create_migration_collection():
        return False

    # Get applied migrations
    applied = get_applied_migrations()

    # Apply pending migrations
    for name, func in MIGRATIONS:
        if name not in applied:
            apply_migration(name, func)

    return True

if __name__ == "__main__":
    run_migrations()
