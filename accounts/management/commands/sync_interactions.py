from django.core.management.base import BaseCommand
from accounts.models import WallpaperInteraction, Wallpaper, User
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Sync wallpaper interactions between MongoDB and Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--direction',
            type=str,
            default='mongo-to-django',
            help='Sync direction: mongo-to-django or django-to-mongo'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of interactions to sync (default: 30)'
        )

    def handle(self, *args, **options):
        direction = options['direction']
        days = options['days']
        
        # Connect to MongoDB
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            
            # Ensure the interactions collection exists
            if 'wallpaper_interactions' not in db.list_collection_names():
                db.create_collection('wallpaper_interactions')
                
            interactions_collection = db.wallpaper_interactions
            
            self.stdout.write(self.style.SUCCESS('Successfully connected to MongoDB'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to MongoDB: {e}'))
            sys.exit(1)
        
        # Sync from MongoDB to Django
        if direction == 'mongo-to-django':
            self.stdout.write('Syncing interactions from MongoDB to Django...')
            
            # Get interactions from MongoDB
            mongo_interactions = list(interactions_collection.find())
            self.stdout.write(f'Found {len(mongo_interactions)} interactions in MongoDB')
            
            # Sync each interaction to Django
            synced_count = 0
            for mongo_interaction in mongo_interactions:
                try:
                    # Get the user
                    try:
                        user = User.objects.get(id=mongo_interaction.get('user_id'))
                    except User.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'User with ID {mongo_interaction.get("user_id")} not found, skipping interaction'))
                        continue
                    
                    # Get the wallpaper
                    wallpaper = None
                    wallpaper_id = mongo_interaction.get('wallpaper_id')
                    wallpaper_mongo_id = mongo_interaction.get('wallpaper_mongo_id')
                    
                    if wallpaper_id:
                        try:
                            wallpaper = Wallpaper.objects.get(id=wallpaper_id)
                        except Wallpaper.DoesNotExist:
                            pass
                    
                    if not wallpaper and wallpaper_mongo_id:
                        try:
                            wallpaper = Wallpaper.objects.get(mongo_id=wallpaper_mongo_id)
                        except Wallpaper.DoesNotExist:
                            pass
                    
                    if not wallpaper:
                        self.stdout.write(self.style.WARNING(f'Wallpaper not found for interaction {mongo_interaction.get("_id")}, skipping'))
                        continue
                    
                    # Check if we already have this interaction in Django
                    mongo_id = str(mongo_interaction.get('_id'))
                    try:
                        interaction = WallpaperInteraction.objects.get(mongo_id=mongo_id)
                        # Update existing interaction
                        interaction.interaction_type = mongo_interaction.get('interaction_type', 'view')
                        interaction.timestamp = mongo_interaction.get('timestamp', timezone.now())
                        interaction.ip_address = mongo_interaction.get('ip_address')
                        interaction.user_agent = mongo_interaction.get('user_agent', '')
                        interaction.device_type = mongo_interaction.get('device_type', '')
                        interaction.session_id = mongo_interaction.get('session_id', '')
                        interaction.share_platform = mongo_interaction.get('share_platform', '')
                        interaction.referrer = mongo_interaction.get('referrer', '')
                        interaction.duration = mongo_interaction.get('duration', 0)
                    except WallpaperInteraction.DoesNotExist:
                        # Create new interaction
                        interaction = WallpaperInteraction(
                            user=user,
                            wallpaper=wallpaper,
                            interaction_type=mongo_interaction.get('interaction_type', 'view'),
                            timestamp=mongo_interaction.get('timestamp', timezone.now()),
                            ip_address=mongo_interaction.get('ip_address'),
                            user_agent=mongo_interaction.get('user_agent', ''),
                            device_type=mongo_interaction.get('device_type', ''),
                            session_id=mongo_interaction.get('session_id', ''),
                            share_platform=mongo_interaction.get('share_platform', ''),
                            referrer=mongo_interaction.get('referrer', ''),
                            duration=mongo_interaction.get('duration', 0),
                            mongo_id=mongo_id
                        )
                    
                    # Set _syncing flag to prevent infinite loop with signal handlers
                    interaction._syncing = True
                    interaction.save()
                    
                    synced_count += 1
                    if synced_count % 100 == 0:
                        self.stdout.write(f'Synced {synced_count} interactions so far...')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing interaction: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} interactions from MongoDB to Django'))
        
        # Sync from Django to MongoDB
        elif direction == 'django-to-mongo':
            self.stdout.write('Syncing interactions from Django to MongoDB...')
            
            # Get interactions from Django
            from django.utils import timezone
            from datetime import timedelta
            
            # Get interactions from the last X days
            cutoff_date = timezone.now() - timedelta(days=days)
            django_interactions = WallpaperInteraction.objects.filter(timestamp__gte=cutoff_date)
            
            self.stdout.write(f'Found {django_interactions.count()} interactions in Django from the last {days} days')
            
            # Sync each interaction to MongoDB
            synced_count = 0
            for django_interaction in django_interactions:
                try:
                    django_interaction.sync_to_mongodb()
                    synced_count += 1
                    if synced_count % 100 == 0:
                        self.stdout.write(f'Synced {synced_count} interactions so far...')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing interaction: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {synced_count} interactions from Django to MongoDB'))
        else:
            self.stdout.write(self.style.ERROR(f'Invalid direction: {direction}. Use mongo-to-django or django-to-mongo'))
