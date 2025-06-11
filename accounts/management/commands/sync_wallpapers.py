from django.core.management.base import BaseCommand
from accounts.models import Wallpaper
from pymongo import MongoClient
import sys

class Command(BaseCommand):
    help = 'Sync wallpapers between MongoDB and Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--direction',
            type=str,
            default='both',
            help='Sync direction: mongo-to-django, django-to-mongo, or both'
        )

    def handle(self, *args, **options):
        direction = options['direction']
        
        # Connect to MongoDB
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            wallpapers_collection = db.wallpapers
            
            self.stdout.write(self.style.SUCCESS('Successfully connected to MongoDB'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to MongoDB: {e}'))
            sys.exit(1)
        
        # Sync from MongoDB to Django
        if direction in ['mongo-to-django', 'both']:
            self.stdout.write('Syncing from MongoDB to Django...')
            
            # Get all wallpapers from MongoDB
            mongo_wallpapers = list(wallpapers_collection.find())
            self.stdout.write(f'Found {len(mongo_wallpapers)} wallpapers in MongoDB')
            
            # Sync each wallpaper to Django
            synced_count = 0
            for mongo_wallpaper in mongo_wallpapers:
                try:
                    Wallpaper.sync_from_mongodb(mongo_wallpaper)
                    synced_count += 1
                    self.stdout.write(f'Synced wallpaper: {mongo_wallpaper.get("title", "Untitled")}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing wallpaper: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} wallpapers from MongoDB to Django'))
        
        # Sync from Django to MongoDB
        if direction in ['django-to-mongo', 'both']:
            self.stdout.write('Syncing from Django to MongoDB...')
            
            # Get all wallpapers from Django
            django_wallpapers = Wallpaper.objects.all()
            self.stdout.write(f'Found {django_wallpapers.count()} wallpapers in Django')
            
            # Sync each wallpaper to MongoDB
            synced_count = 0
            for django_wallpaper in django_wallpapers:
                try:
                    django_wallpaper.sync_to_mongodb()
                    synced_count += 1
                    self.stdout.write(f'Synced wallpaper: {django_wallpaper.title}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing wallpaper: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} wallpapers from Django to MongoDB'))
