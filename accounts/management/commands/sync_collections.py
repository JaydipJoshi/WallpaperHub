from django.core.management.base import BaseCommand
from accounts.models import Collection, User
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Sync collections between MongoDB and Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--direction',
            type=str,
            default='both',
            help='Sync direction: mongo-to-django, django-to-mongo, or both'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Sync collections for a specific user (username or email)'
        )

    def handle(self, *args, **options):
        direction = options['direction']
        user_filter = options['user']
        
        # Connect to MongoDB
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            
            # Ensure the collections collection exists
            if 'collections' not in db.list_collection_names():
                db.create_collection('collections')
                
            collections_collection = db.collections
            
            self.stdout.write(self.style.SUCCESS('Successfully connected to MongoDB'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to MongoDB: {e}'))
            sys.exit(1)
        
        # Get user if specified
        user = None
        if user_filter:
            try:
                # Try to find by username
                user = User.objects.get(username=user_filter)
            except User.DoesNotExist:
                try:
                    # Try to find by email
                    user = User.objects.get(email=user_filter)
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'User not found: {user_filter}'))
                    sys.exit(1)
            
            self.stdout.write(f'Syncing collections for user: {user.username} ({user.email})')
        
        # Sync from MongoDB to Django
        if direction in ['mongo-to-django', 'both']:
            self.stdout.write('Syncing from MongoDB to Django...')
            
            # Get collections from MongoDB
            mongo_query = {}
            if user:
                mongo_query['owner_id'] = user.id
                
            mongo_collections = list(collections_collection.find(mongo_query))
            self.stdout.write(f'Found {len(mongo_collections)} collections in MongoDB')
            
            # Sync each collection to Django
            synced_count = 0
            for mongo_collection in mongo_collections:
                try:
                    Collection.sync_from_mongodb(mongo_collection, owner=user)
                    synced_count += 1
                    self.stdout.write(f'Synced collection: {mongo_collection.get("name", "Untitled")}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing collection: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} collections from MongoDB to Django'))
        
        # Sync from Django to MongoDB
        if direction in ['django-to-mongo', 'both']:
            self.stdout.write('Syncing from Django to MongoDB...')
            
            # Get collections from Django
            django_query = {}
            if user:
                django_query['owner'] = user
                
            django_collections = Collection.objects.filter(**django_query)
            self.stdout.write(f'Found {django_collections.count()} collections in Django')
            
            # Sync each collection to MongoDB
            synced_count = 0
            for django_collection in django_collections:
                try:
                    django_collection.sync_to_mongodb()
                    synced_count += 1
                    self.stdout.write(f'Synced collection: {django_collection.name}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing collection: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} collections from Django to MongoDB'))
