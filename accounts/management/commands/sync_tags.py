from django.core.management.base import BaseCommand
from accounts.models import Tag, Wallpaper
from pymongo import MongoClient
import sys
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Sync tags between MongoDB and Django, and migrate from legacy tags to the new Tag model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--direction',
            type=str,
            default='both',
            help='Sync direction: mongo-to-django, django-to-mongo, or both'
        )
        parser.add_argument(
            '--migrate-legacy',
            action='store_true',
            help='Migrate legacy tags (stored as comma-separated strings) to the new Tag model'
        )

    def handle(self, *args, **options):
        direction = options['direction']
        migrate_legacy = options['migrate_legacy']
        
        # Connect to MongoDB
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            
            # Ensure the tags collection exists
            if 'tags' not in db.list_collection_names():
                db.create_collection('tags')
                
            tags_collection = db.tags
            
            self.stdout.write(self.style.SUCCESS('Successfully connected to MongoDB'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to MongoDB: {e}'))
            sys.exit(1)
        
        # Migrate legacy tags to the new Tag model
        if migrate_legacy:
            self.stdout.write('Migrating legacy tags to the new Tag model...')
            
            # Get all wallpapers with legacy tags
            wallpapers = Wallpaper.objects.exclude(tags_string='')
            self.stdout.write(f'Found {wallpapers.count()} wallpapers with legacy tags')
            
            # Process each wallpaper
            processed_count = 0
            for wallpaper in wallpapers:
                if not wallpaper.tags_string:
                    continue
                    
                # Get tag names from the legacy field
                tag_names = [tag.strip() for tag in wallpaper.tags_string.split(',') if tag.strip()]
                
                # Process each tag
                for tag_name in tag_names:
                    # Try to find existing tag or create a new one
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={'slug': slugify(tag_name)}
                    )
                    
                    # Add tag to wallpaper if not already added
                    if tag not in wallpaper.tags.all():
                        wallpaper.tags.add(tag)
                        
                # Update wallpaper
                processed_count += 1
                if processed_count % 100 == 0:
                    self.stdout.write(f'Processed {processed_count} wallpapers so far...')
            
            # Update usage counts for all tags
            for tag in Tag.objects.all():
                tag.update_usage_count()
                
            self.stdout.write(self.style.SUCCESS(f'Successfully migrated tags for {processed_count} wallpapers'))
        
        # Sync from MongoDB to Django
        if direction in ['mongo-to-django', 'both']:
            self.stdout.write('Syncing tags from MongoDB to Django...')
            
            # Get all tags from MongoDB
            mongo_tags = list(tags_collection.find())
            self.stdout.write(f'Found {len(mongo_tags)} tags in MongoDB')
            
            # Sync each tag to Django
            synced_count = 0
            for mongo_tag in mongo_tags:
                try:
                    Tag.sync_from_mongodb(mongo_tag)
                    synced_count += 1
                    if synced_count % 100 == 0:
                        self.stdout.write(f'Synced {synced_count} tags so far...')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing tag: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} tags from MongoDB to Django'))
        
        # Sync from Django to MongoDB
        if direction in ['django-to-mongo', 'both']:
            self.stdout.write('Syncing tags from Django to MongoDB...')
            
            # Get all tags from Django
            django_tags = Tag.objects.all()
            self.stdout.write(f'Found {django_tags.count()} tags in Django')
            
            # Sync each tag to MongoDB
            synced_count = 0
            for django_tag in django_tags:
                try:
                    django_tag.sync_to_mongodb()
                    synced_count += 1
                    if synced_count % 100 == 0:
                        self.stdout.write(f'Synced {synced_count} tags so far...')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing tag: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} tags from Django to MongoDB'))
