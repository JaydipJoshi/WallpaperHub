from django.core.management.base import BaseCommand
from accounts.models import Comment, Wallpaper, User
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Sync comments between MongoDB and Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--direction',
            type=str,
            default='both',
            help='Sync direction: mongo-to-django, django-to-mongo, or both'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of comments to sync (default: 30)'
        )
        parser.add_argument(
            '--wallpaper',
            type=str,
            help='Sync comments for a specific wallpaper (ID)'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Sync comments by a specific user (username or email)'
        )

    def handle(self, *args, **options):
        direction = options['direction']
        days = options['days']
        wallpaper_filter = options['wallpaper']
        user_filter = options['user']
        
        # Connect to MongoDB
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            
            # Ensure the comments collection exists
            if 'comments' not in db.list_collection_names():
                db.create_collection('comments')
                
            comments_collection = db.comments
            
            self.stdout.write(self.style.SUCCESS('Successfully connected to MongoDB'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to MongoDB: {e}'))
            sys.exit(1)
        
        # Get filters for wallpaper and user
        wallpaper = None
        if wallpaper_filter:
            try:
                wallpaper = Wallpaper.objects.get(id=wallpaper_filter)
                self.stdout.write(f'Filtering by wallpaper: {wallpaper.title}')
            except Wallpaper.DoesNotExist:
                try:
                    wallpaper = Wallpaper.objects.get(mongo_id=wallpaper_filter)
                    self.stdout.write(f'Filtering by wallpaper: {wallpaper.title}')
                except Wallpaper.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Wallpaper not found: {wallpaper_filter}'))
                    sys.exit(1)
        
        user = None
        if user_filter:
            try:
                user = User.objects.get(username=user_filter)
                self.stdout.write(f'Filtering by user: {user.username}')
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=user_filter)
                    self.stdout.write(f'Filtering by user: {user.username}')
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'User not found: {user_filter}'))
                    sys.exit(1)
        
        # Sync from MongoDB to Django
        if direction in ['mongo-to-django', 'both']:
            self.stdout.write('Syncing from MongoDB to Django...')
            
            # Build MongoDB query
            mongo_query = {}
            if wallpaper:
                mongo_query['wallpaper_id'] = str(wallpaper.id)
            if user:
                mongo_query['author_id'] = user.id
                
            # Get comments from MongoDB
            mongo_comments = list(comments_collection.find(mongo_query))
            self.stdout.write(f'Found {len(mongo_comments)} comments in MongoDB')
            
            # Sync each comment to Django
            synced_count = 0
            for mongo_comment in mongo_comments:
                try:
                    Comment.sync_from_mongodb(mongo_comment)
                    synced_count += 1
                    if synced_count % 100 == 0:
                        self.stdout.write(f'Synced {synced_count} comments so far...')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing comment: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} comments from MongoDB to Django'))
        
        # Sync from Django to MongoDB
        if direction in ['django-to-mongo', 'both']:
            self.stdout.write('Syncing from Django to MongoDB...')
            
            # Build Django query
            django_query = {}
            if wallpaper:
                django_query['wallpaper'] = wallpaper
            if user:
                django_query['author'] = user
                
            # Get comments from the last X days
            cutoff_date = timezone.now() - timedelta(days=days)
            django_comments = Comment.objects.filter(created_at__gte=cutoff_date, **django_query)
            
            self.stdout.write(f'Found {django_comments.count()} comments in Django from the last {days} days')
            
            # Sync each comment to MongoDB
            synced_count = 0
            for django_comment in django_comments:
                try:
                    django_comment.sync_to_mongodb()
                    synced_count += 1
                    if synced_count % 100 == 0:
                        self.stdout.write(f'Synced {synced_count} comments so far...')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing comment: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} comments from Django to MongoDB'))
