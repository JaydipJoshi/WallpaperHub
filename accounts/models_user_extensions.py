from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import re

class UserProfile(models.Model):
    """Extended user profile with additional information"""
    # User relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Phone number with international format validation
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        help_text="Phone number in international format (e.g., +1234567890)"
    )

    # Phone verification status
    phone_verified = models.BooleanField(default=False)
    phone_verified_at = models.DateTimeField(null=True, blank=True)

    # Profile information
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    # Profile picture
    profile_picture = models.URLField(blank=True, help_text="URL to profile picture")

    # Account preferences
    receive_sms_notifications = models.BooleanField(default=False)
    receive_email_notifications = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def full_name(self):
        """Return the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.user.username

    @property
    def formatted_phone(self):
        """Return formatted phone number"""
        if self.phone_number:
            # Remove any non-digit characters except +
            cleaned = re.sub(r'[^\d+]', '', self.phone_number)
            if cleaned.startswith('+1') and len(cleaned) == 12:
                # US format: +1 (XXX) XXX-XXXX
                return f"+1 ({cleaned[2:5]}) {cleaned[5:8]}-{cleaned[8:]}"
            elif cleaned.startswith('+'):
                # International format: +XX XXXX XXXX
                country_code = cleaned[1:3] if len(cleaned) > 10 else cleaned[1:2]
                number = cleaned[len(country_code)+1:]
                if len(number) >= 8:
                    return f"+{country_code} {number[:4]} {number[4:]}"
                return cleaned
            else:
                # Domestic format
                if len(cleaned) == 10:
                    return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
                return cleaned
        return ""

class UserSettings(models.Model):
    """Model for user settings"""
    # User relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')

    # Appearance settings
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default'),
    ]

    LAYOUT_DENSITY_CHOICES = [
        ('compact', 'Compact'),
        ('medium', 'Medium'),
        ('comfortable', 'Comfortable'),
    ]

    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='system')
    accent_color = models.CharField(max_length=7, default='#65558F')  # Default purple
    layout_density = models.CharField(max_length=15, choices=LAYOUT_DENSITY_CHOICES, default='medium')

    # Privacy settings
    show_email = models.BooleanField(default=True)
    show_activity = models.BooleanField(default=True)
    allow_data_collection = models.BooleanField(default=True)

    # Notification settings
    email_notifications = models.BooleanField(default=True)  # Enabled by default
    site_notifications = models.BooleanField(default=True)

    # Connected accounts
    connected_google = models.BooleanField(default=False)

    # Session data
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_active = models.DateTimeField(default=timezone.now)

    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)  # Store MongoDB ObjectId as string

    class Meta:
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'

    def __str__(self):
        return f"{self.user.username}'s Settings"

    def update_last_active(self):
        """Update the last active timestamp"""
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])

    def sync_to_mongodb(self):
        """Sync this model to MongoDB"""
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']

            # Ensure the user_settings collection exists
            if 'user_settings' not in db.list_collection_names():
                db.create_collection('user_settings')

            settings = db.user_settings
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

        # Prepare data for MongoDB
        mongo_data = {
            'user_id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'theme': self.theme,
            'accent_color': self.accent_color,
            'layout_density': self.layout_density,
            'show_email': self.show_email,
            'show_activity': self.show_activity,
            'allow_data_collection': self.allow_data_collection,
            'email_notifications': self.email_notifications,
            'site_notifications': self.site_notifications,
            'connected_google': self.connected_google,
            'last_login_ip': self.last_login_ip,
            'last_active': self.last_active
        }

        # If we have a mongo_id, update the existing document
        if self.mongo_id:
            try:
                result = settings.update_one(
                    {'_id': ObjectId(self.mongo_id)},
                    {'$set': mongo_data}
                )
                return result.modified_count > 0
            except Exception as e:
                print(f"Error updating MongoDB document: {e}")
                return False
        else:
            # Insert a new document
            try:
                result = settings.insert_one(mongo_data)
                self.mongo_id = str(result.inserted_id)
                self.save(update_fields=['mongo_id'])
                return True
            except Exception as e:
                print(f"Error inserting MongoDB document: {e}")
                return False


class UserPreferences(models.Model):
    """Model for user wallpaper preferences"""
    # User relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')

    # Preferred categories (stored as a JSON array of category names)
    preferred_categories = models.JSONField(default=list, blank=True)

    # Preferred tags (stored as a JSON array of tag IDs or names)
    preferred_tags = models.JSONField(default=list, blank=True)

    # Preferred aspect ratios
    ASPECT_RATIO_CHOICES = [
        ('any', 'Any'),
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
        ('square', 'Square'),
        ('ultrawide', 'Ultrawide'),
    ]
    preferred_aspect_ratio = models.CharField(max_length=20, choices=ASPECT_RATIO_CHOICES, default='any')

    # Preferred color schemes (stored as a JSON array of color hex codes)
    preferred_colors = models.JSONField(default=list, blank=True)

    # Content preferences
    show_nsfw_content = models.BooleanField(default=False)
    hide_viewed_wallpapers = models.BooleanField(default=False)
    hide_downloaded_wallpapers = models.BooleanField(default=False)

    # Discovery preferences
    show_trending = models.BooleanField(default=True)
    show_featured = models.BooleanField(default=True)
    show_new = models.BooleanField(default=True)
    show_recommendations = models.BooleanField(default=True)

    # Download preferences
    DEFAULT_QUALITY_CHOICES = [
        ('original', 'Original'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    default_download_quality = models.CharField(max_length=20, choices=DEFAULT_QUALITY_CHOICES, default='high')
    auto_resize_to_screen = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)  # Store MongoDB ObjectId as string

    class Meta:
        verbose_name = 'User Preferences'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        return f"{self.user.username}'s Preferences"

    def get_preferred_categories_list(self):
        """Get preferred categories as a list"""
        return self.preferred_categories or []

    def add_preferred_category(self, category):
        """Add a category to preferred categories"""
        if not self.preferred_categories:
            self.preferred_categories = []

        if category not in self.preferred_categories:
            self.preferred_categories.append(category)
            self.save(update_fields=['preferred_categories'])
            return True
        return False

    def remove_preferred_category(self, category):
        """Remove a category from preferred categories"""
        if not self.preferred_categories:
            return False

        if category in self.preferred_categories:
            self.preferred_categories.remove(category)
            self.save(update_fields=['preferred_categories'])
            return True
        return False

    def get_preferred_tags_list(self):
        """Get preferred tags as a list"""
        return self.preferred_tags or []

    def add_preferred_tag(self, tag):
        """Add a tag to preferred tags"""
        if not self.preferred_tags:
            self.preferred_tags = []

        if tag not in self.preferred_tags:
            self.preferred_tags.append(tag)
            self.save(update_fields=['preferred_tags'])
            return True
        return False

    def remove_preferred_tag(self, tag):
        """Remove a tag from preferred tags"""
        if not self.preferred_tags:
            return False

        if tag in self.preferred_tags:
            self.preferred_tags.remove(tag)
            self.save(update_fields=['preferred_tags'])
            return True
        return False

    def get_preferred_colors_list(self):
        """Get preferred colors as a list"""
        return self.preferred_colors or []

    def add_preferred_color(self, color):
        """Add a color to preferred colors"""
        if not self.preferred_colors:
            self.preferred_colors = []

        if color not in self.preferred_colors:
            self.preferred_colors.append(color)
            self.save(update_fields=['preferred_colors'])
            return True
        return False

    def remove_preferred_color(self, color):
        """Remove a color from preferred colors"""
        if not self.preferred_colors:
            return False

        if color in self.preferred_colors:
            self.preferred_colors.remove(color)
            self.save(update_fields=['preferred_colors'])
            return True
        return False

    def sync_to_mongodb(self):
        """Sync this model to MongoDB"""
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']

            # Ensure the user_preferences collection exists
            if 'user_preferences' not in db.list_collection_names():
                db.create_collection('user_preferences')

            preferences = db.user_preferences
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

        # Prepare data for MongoDB
        mongo_data = {
            'user_id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'preferred_categories': self.preferred_categories,
            'preferred_tags': self.preferred_tags,
            'preferred_aspect_ratio': self.preferred_aspect_ratio,
            'preferred_colors': self.preferred_colors,
            'show_nsfw_content': self.show_nsfw_content,
            'hide_viewed_wallpapers': self.hide_viewed_wallpapers,
            'hide_downloaded_wallpapers': self.hide_downloaded_wallpapers,
            'show_trending': self.show_trending,
            'show_featured': self.show_featured,
            'show_new': self.show_new,
            'show_recommendations': self.show_recommendations,
            'default_download_quality': self.default_download_quality,
            'auto_resize_to_screen': self.auto_resize_to_screen,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        # If we have a mongo_id, update the existing document
        if self.mongo_id:
            try:
                result = preferences.update_one(
                    {'_id': ObjectId(self.mongo_id)},
                    {'$set': mongo_data}
                )
                return result.modified_count > 0
            except Exception as e:
                print(f"Error updating MongoDB document: {e}")
                return False
        else:
            # Insert a new document
            try:
                result = preferences.insert_one(mongo_data)
                self.mongo_id = str(result.inserted_id)
                self.save(update_fields=['mongo_id'])
                return True
            except Exception as e:
                print(f"Error inserting MongoDB document: {e}")
                return False


class UserStatistics(models.Model):
    """Model for tracking detailed user statistics"""
    # User relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='statistics')

    # General statistics
    total_views = models.PositiveIntegerField(default=0)
    total_downloads = models.PositiveIntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    total_saves = models.PositiveIntegerField(default=0)
    total_uploads = models.PositiveIntegerField(default=0)
    total_collections = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)

    # Time spent on the platform (in minutes)
    total_time_spent = models.PositiveIntegerField(default=0)

    # Category preferences (stored as a JSON object with category names as keys and counts as values)
    category_interactions = models.JSONField(default=dict, blank=True)

    # Tag preferences (stored as a JSON object with tag IDs or names as keys and counts as values)
    tag_interactions = models.JSONField(default=dict, blank=True)

    # Daily activity (stored as a JSON object with dates as keys and counts as values)
    daily_activity = models.JSONField(default=dict, blank=True)

    # Weekly activity (stored as a JSON object with week numbers as keys and counts as values)
    weekly_activity = models.JSONField(default=dict, blank=True)

    # Monthly activity (stored as a JSON object with month numbers as keys and counts as values)
    monthly_activity = models.JSONField(default=dict, blank=True)

    # Device usage (stored as a JSON object with device types as keys and counts as values)
    device_usage = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_interaction_at = models.DateTimeField(default=timezone.now)

    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)  # Store MongoDB ObjectId as string

    class Meta:
        verbose_name = 'User Statistics'
        verbose_name_plural = 'User Statistics'

    def __str__(self):
        return f"{self.user.username}'s Statistics"

    def record_interaction(self, interaction_type, category=None, tags=None, device_type=None, duration=0):
        """Record a user interaction and update statistics"""
        # Update total counts based on interaction type
        if interaction_type == 'view':
            self.total_views += 1
        elif interaction_type == 'download':
            self.total_downloads += 1
        elif interaction_type == 'like':
            self.total_likes += 1
        elif interaction_type == 'share':
            self.total_shares += 1
        elif interaction_type == 'save':
            self.total_saves += 1
        elif interaction_type == 'upload':
            self.total_uploads += 1

        # Update time spent
        if duration > 0:
            self.total_time_spent += duration // 60  # Convert seconds to minutes

        # Update category interactions
        if category:
            if not self.category_interactions:
                self.category_interactions = {}

            self.category_interactions[category] = self.category_interactions.get(category, 0) + 1

        # Update tag interactions
        if tags:
            if not self.tag_interactions:
                self.tag_interactions = {}

            for tag in tags:
                self.tag_interactions[tag] = self.tag_interactions.get(tag, 0) + 1

        # Update device usage
        if device_type:
            if not self.device_usage:
                self.device_usage = {}

            self.device_usage[device_type] = self.device_usage.get(device_type, 0) + 1

        # Update daily activity
        today = timezone.now().strftime('%Y-%m-%d')
        if not self.daily_activity:
            self.daily_activity = {}

        self.daily_activity[today] = self.daily_activity.get(today, 0) + 1

        # Update weekly activity
        week = timezone.now().strftime('%Y-%W')
        if not self.weekly_activity:
            self.weekly_activity = {}

        self.weekly_activity[week] = self.weekly_activity.get(week, 0) + 1

        # Update monthly activity
        month = timezone.now().strftime('%Y-%m')
        if not self.monthly_activity:
            self.monthly_activity = {}

        self.monthly_activity[month] = self.monthly_activity.get(month, 0) + 1

        # Update last interaction timestamp
        self.last_interaction_at = timezone.now()

        # Save the model
        self.save()

    def get_most_viewed_categories(self, limit=5):
        """Get the most viewed categories"""
        if not self.category_interactions:
            return []

        # Sort categories by view count
        sorted_categories = sorted(
            self.category_interactions.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_categories[:limit]

    def get_most_used_tags(self, limit=10):
        """Get the most used tags"""
        if not self.tag_interactions:
            return []

        # Sort tags by usage count
        sorted_tags = sorted(
            self.tag_interactions.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_tags[:limit]

    def get_activity_summary(self, days=30):
        """Get a summary of user activity for the last N days"""
        from datetime import datetime, timedelta

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Initialize summary
        summary = {
            'total_interactions': 0,
            'views': 0,
            'downloads': 0,
            'likes': 0,
            'shares': 0,
            'saves': 0,
            'daily_activity': {}
        }

        # Fill in daily activity for each day in the range
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            summary['daily_activity'][date_str] = self.daily_activity.get(date_str, 0)
            summary['total_interactions'] += summary['daily_activity'][date_str]
            current_date += timedelta(days=1)

        # Add totals for the period
        summary['views'] = self.total_views
        summary['downloads'] = self.total_downloads
        summary['likes'] = self.total_likes
        summary['shares'] = self.total_shares
        summary['saves'] = self.total_saves

        return summary

    def sync_to_mongodb(self):
        """Sync this model to MongoDB"""
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']

            # Ensure the user_statistics collection exists
            if 'user_statistics' not in db.list_collection_names():
                db.create_collection('user_statistics')

            statistics = db.user_statistics
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

        # Prepare data for MongoDB
        mongo_data = {
            'user_id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'total_views': self.total_views,
            'total_downloads': self.total_downloads,
            'total_likes': self.total_likes,
            'total_shares': self.total_shares,
            'total_saves': self.total_saves,
            'total_uploads': self.total_uploads,
            'total_collections': self.total_collections,
            'total_comments': self.total_comments,
            'total_time_spent': self.total_time_spent,
            'category_interactions': self.category_interactions,
            'tag_interactions': self.tag_interactions,
            'daily_activity': self.daily_activity,
            'weekly_activity': self.weekly_activity,
            'monthly_activity': self.monthly_activity,
            'device_usage': self.device_usage,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_interaction_at': self.last_interaction_at
        }

        # If we have a mongo_id, update the existing document
        if self.mongo_id:
            try:
                result = statistics.update_one(
                    {'_id': ObjectId(self.mongo_id)},
                    {'$set': mongo_data}
                )
                return result.modified_count > 0
            except Exception as e:
                print(f"Error updating MongoDB document: {e}")
                return False
        else:
            # Insert a new document
            try:
                result = statistics.insert_one(mongo_data)
                self.mongo_id = str(result.inserted_id)
                self.save(update_fields=['mongo_id'])
                return True
            except Exception as e:
                print(f"Error inserting MongoDB document: {e}")
                return False


# Signal handlers to create user profile extensions when a user is created
@receiver(post_save, sender=User)
def create_user_profile_extensions(sender, instance, created, **kwargs):
    """Create user profile extensions when a new user is created"""
    if created:
        # Create UserProfile
        UserProfile.objects.get_or_create(user=instance)

        # Create UserSettings
        UserSettings.objects.get_or_create(user=instance)

        # Create UserPreferences
        UserPreferences.objects.get_or_create(user=instance)

        # Create UserStatistics
        UserStatistics.objects.get_or_create(user=instance)


# Signal handlers for MongoDB syncing
@receiver(post_save, sender=UserSettings)
def user_settings_post_save(sender, instance, **kwargs):
    """Sync UserSettings to MongoDB after save"""
    # Only sync if we're not already in the middle of a sync operation
    if not getattr(instance, '_syncing', False):
        instance._syncing = True
        instance.sync_to_mongodb()
        instance._syncing = False


@receiver(post_save, sender=UserPreferences)
def user_preferences_post_save(sender, instance, **kwargs):
    """Sync UserPreferences to MongoDB after save"""
    # Only sync if we're not already in the middle of a sync operation
    if not getattr(instance, '_syncing', False):
        instance._syncing = True
        instance.sync_to_mongodb()
        instance._syncing = False


@receiver(post_save, sender=UserStatistics)
def user_statistics_post_save(sender, instance, **kwargs):
    """Sync UserStatistics to MongoDB after save"""
    # Only sync if we're not already in the middle of a sync operation
    if not getattr(instance, '_syncing', False):
        instance._syncing = True
        instance.sync_to_mongodb()
        instance._syncing = False


# Utility functions
def get_user_preferences(user):
    """Get or create user preferences"""
    if not user or not user.is_authenticated:
        return None

    preferences, created = UserPreferences.objects.get_or_create(user=user)
    return preferences


def get_user_statistics(user):
    """Get or create user statistics"""
    if not user or not user.is_authenticated:
        return None

    statistics, created = UserStatistics.objects.get_or_create(user=user)
    return statistics


def get_user_settings(user):
    """Get or create user settings"""
    if not user or not user.is_authenticated:
        return None

    settings, created = UserSettings.objects.get_or_create(user=user)
    return settings


def get_recommended_wallpapers(user, limit=10):
    """Get recommended wallpapers based on user preferences and statistics"""
    from django.db.models import Q
    from .models import Wallpaper, Tag

    if not user or not user.is_authenticated:
        # For anonymous users, return trending wallpapers
        return Wallpaper.objects.order_by('-views')[:limit]

    # Get user preferences and statistics
    preferences = get_user_preferences(user)
    statistics = get_user_statistics(user)

    if not preferences or not statistics:
        # If no preferences or statistics, return trending wallpapers
        return Wallpaper.objects.order_by('-views')[:limit]

    # Start with an empty query
    query = Q()

    # Add preferred categories to query
    if preferences.preferred_categories:
        category_query = Q()
        for category in preferences.preferred_categories:
            category_query |= Q(category=category)
        query |= category_query

    # Add preferred tags to query
    if preferences.preferred_tags:
        # Convert tag names to Tag objects
        tag_objects = []
        for tag_name in preferences.preferred_tags:
            try:
                tag = Tag.objects.get(name=tag_name)
                tag_objects.append(tag)
            except Tag.DoesNotExist:
                pass

        if tag_objects:
            query |= Q(tags__in=tag_objects)

    # Add most interacted categories from statistics
    if statistics.category_interactions:
        top_categories = [cat for cat, _ in statistics.get_most_viewed_categories(3)]
        if top_categories:
            category_query = Q()
            for category in top_categories:
                category_query |= Q(category=category)
            query |= category_query

    # Add most interacted tags from statistics
    if statistics.tag_interactions:
        top_tags = [tag for tag, _ in statistics.get_most_used_tags(5)]
        if top_tags:
            # Convert tag names to Tag objects
            tag_objects = []
            for tag_name in top_tags:
                try:
                    tag = Tag.objects.get(name=tag_name)
                    tag_objects.append(tag)
                except Tag.DoesNotExist:
                    pass

            if tag_objects:
                query |= Q(tags__in=tag_objects)

    # Filter out wallpapers the user has already interacted with if requested
    if preferences.hide_viewed_wallpapers:
        query &= ~Q(user_interactions__user=user, user_interactions__interaction_type='view')

    if preferences.hide_downloaded_wallpapers:
        query &= ~Q(user_interactions__user=user, user_interactions__interaction_type='download')

    # Get recommended wallpapers
    if query:
        # If we have a query, use it to filter wallpapers
        recommended = Wallpaper.objects.filter(query).distinct().order_by('-views')[:limit]

        # If we don't have enough recommendations, add some trending wallpapers
        if recommended.count() < limit:
            # Get IDs of wallpapers we already have
            existing_ids = [w.id for w in recommended]

            # Get additional trending wallpapers
            additional = Wallpaper.objects.exclude(id__in=existing_ids).order_by('-views')[:limit - recommended.count()]

            # Combine the querysets
            recommended = list(recommended) + list(additional)
    else:
        # If no query was built, return trending wallpapers
        recommended = Wallpaper.objects.order_by('-views')[:limit]

    return recommended
