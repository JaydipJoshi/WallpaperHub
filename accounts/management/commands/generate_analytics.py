from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Wallpaper, WallpaperInteraction, Collection, Comment
from accounts.models_user_extensions import UserStatistics
import random
from datetime import timedelta
import sys

class Command(BaseCommand):
    help = 'Generate analytics data for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Generate analytics for a specific user (username or email)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of data to generate (default: 30)'
        )
        parser.add_argument(
            '--interactions',
            type=int,
            default=100,
            help='Number of interactions to generate per user (default: 100)'
        )

    def handle(self, *args, **options):
        user_filter = options['user']
        days = options['days']
        interactions_count = options['interactions']
        
        # Get users to generate analytics for
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
        
        # Get wallpapers
        wallpapers = list(Wallpaper.objects.all())
        if not wallpapers:
            self.stdout.write(self.style.ERROR('No wallpapers found in the database'))
            sys.exit(1)
        
        self.stdout.write(f'Found {len(wallpapers)} wallpapers')
        
        # Generate analytics for each user
        for user in users:
            self.stdout.write(f'Generating analytics for user: {user.username}')
            
            # Get or create user statistics
            statistics, created = UserStatistics.objects.get_or_create(user=user)
            
            # Reset statistics
            statistics.total_views = 0
            statistics.total_downloads = 0
            statistics.total_likes = 0
            statistics.total_shares = 0
            statistics.total_saves = 0
            statistics.total_uploads = 0
            statistics.total_collections = 0
            statistics.total_comments = 0
            statistics.total_time_spent = 0
            statistics.category_interactions = {}
            statistics.tag_interactions = {}
            statistics.daily_activity = {}
            statistics.weekly_activity = {}
            statistics.monthly_activity = {}
            statistics.device_usage = {}
            
            # Generate random interactions
            for _ in range(interactions_count):
                # Pick a random wallpaper
                wallpaper = random.choice(wallpapers)
                
                # Pick a random interaction type
                interaction_type = random.choice(['view', 'download', 'like', 'share', 'save'])
                
                # Pick a random date within the specified range
                days_ago = random.randint(0, days)
                interaction_date = timezone.now() - timedelta(days=days_ago)
                
                # Pick a random device type
                device_type = random.choice(['mobile', 'tablet', 'desktop'])
                
                # Pick a random duration (for views)
                duration = random.randint(10, 300) if interaction_type == 'view' else 0
                
                # Get category and tags
                category = wallpaper.category
                tags = [tag.name for tag in wallpaper.tags.all()]
                
                # Record the interaction
                self._record_interaction(
                    statistics=statistics,
                    interaction_type=interaction_type,
                    interaction_date=interaction_date,
                    category=category,
                    tags=tags,
                    device_type=device_type,
                    duration=duration
                )
            
            # Save the statistics
            statistics.save()
            
            # Sync to MongoDB
            statistics.sync_to_mongodb()
            
            self.stdout.write(self.style.SUCCESS(f'Generated {interactions_count} interactions for {user.username}'))
        
        self.stdout.write(self.style.SUCCESS('Analytics generation completed successfully'))
    
    def _record_interaction(self, statistics, interaction_type, interaction_date, category, tags, device_type, duration):
        """Record a user interaction with the specified date"""
        # Update total counts based on interaction type
        if interaction_type == 'view':
            statistics.total_views += 1
        elif interaction_type == 'download':
            statistics.total_downloads += 1
        elif interaction_type == 'like':
            statistics.total_likes += 1
        elif interaction_type == 'share':
            statistics.total_shares += 1
        elif interaction_type == 'save':
            statistics.total_saves += 1
        
        # Update time spent
        if duration > 0:
            statistics.total_time_spent += duration // 60  # Convert seconds to minutes
        
        # Update category interactions
        if category:
            if not statistics.category_interactions:
                statistics.category_interactions = {}
            
            statistics.category_interactions[category] = statistics.category_interactions.get(category, 0) + 1
        
        # Update tag interactions
        if tags:
            if not statistics.tag_interactions:
                statistics.tag_interactions = {}
            
            for tag in tags:
                statistics.tag_interactions[tag] = statistics.tag_interactions.get(tag, 0) + 1
        
        # Update device usage
        if device_type:
            if not statistics.device_usage:
                statistics.device_usage = {}
            
            statistics.device_usage[device_type] = statistics.device_usage.get(device_type, 0) + 1
        
        # Update daily activity
        day_str = interaction_date.strftime('%Y-%m-%d')
        if not statistics.daily_activity:
            statistics.daily_activity = {}
        
        statistics.daily_activity[day_str] = statistics.daily_activity.get(day_str, 0) + 1
        
        # Update weekly activity
        week_str = interaction_date.strftime('%Y-%W')
        if not statistics.weekly_activity:
            statistics.weekly_activity = {}
        
        statistics.weekly_activity[week_str] = statistics.weekly_activity.get(week_str, 0) + 1
        
        # Update monthly activity
        month_str = interaction_date.strftime('%Y-%m')
        if not statistics.monthly_activity:
            statistics.monthly_activity = {}
        
        statistics.monthly_activity[month_str] = statistics.monthly_activity.get(month_str, 0) + 1
