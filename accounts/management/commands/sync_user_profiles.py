from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models_user_extensions import UserSettings, UserPreferences, UserStatistics
from pymongo import MongoClient
import sys

class Command(BaseCommand):
    help = 'Sync user profile extensions between MongoDB and Django'

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
            help='Sync a specific user (username or email)'
        )
        parser.add_argument(
            '--model',
            type=str,
            choices=['settings', 'preferences', 'statistics', 'all'],
            default='all',
            help='Sync a specific model or all models'
        )

    def handle(self, *args, **options):
        direction = options['direction']
        user_filter = options['user']
        model_filter = options['model']
        
        # Connect to MongoDB
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            
            # Ensure collections exist
            if 'user_settings' not in db.list_collection_names():
                db.create_collection('user_settings')
            if 'user_preferences' not in db.list_collection_names():
                db.create_collection('user_preferences')
            if 'user_statistics' not in db.list_collection_names():
                db.create_collection('user_statistics')
                
            settings_collection = db.user_settings
            preferences_collection = db.user_preferences
            statistics_collection = db.user_statistics
            
            self.stdout.write(self.style.SUCCESS('Successfully connected to MongoDB'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to MongoDB: {e}'))
            sys.exit(1)
        
        # Get users to sync
        users = []
        if user_filter:
            # Try to find by username
            try:
                user = User.objects.get(username=user_filter)
                users = [user]
                self.stdout.write(f'Found user by username: {user.username}')
            except User.DoesNotExist:
                # Try to find by email
                try:
                    user = User.objects.get(email=user_filter)
                    users = [user]
                    self.stdout.write(f'Found user by email: {user.email}')
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'User not found: {user_filter}'))
                    sys.exit(1)
        else:
            # Get all users
            users = User.objects.all()
            self.stdout.write(f'Found {users.count()} users')
        
        # Sync from MongoDB to Django
        if direction in ['mongo-to-django', 'both']:
            self.stdout.write('Syncing from MongoDB to Django...')
            
            for user in users:
                self.stdout.write(f'Processing user: {user.username}')
                
                # Sync UserSettings
                if model_filter in ['settings', 'all']:
                    mongo_settings = settings_collection.find_one({'user_id': user.id})
                    if mongo_settings:
                        try:
                            settings, created = UserSettings.objects.get_or_create(user=user)
                            
                            # Update fields from MongoDB
                            settings.theme = mongo_settings.get('theme', 'system')
                            settings.accent_color = mongo_settings.get('accent_color', '#65558F')
                            settings.layout_density = mongo_settings.get('layout_density', 'medium')
                            settings.show_email = mongo_settings.get('show_email', True)
                            settings.show_activity = mongo_settings.get('show_activity', True)
                            settings.allow_data_collection = mongo_settings.get('allow_data_collection', True)
                            settings.email_notifications = mongo_settings.get('email_notifications', True)
                            settings.site_notifications = mongo_settings.get('site_notifications', True)
                            settings.connected_google = mongo_settings.get('connected_google', False)
                            
                            # Set MongoDB ID
                            settings.mongo_id = str(mongo_settings.get('_id'))
                            
                            # Save with _syncing flag to prevent infinite loop
                            settings._syncing = True
                            settings.save()
                            settings._syncing = False
                            
                            self.stdout.write(self.style.SUCCESS(f'  Synced settings for {user.username}'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  Error syncing settings for {user.username}: {e}'))
                
                # Sync UserPreferences
                if model_filter in ['preferences', 'all']:
                    mongo_preferences = preferences_collection.find_one({'user_id': user.id})
                    if mongo_preferences:
                        try:
                            preferences, created = UserPreferences.objects.get_or_create(user=user)
                            
                            # Update fields from MongoDB
                            preferences.preferred_categories = mongo_preferences.get('preferred_categories', [])
                            preferences.preferred_tags = mongo_preferences.get('preferred_tags', [])
                            preferences.preferred_aspect_ratio = mongo_preferences.get('preferred_aspect_ratio', 'any')
                            preferences.preferred_colors = mongo_preferences.get('preferred_colors', [])
                            preferences.show_nsfw_content = mongo_preferences.get('show_nsfw_content', False)
                            preferences.hide_viewed_wallpapers = mongo_preferences.get('hide_viewed_wallpapers', False)
                            preferences.hide_downloaded_wallpapers = mongo_preferences.get('hide_downloaded_wallpapers', False)
                            preferences.show_trending = mongo_preferences.get('show_trending', True)
                            preferences.show_featured = mongo_preferences.get('show_featured', True)
                            preferences.show_new = mongo_preferences.get('show_new', True)
                            preferences.show_recommendations = mongo_preferences.get('show_recommendations', True)
                            preferences.default_download_quality = mongo_preferences.get('default_download_quality', 'high')
                            preferences.auto_resize_to_screen = mongo_preferences.get('auto_resize_to_screen', True)
                            
                            # Set MongoDB ID
                            preferences.mongo_id = str(mongo_preferences.get('_id'))
                            
                            # Save with _syncing flag to prevent infinite loop
                            preferences._syncing = True
                            preferences.save()
                            preferences._syncing = False
                            
                            self.stdout.write(self.style.SUCCESS(f'  Synced preferences for {user.username}'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  Error syncing preferences for {user.username}: {e}'))
                
                # Sync UserStatistics
                if model_filter in ['statistics', 'all']:
                    mongo_statistics = statistics_collection.find_one({'user_id': user.id})
                    if mongo_statistics:
                        try:
                            statistics, created = UserStatistics.objects.get_or_create(user=user)
                            
                            # Update fields from MongoDB
                            statistics.total_views = mongo_statistics.get('total_views', 0)
                            statistics.total_downloads = mongo_statistics.get('total_downloads', 0)
                            statistics.total_likes = mongo_statistics.get('total_likes', 0)
                            statistics.total_shares = mongo_statistics.get('total_shares', 0)
                            statistics.total_saves = mongo_statistics.get('total_saves', 0)
                            statistics.total_uploads = mongo_statistics.get('total_uploads', 0)
                            statistics.total_collections = mongo_statistics.get('total_collections', 0)
                            statistics.total_comments = mongo_statistics.get('total_comments', 0)
                            statistics.total_time_spent = mongo_statistics.get('total_time_spent', 0)
                            statistics.category_interactions = mongo_statistics.get('category_interactions', {})
                            statistics.tag_interactions = mongo_statistics.get('tag_interactions', {})
                            statistics.daily_activity = mongo_statistics.get('daily_activity', {})
                            statistics.weekly_activity = mongo_statistics.get('weekly_activity', {})
                            statistics.monthly_activity = mongo_statistics.get('monthly_activity', {})
                            statistics.device_usage = mongo_statistics.get('device_usage', {})
                            
                            # Set MongoDB ID
                            statistics.mongo_id = str(mongo_statistics.get('_id'))
                            
                            # Save with _syncing flag to prevent infinite loop
                            statistics._syncing = True
                            statistics.save()
                            statistics._syncing = False
                            
                            self.stdout.write(self.style.SUCCESS(f'  Synced statistics for {user.username}'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  Error syncing statistics for {user.username}: {e}'))
        
        # Sync from Django to MongoDB
        if direction in ['django-to-mongo', 'both']:
            self.stdout.write('Syncing from Django to MongoDB...')
            
            for user in users:
                self.stdout.write(f'Processing user: {user.username}')
                
                # Sync UserSettings
                if model_filter in ['settings', 'all']:
                    try:
                        settings, created = UserSettings.objects.get_or_create(user=user)
                        settings.sync_to_mongodb()
                        self.stdout.write(self.style.SUCCESS(f'  Synced settings for {user.username}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Error syncing settings for {user.username}: {e}'))
                
                # Sync UserPreferences
                if model_filter in ['preferences', 'all']:
                    try:
                        preferences, created = UserPreferences.objects.get_or_create(user=user)
                        preferences.sync_to_mongodb()
                        self.stdout.write(self.style.SUCCESS(f'  Synced preferences for {user.username}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Error syncing preferences for {user.username}: {e}'))
                
                # Sync UserStatistics
                if model_filter in ['statistics', 'all']:
                    try:
                        statistics, created = UserStatistics.objects.get_or_create(user=user)
                        statistics.sync_to_mongodb()
                        self.stdout.write(self.style.SUCCESS(f'  Synced statistics for {user.username}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Error syncing statistics for {user.username}: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Sync completed successfully'))
