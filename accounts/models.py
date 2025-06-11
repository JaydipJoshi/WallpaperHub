from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
import uuid

# Create your models here.

class NewsletterSubscriber(models.Model):
    """
    Model to store newsletter subscribers
    """
    email = models.EmailField(unique=True, db_index=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    source = models.CharField(max_length=50, default='footer_form')  # Track where they subscribed from

    # Optional user relationship (if they're registered users)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='newsletter_subscriptions')

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'

    def __str__(self):
        return f"{self.email} ({'Active' if self.is_active else 'Inactive'})"

    def unsubscribe(self):
        """Unsubscribe the user"""
        self.is_active = False
        self.save()

    def get_unsubscribe_url(self):
        """Get the unsubscribe URL for this subscriber"""
        from django.urls import reverse
        from django.conf import settings
        return f"{settings.SITE_URL}{reverse('newsletter_unsubscribe', kwargs={'token': self.unsubscribe_token})}"


class PasswordResetOTP(models.Model):
    """
    Model to store OTP for password reset functionality
    """
    CONTACT_TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]

    contact_value = models.CharField(max_length=255, db_index=True)  # Email or phone number
    contact_type = models.CharField(max_length=10, choices=CONTACT_TYPE_CHOICES)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Link to user if they exist
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Password Reset OTP'
        verbose_name_plural = 'Password Reset OTPs'
        indexes = [
            models.Index(fields=['contact_value', 'contact_type']),
            models.Index(fields=['otp_code', 'is_used']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"OTP for {self.contact_value} ({self.contact_type}) - {'Used' if self.is_used else 'Active'}"

    def is_expired(self):
        """Check if OTP has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Check if OTP is valid (not expired, not used, not too many attempts)"""
        return not self.is_expired() and not self.is_used and self.attempts < 5

    def verify_otp(self, provided_otp):
        """Verify the provided OTP"""
        self.attempts += 1
        self.save()

        if not self.is_valid():
            return False

        if self.otp_code == provided_otp:
            self.is_verified = True
            self.is_used = True
            self.save()
            return True

        return False

    @classmethod
    def generate_otp(cls, contact_value, contact_type, user=None, ip_address=None, user_agent=None):
        """Generate a new OTP for password reset"""
        import random
        from django.utils import timezone
        from datetime import timedelta

        # Generate 6-digit OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # Set expiration time (10 minutes from now)
        expires_at = timezone.now() + timedelta(minutes=10)

        # Deactivate any existing OTPs for this contact
        cls.objects.filter(
            contact_value=contact_value,
            contact_type=contact_type,
            is_used=False
        ).update(is_used=True)

        # Create new OTP
        otp_instance = cls.objects.create(
            contact_value=contact_value,
            contact_type=contact_type,
            otp_code=otp_code,
            expires_at=expires_at,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return otp_instance


class Tag(models.Model):
    """Model for wallpaper tags"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Statistics
    usage_count = models.PositiveIntegerField(default=0)  # Number of wallpapers using this tag
    search_count = models.PositiveIntegerField(default=0)  # Number of times this tag was searched for

    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)  # Store MongoDB ObjectId as string

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['usage_count']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Generate slug from name if not provided
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tag_detail', args=[str(self.slug)])

    def get_wallpapers(self):
        """Get all wallpapers with this tag"""
        return self.wallpapers.all()

    def increment_search_count(self):
        """Increment the search count for this tag"""
        self.search_count += 1
        self.save(update_fields=['search_count'])

    def update_usage_count(self):
        """Update the usage count based on actual wallpaper count"""
        self.usage_count = self.wallpapers.count()
        self.save(update_fields=['usage_count'])

    def sync_to_mongodb(self):
        """Sync this tag to MongoDB"""
        from pymongo import MongoClient
        from bson.objectid import ObjectId

        # Get MongoDB connection
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']

            # Ensure the tags collection exists
            if 'tags' not in db.list_collection_names():
                db.create_collection('tags')

            tags = db.tags
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

        # Prepare data for MongoDB
        mongo_data = {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'usage_count': self.usage_count,
            'search_count': self.search_count
        }

        # If we have a mongo_id, update the existing document
        if self.mongo_id:
            try:
                result = tags.update_one(
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
                result = tags.insert_one(mongo_data)
                self.mongo_id = str(result.inserted_id)
                self.save(update_fields=['mongo_id'])
                return True
            except Exception as e:
                print(f"Error inserting MongoDB document: {e}")
                return False

    @classmethod
    def sync_from_mongodb(cls, mongo_tag):
        """Create or update a Django Tag model from MongoDB data"""
        from bson.objectid import ObjectId

        # Check if we already have this tag in Django
        mongo_id = str(mongo_tag.get('_id'))
        tag = None

        try:
            # Try to find by MongoDB ID
            tag = cls.objects.get(mongo_id=mongo_id)
        except cls.DoesNotExist:
            # If not found by mongo_id, try to find by name or slug
            name = mongo_tag.get('name')
            slug = mongo_tag.get('slug')

            if name:
                try:
                    tag = cls.objects.get(name=name)
                except cls.DoesNotExist:
                    pass

            if not tag and slug:
                try:
                    tag = cls.objects.get(slug=slug)
                except cls.DoesNotExist:
                    pass

        # If not found, create a new one
        if not tag:
            tag = cls()
            tag.mongo_id = mongo_id

        # Update fields from MongoDB data
        tag.name = mongo_tag.get('name', 'Unnamed Tag')
        tag.slug = mongo_tag.get('slug', slugify(tag.name))
        tag.description = mongo_tag.get('description', '')
        tag.usage_count = mongo_tag.get('usage_count', 0)
        tag.search_count = mongo_tag.get('search_count', 0)

        # Handle timestamps
        if 'created_at' in mongo_tag:
            # Convert string to datetime if needed
            created_at = mongo_tag['created_at']
            if isinstance(created_at, str):
                from dateutil import parser
                try:
                    tag.created_at = parser.parse(created_at)
                except:
                    pass
            elif hasattr(created_at, 'strftime'):  # It's already a datetime
                tag.created_at = created_at

        # Save the tag
        tag.save()

        return tag


class Wallpaper(models.Model):
    """Base model for wallpapers with essential fields"""
    # Unique identifier for the wallpaper
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Image URLs
    image_url = models.URLField(max_length=500, blank=True)  # Main image URL (could be external or local)
    image_path = models.CharField(max_length=500, blank=True)  # Path to locally stored image

    # Image variations (stored as JSON in MongoDB, as text here)
    small_url = models.URLField(max_length=500, blank=True)  # Small version URL
    regular_url = models.URLField(max_length=500, blank=True)  # Regular version URL
    full_url = models.URLField(max_length=500, blank=True)  # Full version URL

    # Metadata
    tags = models.ManyToManyField(Tag, related_name='wallpapers', blank=True)  # Many-to-many relationship with tags
    tags_string = models.CharField(max_length=500, blank=True)  # Legacy field for comma-separated tags (for backward compatibility)
    category = models.CharField(max_length=100, blank=True)  # Legacy field for category name (for backward compatibility)
    category_obj = models.ForeignKey('accounts.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='wallpapers')  # Relationship to Category model

    # Featured status
    is_featured = models.BooleanField(default=False)  # Whether this wallpaper is featured
    featured_at = models.DateTimeField(null=True, blank=True)  # When this wallpaper was featured

    # Statistics
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    # Advanced statistics
    daily_views = models.JSONField(default=dict, blank=True)  # Store daily view counts as JSON
    weekly_views = models.JSONField(default=dict, blank=True)  # Store weekly view counts as JSON
    monthly_views = models.JSONField(default=dict, blank=True)  # Store monthly view counts as JSON

    # User interaction tracking
    liked_by_users = models.ManyToManyField(User, related_name='liked_wallpapers', blank=True)
    downloaded_by_users = models.ManyToManyField(User, related_name='downloaded_wallpapers', blank=True)
    saved_by_users = models.ManyToManyField(User, related_name='saved_wallpapers', blank=True)

    # Source information
    unsplash_id = models.CharField(max_length=100, blank=True)  # For Unsplash wallpapers
    custom_upload = models.BooleanField(default=False)  # Flag for user uploads

    # User relationship
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_wallpapers')

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)  # Last time the wallpaper was viewed
    last_downloaded_at = models.DateTimeField(null=True, blank=True)  # Last time the wallpaper was downloaded
    last_shared_at = models.DateTimeField(null=True, blank=True)  # Last time the wallpaper was shared
    featured_at = models.DateTimeField(null=True, blank=True)  # When the wallpaper was featured (if applicable)

    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)  # Store MongoDB ObjectId as string

    class Meta:
        verbose_name = 'Wallpaper'
        verbose_name_plural = 'Wallpapers'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Update featured_at timestamp if featured status changes
        if self.is_featured and not self.featured_at:
            self.featured_at = timezone.now()
        elif not self.is_featured and self.featured_at:
            self.featured_at = None

        # Sync category_obj with category string if needed
        if self.category and not self.category_obj:
            from .models_category import get_or_create_category
            self.category_obj = get_or_create_category(self.category)
        elif self.category_obj and not self.category:
            self.category = self.category_obj.name

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('wallpaper_detail', args=[str(self.id)])

    def increment_view(self, user=None, request=None):
        """Increment the view count for this wallpaper"""
        self.views += 1
        self.save(update_fields=['views'])

        # Record the interaction if user is provided
        if user and user.is_authenticated:
            from .models import WallpaperInteraction

            # Get IP address and user agent from request
            ip_address = None
            user_agent = None
            device_type = 'unknown'
            referrer = None
            session_id = None

            if request:
                # Get IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')

                # Get user agent
                user_agent = request.META.get('HTTP_USER_AGENT')

                # Determine device type
                if user_agent:
                    if 'Mobile' in user_agent or 'Android' in user_agent:
                        device_type = 'mobile'
                    elif 'Tablet' in user_agent or 'iPad' in user_agent:
                        device_type = 'tablet'
                    else:
                        device_type = 'desktop'

                # Get referrer
                referrer = request.META.get('HTTP_REFERER')

                # Get session ID
                session_id = request.session.session_key

            # Create the interaction
            interaction = WallpaperInteraction(
                user=user,
                wallpaper=self,
                interaction_type='view',
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_type,
                referrer=referrer,
                session_id=session_id
            )
            interaction.save()

            # Update user statistics if available
            try:
                from .models_user_extensions import get_user_statistics
                statistics = get_user_statistics(user)
                if statistics:
                    # Get category and tags
                    category = self.category
                    tags = [tag.name for tag in self.tags.all()]

                    # Record the interaction
                    statistics.record_interaction(
                        interaction_type='view',
                        category=category,
                        tags=tags,
                        device_type=device_type
                    )
            except ImportError:
                pass

        # Update category view count if available
        if self.category_obj:
            self.category_obj.increment_view_count()

        return self.views

    def toggle_like(self, user=None, request=None):
        """Toggle the like status for this wallpaper"""
        if not user or not user.is_authenticated:
            return False, self.likes

        from .models import WallpaperInteraction

        # Check if the user has already liked this wallpaper
        existing_like = WallpaperInteraction.objects.filter(
            user=user,
            wallpaper=self,
            interaction_type='like'
        ).first()

        if existing_like:
            # User has already liked this wallpaper, so unlike it
            existing_like.delete()
            self.likes = max(0, self.likes - 1)  # Ensure likes don't go below 0
            self.save(update_fields=['likes'])
            liked = False
        else:
            # User hasn't liked this wallpaper yet, so like it
            # Get IP address and user agent from request
            ip_address = None
            user_agent = None
            device_type = 'unknown'
            session_id = None

            if request:
                # Get IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')

                # Get user agent
                user_agent = request.META.get('HTTP_USER_AGENT')

                # Determine device type
                if user_agent:
                    if 'Mobile' in user_agent or 'Android' in user_agent:
                        device_type = 'mobile'
                    elif 'Tablet' in user_agent or 'iPad' in user_agent:
                        device_type = 'tablet'
                    else:
                        device_type = 'desktop'

                # Get session ID
                session_id = request.session.session_key

            # Create the interaction
            interaction = WallpaperInteraction(
                user=user,
                wallpaper=self,
                interaction_type='like',
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_type,
                session_id=session_id
            )
            interaction.save()

            # Increment the like count
            self.likes += 1
            self.save(update_fields=['likes'])
            liked = True

            # Update user statistics if available
            try:
                from .models_user_extensions import get_user_statistics
                statistics = get_user_statistics(user)
                if statistics:
                    # Get category and tags
                    category = self.category
                    tags = [tag.name for tag in self.tags.all()]

                    # Record the interaction
                    statistics.record_interaction(
                        interaction_type='like',
                        category=category,
                        tags=tags,
                        device_type=device_type
                    )
            except ImportError:
                pass

        return liked, self.likes

    def increment_download(self, user=None, request=None):
        """Increment the download count for this wallpaper"""
        self.downloads += 1
        self.save(update_fields=['downloads'])

        # Record the interaction if user is provided
        if user and user.is_authenticated:
            from .models import WallpaperInteraction

            # Get IP address and user agent from request
            ip_address = None
            user_agent = None
            device_type = 'unknown'
            referrer = None
            session_id = None

            if request:
                # Get IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')

                # Get user agent
                user_agent = request.META.get('HTTP_USER_AGENT')

                # Determine device type
                if user_agent:
                    if 'Mobile' in user_agent or 'Android' in user_agent:
                        device_type = 'mobile'
                    elif 'Tablet' in user_agent or 'iPad' in user_agent:
                        device_type = 'tablet'
                    else:
                        device_type = 'desktop'

                # Get referrer
                referrer = request.META.get('HTTP_REFERER')

                # Get session ID
                session_id = request.session.session_key

            # Create the interaction
            interaction = WallpaperInteraction(
                user=user,
                wallpaper=self,
                interaction_type='download',
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_type,
                referrer=referrer,
                session_id=session_id
            )
            interaction.save()

            # Update user statistics if available
            try:
                from .models_user_extensions import get_user_statistics
                statistics = get_user_statistics(user)
                if statistics:
                    # Get category and tags
                    category = self.category
                    tags = [tag.name for tag in self.tags.all()]

                    # Record the interaction
                    statistics.record_interaction(
                        interaction_type='download',
                        category=category,
                        tags=tags,
                        device_type=device_type
                    )
            except ImportError:
                pass

        return self.downloads

    def increment_share(self, platform=None, user=None, request=None):
        """Increment the share count for this wallpaper"""
        self.shares += 1
        self.save(update_fields=['shares'])

        # Record the interaction if user is provided
        if user and user.is_authenticated:
            from .models import WallpaperInteraction

            # Get IP address and user agent from request
            ip_address = None
            user_agent = None
            device_type = 'unknown'
            referrer = None
            session_id = None

            if request:
                # Get IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')

                # Get user agent
                user_agent = request.META.get('HTTP_USER_AGENT')

                # Determine device type
                if user_agent:
                    if 'Mobile' in user_agent or 'Android' in user_agent:
                        device_type = 'mobile'
                    elif 'Tablet' in user_agent or 'iPad' in user_agent:
                        device_type = 'tablet'
                    else:
                        device_type = 'desktop'

                # Get referrer
                referrer = request.META.get('HTTP_REFERER')

                # Get session ID
                session_id = request.session.session_key

            # Create the interaction
            interaction = WallpaperInteraction(
                user=user,
                wallpaper=self,
                interaction_type='share',
                share_platform=platform,
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_type,
                referrer=referrer,
                session_id=session_id
            )
            interaction.save()

            # Update user statistics if available
            try:
                from .models_user_extensions import get_user_statistics
                statistics = get_user_statistics(user)
                if statistics:
                    # Get category and tags
                    category = self.category
                    tags = [tag.name for tag in self.tags.all()]

                    # Record the interaction
                    statistics.record_interaction(
                        interaction_type='share',
                        category=category,
                        tags=tags,
                        device_type=device_type
                    )
            except ImportError:
                pass

        return self.shares

    def get_image_url(self):
        """Return the best available image URL"""
        if self.image_url:
            return self.image_url
        elif self.image_path:
            return self.image_path
        elif self.full_url:
            return self.full_url
        elif self.regular_url:
            return self.regular_url
        elif self.small_url:
            return self.small_url
        return ''

    def increment_view(self, user=None, request=None):
        """Increment view count and update last_viewed_at"""
        self.views += 1
        self.last_viewed_at = timezone.now()

        # Update daily views statistics
        today = timezone.now().strftime('%Y-%m-%d')
        daily_stats = self.daily_views or {}
        daily_stats[today] = daily_stats.get(today, 0) + 1
        self.daily_views = daily_stats

        # If user is provided, track the view using WallpaperInteraction
        if user and user.is_authenticated:
            # Record the interaction
            WallpaperInteraction.record_interaction(
                user=user,
                wallpaper=self,
                interaction_type='view',
                request=request
            )
        else:
            # Just save the wallpaper without recording an interaction
            self.save(update_fields=['views', 'last_viewed_at', 'daily_views'])

    def increment_download(self, user=None, request=None):
        """Increment download count and update last_downloaded_at"""
        self.downloads += 1
        self.last_downloaded_at = timezone.now()

        # If user is provided, track the download using WallpaperInteraction
        if user and user.is_authenticated:
            # Add to downloaded_by_users
            self.downloaded_by_users.add(user)

            # Record the interaction
            WallpaperInteraction.record_interaction(
                user=user,
                wallpaper=self,
                interaction_type='download',
                request=request
            )
        else:
            # Just save the wallpaper without recording an interaction
            self.save(update_fields=['downloads', 'last_downloaded_at'])

    def increment_share(self, user=None, request=None, share_platform=None):
        """Increment share count and update last_shared_at"""
        self.shares += 1
        self.last_shared_at = timezone.now()

        # If user is provided, track the share using WallpaperInteraction
        if user and user.is_authenticated:
            # Record the interaction
            WallpaperInteraction.record_interaction(
                user=user,
                wallpaper=self,
                interaction_type='share',
                request=request,
                share_platform=share_platform or ''
            )
        else:
            # Just save the wallpaper without recording an interaction
            self.save(update_fields=['shares', 'last_shared_at'])

    def toggle_like(self, user, request=None):
        """Toggle like status for a user"""
        if not user or not user.is_authenticated:
            return False

        if user in self.liked_by_users.all():
            # User already liked this wallpaper, so unlike it
            self.liked_by_users.remove(user)
            self.likes -= 1
            liked = False

            # Record the unlike interaction
            WallpaperInteraction.record_interaction(
                user=user,
                wallpaper=self,
                interaction_type='unlike',
                request=request
            )
        else:
            # User hasn't liked this wallpaper yet, so like it
            self.liked_by_users.add(user)
            self.likes += 1
            liked = True

            # Record the like interaction
            WallpaperInteraction.record_interaction(
                user=user,
                wallpaper=self,
                interaction_type='like',
                request=request
            )

        # No need to save here as the record_interaction method will save the wallpaper
        return liked

    def toggle_save(self, user, request=None):
        """Toggle save status for a user"""
        if not user or not user.is_authenticated:
            return False

        if user in self.saved_by_users.all():
            # User already saved this wallpaper, so unsave it
            self.saved_by_users.remove(user)
            saved = False

            # Record the unsave interaction
            WallpaperInteraction.record_interaction(
                user=user,
                wallpaper=self,
                interaction_type='unsave',
                request=request
            )
        else:
            # User hasn't saved this wallpaper yet, so save it
            self.saved_by_users.add(user)
            saved = True

            # Record the save interaction
            WallpaperInteraction.record_interaction(
                user=user,
                wallpaper=self,
                interaction_type='save',
                request=request
            )

        return saved

    def get_related_wallpapers(self, limit=6):
        """Get related wallpapers based on tags and category"""
        from django.db.models import Q

        # Start with an empty queryset
        related = Wallpaper.objects.none()

        # If we have tags, find wallpapers with similar tags
        if self.tags.exists():
            # Get wallpapers that share tags with this wallpaper
            related = Wallpaper.objects.filter(tags__in=self.tags.all()).exclude(id=self.id).distinct()
        # Fallback to legacy tags_string if no tags relationship is populated
        elif self.tags_string:
            tags_list = [tag.strip() for tag in self.tags_string.split(',')]
            tag_filter = Q()
            for tag in tags_list:
                tag_filter |= Q(tags_string__icontains=tag)

            related = Wallpaper.objects.filter(tag_filter).exclude(id=self.id)

        # If we have a category, add wallpapers from the same category
        if self.category:
            category_related = Wallpaper.objects.filter(category=self.category).exclude(id=self.id)
            related = (related | category_related).distinct()

        # If we still don't have enough, add some recent wallpapers
        if related.count() < limit:
            recent = Wallpaper.objects.exclude(id=self.id).order_by('-created_at')
            related = (related | recent).distinct()

        return related[:limit]

    def get_stats_summary(self):
        """Get a summary of the wallpaper's statistics"""
        return {
            'views': self.views,
            'likes': self.likes,
            'downloads': self.downloads,
            'shares': self.shares,
            'daily_views': self.daily_views,
            'weekly_views': self.weekly_views,
            'monthly_views': self.monthly_views,
        }

    def update_weekly_monthly_stats(self):
        """Update weekly and monthly statistics based on daily views"""
        from datetime import datetime, timedelta

        # Get daily stats
        daily_stats = self.daily_views or {}

        # Calculate weekly stats
        weekly_stats = {}
        today = datetime.now().date()

        # Process the last 12 weeks
        for week_offset in range(12):
            week_start = today - timedelta(days=today.weekday() + 7 * week_offset)
            week_end = week_start + timedelta(days=6)
            week_key = f"{week_start.isocalendar()[0]}-W{week_start.isocalendar()[1]}"

            # Sum up daily views for this week
            week_views = 0
            current = week_start
            while current <= week_end and current <= today:
                date_key = current.strftime('%Y-%m-%d')
                week_views += daily_stats.get(date_key, 0)
                current += timedelta(days=1)

            if week_views > 0:
                weekly_stats[week_key] = week_views

        # Calculate monthly stats
        monthly_stats = {}

        # Process the last 12 months
        for month_offset in range(12):
            month_date = today.replace(day=1) - timedelta(days=1 * month_offset * 30)  # Approximate
            month_key = month_date.strftime('%Y-%m')

            # Sum up daily views for this month
            month_views = 0
            for date_key, views in daily_stats.items():
                if date_key.startswith(month_key):
                    month_views += views

            if month_views > 0:
                monthly_stats[month_key] = month_views

        # Update the model
        self.weekly_views = weekly_stats
        self.monthly_views = monthly_stats
        self.save(update_fields=['weekly_views', 'monthly_views'])

    @classmethod
    def sync_from_mongodb(cls, mongo_wallpaper):
        """Create or update a Django Wallpaper model from MongoDB data"""
        from bson.objectid import ObjectId

        # Check if we already have this wallpaper in Django
        mongo_id = str(mongo_wallpaper.get('_id'))
        wallpaper = None

        try:
            # Try to find by MongoDB ID
            wallpaper = cls.objects.get(mongo_id=mongo_id)
        except cls.DoesNotExist:
            # If not found by mongo_id, try to find by unsplash_id if available
            unsplash_id = mongo_wallpaper.get('unsplash_id')
            if unsplash_id:
                try:
                    wallpaper = cls.objects.get(unsplash_id=unsplash_id)
                except cls.DoesNotExist:
                    pass

        # If not found, create a new one
        if not wallpaper:
            wallpaper = cls()

        # Update fields from MongoDB data
        wallpaper.mongo_id = mongo_id
        wallpaper.title = mongo_wallpaper.get('title', 'Untitled Wallpaper')
        wallpaper.description = mongo_wallpaper.get('description', '')

        # Handle image paths/URLs
        wallpaper.image_path = mongo_wallpaper.get('image_path', '')

        # Handle Unsplash data if available
        if 'unsplash_id' in mongo_wallpaper:
            wallpaper.unsplash_id = mongo_wallpaper['unsplash_id']

            # If this is an Unsplash wallpaper, it might have URLs in a nested structure
            urls = mongo_wallpaper.get('urls', {})
            if urls:
                wallpaper.small_url = urls.get('small', '')
                wallpaper.regular_url = urls.get('regular', '')
                wallpaper.full_url = urls.get('full', '')

        # Handle tags
        if 'tags' in mongo_wallpaper:
            # Store the original tags in the legacy field for backward compatibility
            if isinstance(mongo_wallpaper['tags'], list):
                wallpaper.tags_string = ','.join(mongo_wallpaper['tags'])
            else:
                wallpaper.tags_string = mongo_wallpaper['tags']

            # Save the wallpaper first so we can add tags
            wallpaper.save()

            # Now process tags and add them to the many-to-many relationship
            if isinstance(mongo_wallpaper['tags'], list):
                tag_names = mongo_wallpaper['tags']
            else:
                tag_names = [tag.strip() for tag in mongo_wallpaper['tags'].split(',') if tag.strip()]

            # Clear existing tags
            wallpaper.tags.clear()

            # Add each tag
            for tag_name in tag_names:
                if not tag_name.strip():
                    continue

                # Try to find existing tag or create a new one
                tag, created = Tag.objects.get_or_create(
                    name=tag_name.strip(),
                    defaults={'slug': slugify(tag_name.strip())}
                )

                # Add tag to wallpaper
                wallpaper.tags.add(tag)

                # Update tag usage count
                tag.update_usage_count()

        # Handle statistics
        wallpaper.views = mongo_wallpaper.get('views', 0)
        wallpaper.likes = mongo_wallpaper.get('likes', 0)
        wallpaper.downloads = mongo_wallpaper.get('downloads', 0)
        wallpaper.shares = mongo_wallpaper.get('shares', 0)

        # Handle custom upload flag
        wallpaper.custom_upload = mongo_wallpaper.get('custom_upload', False)

        # Handle category
        wallpaper.category = mongo_wallpaper.get('category', '')

        # Handle featured status
        wallpaper.is_featured = mongo_wallpaper.get('is_featured', False)

        # Handle featured_at timestamp
        if 'featured_at' in mongo_wallpaper and mongo_wallpaper['featured_at']:
            # Convert string to datetime if needed
            featured_at = mongo_wallpaper['featured_at']
            if isinstance(featured_at, str):
                from dateutil import parser
                try:
                    wallpaper.featured_at = parser.parse(featured_at)
                except:
                    pass
            elif hasattr(featured_at, 'strftime'):  # It's already a datetime
                wallpaper.featured_at = featured_at
        elif wallpaper.is_featured and not wallpaper.featured_at:
            wallpaper.featured_at = timezone.now()
        elif not wallpaper.is_featured and wallpaper.featured_at:
            wallpaper.featured_at = None

        # Handle category relationship
        if wallpaper.category and not wallpaper.category_obj:
            from .models_category import get_or_create_category
            wallpaper.category_obj = get_or_create_category(wallpaper.category)

        # Handle timestamps
        if 'created_at' in mongo_wallpaper:
            # Convert string to datetime if needed
            created_at = mongo_wallpaper['created_at']
            if isinstance(created_at, str):
                from dateutil import parser
                try:
                    wallpaper.created_at = parser.parse(created_at)
                except:
                    pass
            elif hasattr(created_at, 'strftime'):  # It's already a datetime
                wallpaper.created_at = created_at

        # Save the wallpaper
        wallpaper.save()

        return wallpaper

    def sync_to_mongodb(self):
        """Sync this Django model to MongoDB"""
        from pymongo import MongoClient
        from bson.objectid import ObjectId

        # Get MongoDB connection
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            wallpapers = db.wallpapers
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

        # Prepare data for MongoDB
        mongo_data = {
            'title': self.title,
            'description': self.description,
            'image_path': self.image_path,
            'category': self.category,
            'views': self.views,
            'likes': self.likes,
            'downloads': self.downloads,
            'shares': self.shares,
            'custom_upload': self.custom_upload,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_featured': self.is_featured,
            'featured_at': self.featured_at
        }

        # Add category_obj reference if available
        if self.category_obj:
            mongo_data['category_id'] = str(self.category_obj.id)
            mongo_data['category_name'] = self.category_obj.name
            mongo_data['category_slug'] = self.category_obj.slug

        # Handle tags - store both as objects and as strings for backward compatibility
        if self.tags.exists():
            # Get tag names from the many-to-many relationship
            tag_names = list(self.tags.values_list('name', flat=True))
            mongo_data['tags'] = tag_names
            mongo_data['tags_string'] = ','.join(tag_names)
        elif self.tags_string:
            # Use legacy tags_string if no tags relationship is populated
            tag_list = [tag.strip() for tag in self.tags_string.split(',') if tag.strip()]
            mongo_data['tags'] = tag_list
            mongo_data['tags_string'] = self.tags_string

        # Add Unsplash ID if available
        if self.unsplash_id:
            mongo_data['unsplash_id'] = self.unsplash_id

        # Add URLs if available
        if self.small_url or self.regular_url or self.full_url:
            mongo_data['urls'] = {
                'small': self.small_url,
                'regular': self.regular_url,
                'full': self.full_url
            }

        # If we have a mongo_id, update the existing document
        if self.mongo_id:
            try:
                result = wallpapers.update_one(
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
                result = wallpapers.insert_one(mongo_data)
                self.mongo_id = str(result.inserted_id)
                self.save(update_fields=['mongo_id'])
                return True
            except Exception as e:
                print(f"Error inserting MongoDB document: {e}")
                return False


class WallpaperInteraction(models.Model):
    """Model to track detailed user interactions with wallpapers"""
    # Interaction types
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('like', 'Like'),
        ('unlike', 'Unlike'),
        ('download', 'Download'),
        ('save', 'Save'),
        ('unsave', 'Unsave'),
        ('share', 'Share'),
    ]

    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallpaper_interactions')
    wallpaper = models.ForeignKey(Wallpaper, on_delete=models.CASCADE, related_name='user_interactions')

    # Interaction details
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)

    # Additional data
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, blank=True)  # mobile, tablet, desktop
    session_id = models.CharField(max_length=40, blank=True)  # Django session ID

    # For shares, track the platform
    share_platform = models.CharField(max_length=50, blank=True)  # facebook, twitter, whatsapp, etc.

    # For analytics
    referrer = models.URLField(max_length=500, blank=True)  # Where the user came from
    duration = models.PositiveIntegerField(default=0)  # Time spent in seconds (for views)

    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)  # Store MongoDB ObjectId as string

    class Meta:
        verbose_name = 'Wallpaper Interaction'
        verbose_name_plural = 'Wallpaper Interactions'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'wallpaper']),
            models.Index(fields=['interaction_type']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_interaction_type_display()} - {self.wallpaper.title}"

    @classmethod
    def record_interaction(cls, user, wallpaper, interaction_type, request=None, **kwargs):
        """Record a user interaction with a wallpaper"""
        if not user or not user.is_authenticated:
            return None

        # Create the interaction
        interaction = cls(
            user=user,
            wallpaper=wallpaper,
            interaction_type=interaction_type,
            **kwargs
        )

        # If request is provided, extract additional information
        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                interaction.ip_address = x_forwarded_for.split(',')[0]
            else:
                interaction.ip_address = request.META.get('REMOTE_ADDR')

            # Get user agent
            interaction.user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Determine device type (simplified)
            user_agent = interaction.user_agent.lower()
            if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
                interaction.device_type = 'mobile'
            elif 'tablet' in user_agent or 'ipad' in user_agent:
                interaction.device_type = 'tablet'
            else:
                interaction.device_type = 'desktop'

            # Get session ID
            interaction.session_id = request.session.session_key or ''

            # Get referrer
            interaction.referrer = request.META.get('HTTP_REFERER', '')

        # Save the interaction
        interaction.save()

        # Update the wallpaper statistics based on interaction type
        if interaction_type == 'view':
            wallpaper.increment_view(user)
        elif interaction_type == 'like':
            if user not in wallpaper.liked_by_users.all():
                wallpaper.liked_by_users.add(user)
                wallpaper.likes += 1
                wallpaper.save(update_fields=['likes'])
        elif interaction_type == 'unlike':
            if user in wallpaper.liked_by_users.all():
                wallpaper.liked_by_users.remove(user)
                wallpaper.likes -= 1
                wallpaper.save(update_fields=['likes'])
        elif interaction_type == 'download':
            wallpaper.increment_download(user)
        elif interaction_type == 'save':
            if user not in wallpaper.saved_by_users.all():
                wallpaper.saved_by_users.add(user)
        elif interaction_type == 'unsave':
            if user in wallpaper.saved_by_users.all():
                wallpaper.saved_by_users.remove(user)
        elif interaction_type == 'share':
            wallpaper.increment_share(user)

        return interaction

    def sync_to_mongodb(self):
        """Sync this interaction to MongoDB"""
        from pymongo import MongoClient
        from bson.objectid import ObjectId

        # Get MongoDB connection
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']

            # Ensure the interactions collection exists
            if 'wallpaper_interactions' not in db.list_collection_names():
                db.create_collection('wallpaper_interactions')

            interactions = db.wallpaper_interactions
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

        # Prepare data for MongoDB
        mongo_data = {
            'user_id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'wallpaper_id': str(self.wallpaper.id),
            'wallpaper_title': self.wallpaper.title,
            'interaction_type': self.interaction_type,
            'timestamp': self.timestamp,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_type': self.device_type,
            'session_id': self.session_id,
            'share_platform': self.share_platform,
            'referrer': self.referrer,
            'duration': self.duration
        }

        # If the wallpaper has a MongoDB ID, include it
        if self.wallpaper.mongo_id:
            mongo_data['wallpaper_mongo_id'] = self.wallpaper.mongo_id

        # If we have a mongo_id, update the existing document
        if self.mongo_id:
            try:
                result = interactions.update_one(
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
                result = interactions.insert_one(mongo_data)
                self.mongo_id = str(result.inserted_id)
                self.save(update_fields=['mongo_id'])
                return True
            except Exception as e:
                print(f"Error inserting MongoDB document: {e}")
                return False


# Signal handlers moved to signals.py


# Collection and Comment will be defined later in this file

# User methods for interaction statistics
def get_user_interaction_stats(user):
    """Get statistics about a user's interactions with wallpapers"""
    if not user or not user.is_authenticated:
        return {}

    # Get all interactions for this user
    interactions = WallpaperInteraction.objects.filter(user=user)

    # Count by interaction type
    interaction_counts = {}
    for interaction_type, _ in WallpaperInteraction.INTERACTION_TYPES:
        interaction_counts[interaction_type] = interactions.filter(interaction_type=interaction_type).count()

    # Get most recent interactions
    recent_interactions = interactions.order_by('-timestamp')[:10]

    # Get most interacted wallpapers
    from django.db.models import Count
    most_interacted = WallpaperInteraction.objects.filter(user=user)\
        .values('wallpaper')\
        .annotate(interaction_count=Count('wallpaper'))\
        .order_by('-interaction_count')[:5]

    most_interacted_wallpapers = []
    for item in most_interacted:
        try:
            wallpaper = Wallpaper.objects.get(id=item['wallpaper'])
            most_interacted_wallpapers.append({
                'wallpaper': wallpaper,
                'count': item['interaction_count']
            })
        except Wallpaper.DoesNotExist:
            pass

    # Get device statistics
    device_stats = {
        'mobile': interactions.filter(device_type='mobile').count(),
        'tablet': interactions.filter(device_type='tablet').count(),
        'desktop': interactions.filter(device_type='desktop').count(),
    }

    # Get time-based statistics
    from django.utils import timezone
    from datetime import timedelta

    # Last 7 days
    last_week = timezone.now() - timedelta(days=7)
    interactions_last_week = interactions.filter(timestamp__gte=last_week)

    # Last 30 days
    last_month = timezone.now() - timedelta(days=30)
    interactions_last_month = interactions.filter(timestamp__gte=last_month)

    # Daily interactions for the last 30 days
    daily_interactions = {}
    for i in range(30):
        day = timezone.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        count = interactions.filter(timestamp__range=(day_start, day_end)).count()
        daily_interactions[day.strftime('%Y-%m-%d')] = count

    return {
        'total_interactions': interactions.count(),
        'interaction_counts': interaction_counts,
        'recent_interactions': recent_interactions,
        'most_interacted_wallpapers': most_interacted_wallpapers,
        'device_stats': device_stats,
        'interactions_last_week': interactions_last_week.count(),
        'interactions_last_month': interactions_last_month.count(),
        'daily_interactions': daily_interactions
    }


class Collection(models.Model):
    """Model for users to organize wallpapers into collections/groups"""
    # Collection types
    PRIVACY_CHOICES = [
        ('public', 'Public'),      # Visible to everyone
        ('unlisted', 'Unlisted'),  # Only accessible with direct link
        ('private', 'Private'),    # Only visible to the owner
    ]

    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Cover image (can be one of the wallpapers or a custom image)
    cover_image = models.ForeignKey(Wallpaper, on_delete=models.SET_NULL, null=True, blank=True, related_name='cover_for_collections')
    custom_cover_url = models.URLField(max_length=500, blank=True)  # Custom cover image URL

    # Relationships
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    wallpapers = models.ManyToManyField(Wallpaper, related_name='collections', blank=True)

    # Settings
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='private')
    featured = models.BooleanField(default=False)  # Featured on the site

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_modified_at = models.DateTimeField(auto_now=True)  # When wallpapers were last added/removed
    view_count = models.PositiveIntegerField(default=0)  # How many times the collection has been viewed

    # Sorting
    sort_order = models.CharField(max_length=20, default='date_added', choices=[
        ('date_added', 'Date Added'),
        ('date_added_reverse', 'Date Added (Reverse)'),
        ('title', 'Title'),
        ('popularity', 'Popularity'),
        ('custom', 'Custom Order'),
    ])

    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)  # Store MongoDB ObjectId as string

    class Meta:
        verbose_name = 'Collection'
        verbose_name_plural = 'Collections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['privacy']),
            models.Index(fields=['featured']),
        ]
        unique_together = [('owner', 'name')]  # A user can't have two collections with the same name

    def __str__(self):
        return f"{self.name} by {self.owner.username}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collection_detail', args=[str(self.id)])

    def get_cover_image_url(self):
        """Return the URL for the collection's cover image"""
        if self.custom_cover_url:
            return self.custom_cover_url
        elif self.cover_image:
            return self.cover_image.get_image_url()
        elif self.wallpapers.exists():
            # Use the first wallpaper as the cover if no specific cover is set
            return self.wallpapers.first().get_image_url()
        return ''  # Default empty URL if no cover image is available

    def add_wallpaper(self, wallpaper):
        """Add a wallpaper to the collection"""
        if not isinstance(wallpaper, Wallpaper):
            return False

        if wallpaper not in self.wallpapers.all():
            self.wallpapers.add(wallpaper)
            self.last_modified_at = timezone.now()
            self.save(update_fields=['last_modified_at'])
            return True
        return False

    def remove_wallpaper(self, wallpaper):
        """Remove a wallpaper from the collection"""
        if not isinstance(wallpaper, Wallpaper):
            return False

        if wallpaper in self.wallpapers.all():
            self.wallpapers.remove(wallpaper)

            # If this was the cover image, reset it
            if self.cover_image == wallpaper:
                self.cover_image = None
                if self.wallpapers.exists():
                    self.cover_image = self.wallpapers.first()

            self.last_modified_at = timezone.now()
            self.save(update_fields=['cover_image', 'last_modified_at'])
            return True
        return False

    def set_cover_image(self, wallpaper=None, custom_url=None):
        """Set the cover image for the collection"""
        if wallpaper and isinstance(wallpaper, Wallpaper):
            # Make sure the wallpaper is in the collection
            if wallpaper not in self.wallpapers.all():
                self.wallpapers.add(wallpaper)

            self.cover_image = wallpaper
            self.custom_cover_url = ''
            self.save(update_fields=['cover_image', 'custom_cover_url'])
            return True
        elif custom_url:
            self.cover_image = None
            self.custom_cover_url = custom_url
            self.save(update_fields=['cover_image', 'custom_cover_url'])
            return True
        return False

    def increment_view_count(self):
        """Increment the view count for this collection"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def get_wallpaper_count(self):
        """Get the number of wallpapers in this collection"""
        return self.wallpapers.count()

    def is_visible_to(self, user):
        """Check if the collection is visible to a specific user"""
        # Owner can always see their own collections
        if user == self.owner:
            return True

        # Public collections are visible to everyone
        if self.privacy == 'public':
            return True

        # Unlisted collections are visible to everyone with the link
        if self.privacy == 'unlisted':
            return True

        # Private collections are only visible to the owner
        return False

    def sync_to_mongodb(self):
        """Sync this collection to MongoDB"""
        from pymongo import MongoClient
        from bson.objectid import ObjectId

        # Get MongoDB connection
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']

            # Ensure the collections collection exists
            if 'collections' not in db.list_collection_names():
                db.create_collection('collections')

            collections = db.collections
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

        # Get wallpaper IDs
        wallpaper_ids = [str(w.id) for w in self.wallpapers.all()]

        # Prepare data for MongoDB
        mongo_data = {
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner.id,
            'owner_username': self.owner.username,
            'owner_email': self.owner.email,
            'privacy': self.privacy,
            'featured': self.featured,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_modified_at': self.last_modified_at,
            'view_count': self.view_count,
            'sort_order': self.sort_order,
            'wallpaper_ids': wallpaper_ids,
            'wallpaper_count': len(wallpaper_ids)
        }

        # Add cover image information
        if self.cover_image:
            mongo_data['cover_image_id'] = str(self.cover_image.id)
            if self.cover_image.mongo_id:
                mongo_data['cover_image_mongo_id'] = self.cover_image.mongo_id

        if self.custom_cover_url:
            mongo_data['custom_cover_url'] = self.custom_cover_url

        # If we have a mongo_id, update the existing document
        if self.mongo_id:
            try:
                result = collections.update_one(
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
                result = collections.insert_one(mongo_data)
                self.mongo_id = str(result.inserted_id)
                self.save(update_fields=['mongo_id'])
                return True
            except Exception as e:
                print(f"Error inserting MongoDB document: {e}")
                return False

    @classmethod
    def sync_from_mongodb(cls, mongo_collection, owner=None):
        """Create or update a Django Collection model from MongoDB data"""
        from bson.objectid import ObjectId

        # Check if we already have this collection in Django
        mongo_id = str(mongo_collection.get('_id'))
        collection = None

        try:
            # Try to find by MongoDB ID
            collection = cls.objects.get(mongo_id=mongo_id)
        except cls.DoesNotExist:
            # If not found, create a new one
            collection = cls()
            collection.mongo_id = mongo_id

        # Update fields from MongoDB data
        collection.name = mongo_collection.get('name', 'Untitled Collection')
        collection.description = mongo_collection.get('description', '')

        # Handle owner
        if owner:
            collection.owner = owner
        else:
            # Try to find the owner by ID
            owner_id = mongo_collection.get('owner_id')
            if owner_id:
                try:
                    collection.owner = User.objects.get(id=owner_id)
                except User.DoesNotExist:
                    # Cannot create a collection without an owner
                    return None

        # Update settings
        collection.privacy = mongo_collection.get('privacy', 'private')
        collection.featured = mongo_collection.get('featured', False)
        collection.sort_order = mongo_collection.get('sort_order', 'date_added')
        collection.view_count = mongo_collection.get('view_count', 0)

        # Handle timestamps
        if 'created_at' in mongo_collection:
            # Convert string to datetime if needed
            created_at = mongo_collection['created_at']
            if isinstance(created_at, str):
                from dateutil import parser
                try:
                    collection.created_at = parser.parse(created_at)
                except:
                    pass
            elif hasattr(created_at, 'strftime'):  # It's already a datetime
                collection.created_at = created_at

        if 'last_modified_at' in mongo_collection:
            # Convert string to datetime if needed
            last_modified_at = mongo_collection['last_modified_at']
            if isinstance(last_modified_at, str):
                from dateutil import parser
                try:
                    collection.last_modified_at = parser.parse(last_modified_at)
                except:
                    pass
            elif hasattr(last_modified_at, 'strftime'):  # It's already a datetime
                collection.last_modified_at = last_modified_at

        # Save the collection first so we can add wallpapers
        collection.save()

        # Handle wallpapers
        wallpaper_ids = mongo_collection.get('wallpaper_ids', [])
        if wallpaper_ids:
            # Clear existing wallpapers
            collection.wallpapers.clear()

            # Add wallpapers from IDs
            for wallpaper_id in wallpaper_ids:
                try:
                    wallpaper = Wallpaper.objects.get(id=wallpaper_id)
                    collection.wallpapers.add(wallpaper)
                except Wallpaper.DoesNotExist:
                    pass

        # Handle cover image
        cover_image_id = mongo_collection.get('cover_image_id')
        if cover_image_id:
            try:
                cover_image = Wallpaper.objects.get(id=cover_image_id)
                collection.cover_image = cover_image
                collection.save(update_fields=['cover_image'])
            except Wallpaper.DoesNotExist:
                pass

        # Handle custom cover URL
        custom_cover_url = mongo_collection.get('custom_cover_url')
        if custom_cover_url:
            collection.custom_cover_url = custom_cover_url
            collection.save(update_fields=['custom_cover_url'])

        return collection


def get_wallpaper_interaction_stats(wallpaper):
    """Get statistics about interactions with a specific wallpaper"""
    if not wallpaper or not isinstance(wallpaper, Wallpaper):
        return {}

    # Get all interactions for this wallpaper
    interactions = WallpaperInteraction.objects.filter(wallpaper=wallpaper)

    # Count by interaction type
    interaction_counts = {}
    for interaction_type, _ in WallpaperInteraction.INTERACTION_TYPES:
        interaction_counts[interaction_type] = interactions.filter(interaction_type=interaction_type).count()

    # Get most recent interactions
    recent_interactions = interactions.order_by('-timestamp')[:10]

    # Get top users who interacted with this wallpaper
    from django.db.models import Count
    top_users = WallpaperInteraction.objects.filter(wallpaper=wallpaper)\
        .values('user')\
        .annotate(interaction_count=Count('user'))\
        .order_by('-interaction_count')[:5]

    top_interacting_users = []
    for item in top_users:
        try:
            user = User.objects.get(id=item['user'])
            top_interacting_users.append({
                'user': user,
                'count': item['interaction_count']
            })
        except User.DoesNotExist:
            pass

    # Get device statistics
    device_stats = {
        'mobile': interactions.filter(device_type='mobile').count(),
        'tablet': interactions.filter(device_type='tablet').count(),
        'desktop': interactions.filter(device_type='desktop').count(),
    }

    # Get time-based statistics
    from django.utils import timezone
    from datetime import timedelta

    # Last 7 days
    last_week = timezone.now() - timedelta(days=7)
    interactions_last_week = interactions.filter(timestamp__gte=last_week)

    # Last 30 days
    last_month = timezone.now() - timedelta(days=30)
    interactions_last_month = interactions.filter(timestamp__gte=last_month)

    # Daily interactions for the last 30 days
    daily_interactions = {}
    for i in range(30):
        day = timezone.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        count = interactions.filter(timestamp__range=(day_start, day_end)).count()
        daily_interactions[day.strftime('%Y-%m-%d')] = count

    # Get referrer statistics
    referrer_stats = {}
    for interaction in interactions.exclude(referrer=''):
        referrer = interaction.referrer
        # Extract domain from referrer
        from urllib.parse import urlparse
        try:
            domain = urlparse(referrer).netloc
            if domain:
                referrer_stats[domain] = referrer_stats.get(domain, 0) + 1
        except:
            pass

    # Get share platform statistics
    share_stats = {}
    for interaction in interactions.filter(interaction_type='share').exclude(share_platform=''):
        platform = interaction.share_platform
        share_stats[platform] = share_stats.get(platform, 0) + 1

    return {
        'total_interactions': interactions.count(),
        'interaction_counts': interaction_counts,
        'recent_interactions': recent_interactions,
        'top_interacting_users': top_interacting_users,
        'device_stats': device_stats,
        'interactions_last_week': interactions_last_week.count(),
        'interactions_last_month': interactions_last_month.count(),
        'daily_interactions': daily_interactions,
        'referrer_stats': referrer_stats,
        'share_stats': share_stats
    }


def get_user_collections(user, include_private=True):
    """Get collections for a specific user"""
    if not user or not user.is_authenticated:
        # For anonymous users, only return public featured collections
        return Collection.objects.filter(privacy='public', featured=True)

    # For authenticated users, return their own collections and public collections
    if include_private:
        # Include all of the user's collections
        user_collections = Collection.objects.filter(owner=user)
    else:
        # Only include public and unlisted collections
        user_collections = Collection.objects.filter(owner=user).exclude(privacy='private')

    # Get public collections from other users
    public_collections = Collection.objects.filter(privacy='public').exclude(owner=user)

    # Combine the querysets
    return (user_collections | public_collections).distinct().order_by('-created_at')


def get_collection_stats(collection):
    """Get statistics about a collection"""
    if not collection or not isinstance(collection, Collection):
        return {}

    # Get basic stats
    wallpaper_count = collection.wallpapers.count()
    total_views = collection.wallpapers.aggregate(total_views=models.Sum('views'))['total_views'] or 0
    total_likes = collection.wallpapers.aggregate(total_likes=models.Sum('likes'))['total_likes'] or 0
    total_downloads = collection.wallpapers.aggregate(total_downloads=models.Sum('downloads'))['total_downloads'] or 0

    # Get category distribution
    categories = {}
    for wallpaper in collection.wallpapers.all():
        if wallpaper.category:
            categories[wallpaper.category] = categories.get(wallpaper.category, 0) + 1

    # Get tag distribution
    tags = {}
    for wallpaper in collection.wallpapers.all():
        if wallpaper.tags:
            for tag in wallpaper.tags.split(','):
                tag = tag.strip()
                if tag:
                    tags[tag] = tags.get(tag, 0) + 1

    # Sort categories and tags by count
    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:20]  # Limit to top 20 tags

    # Get most viewed wallpapers in the collection
    most_viewed = collection.wallpapers.order_by('-views')[:5]

    # Get most liked wallpapers in the collection
    most_liked = collection.wallpapers.order_by('-likes')[:5]

    # Get most downloaded wallpapers in the collection
    most_downloaded = collection.wallpapers.order_by('-downloads')[:5]

    return {
        'wallpaper_count': wallpaper_count,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_downloads': total_downloads,
        'categories': sorted_categories,
        'tags': sorted_tags,
        'most_viewed': most_viewed,
        'most_liked': most_liked,
        'most_downloaded': most_downloaded,
        'collection_views': collection.view_count
    }


class Comment(models.Model):
    """Model for wallpaper discussions and comments"""
    # Status choices for moderation
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
    ]

    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()

    # Relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    wallpaper = models.ForeignKey(Wallpaper, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    edited = models.BooleanField(default=False)  # Flag to indicate if the comment was edited

    # Moderation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_comments')
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_reason = models.TextField(blank=True)  # Reason for rejection or flagging

    # Engagement
    likes = models.PositiveIntegerField(default=0)
    liked_by = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    # IP and device tracking for moderation purposes
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)  # Store MongoDB ObjectId as string

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallpaper']),
            models.Index(fields=['author']),
            models.Index(fields=['parent']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.author.username}'s comment on {self.wallpaper.title}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('wallpaper_detail', args=[str(self.wallpaper.id)]) + f'#comment-{self.id}'

    def toggle_like(self, user):
        """Toggle like status for a user"""
        if not user or not user.is_authenticated:
            return False

        if user in self.liked_by.all():
            # User already liked this comment, so unlike it
            self.liked_by.remove(user)
            self.likes -= 1
            liked = False
        else:
            # User hasn't liked this comment yet, so like it
            self.liked_by.add(user)
            self.likes += 1
            liked = True

        self.save(update_fields=['likes'])
        return liked

    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent is not None

    def get_reply_count(self):
        """Get the number of replies to this comment"""
        return self.replies.count()

    def get_all_replies(self):
        """Get all replies to this comment, ordered by creation time"""
        return self.replies.filter(status='approved').order_by('created_at')

    def edit(self, new_content):
        """Edit the comment content"""
        if new_content and new_content != self.content:
            self.content = new_content
            self.edited = True
            self.updated_at = timezone.now()
            self.save(update_fields=['content', 'edited', 'updated_at'])
            return True
        return False

    def moderate(self, status, moderator=None, reason=''):
        """Moderate the comment (approve, reject, flag)"""
        if status not in [choice[0] for choice in self.STATUS_CHOICES]:
            return False

        self.status = status
        self.moderation_reason = reason

        if moderator and moderator.is_authenticated:
            self.moderated_by = moderator

        self.moderated_at = timezone.now()
        self.save(update_fields=['status', 'moderation_reason', 'moderated_by', 'moderated_at'])
        return True

    def report(self, reporter, reason=''):
        """Report the comment for moderation"""
        # Flag the comment
        self.status = 'flagged'
        self.moderation_reason = reason
        self.save(update_fields=['status', 'moderation_reason'])

        # Create a CommentReport object
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.contenttypes.fields import GenericForeignKey

        # This would be implemented if we had a separate CommentReport model
        # For now, we'll just flag the comment

        return True

    def sync_to_mongodb(self):
        """Sync this comment to MongoDB"""
        from pymongo import MongoClient
        from bson.objectid import ObjectId

        # Get MongoDB connection
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']

            # Ensure the comments collection exists
            if 'comments' not in db.list_collection_names():
                db.create_collection('comments')

            comments = db.comments
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

        # Prepare data for MongoDB
        mongo_data = {
            'content': self.content,
            'author_id': self.author.id,
            'author_username': self.author.username,
            'wallpaper_id': str(self.wallpaper.id),
            'wallpaper_title': self.wallpaper.title,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'edited': self.edited,
            'status': self.status,
            'likes': self.likes,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

        # Add parent comment ID if this is a reply
        if self.parent:
            mongo_data['parent_id'] = str(self.parent.id)
            if self.parent.mongo_id:
                mongo_data['parent_mongo_id'] = self.parent.mongo_id

        # Add wallpaper MongoDB ID if available
        if self.wallpaper.mongo_id:
            mongo_data['wallpaper_mongo_id'] = self.wallpaper.mongo_id

        # Add moderation data if available
        if self.moderated_by:
            mongo_data['moderated_by_id'] = self.moderated_by.id
            mongo_data['moderated_by_username'] = self.moderated_by.username
            mongo_data['moderated_at'] = self.moderated_at
            mongo_data['moderation_reason'] = self.moderation_reason

        # If we have a mongo_id, update the existing document
        if self.mongo_id:
            try:
                result = comments.update_one(
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
                result = comments.insert_one(mongo_data)
                self.mongo_id = str(result.inserted_id)
                self.save(update_fields=['mongo_id'])
                return True
            except Exception as e:
                print(f"Error inserting MongoDB document: {e}")
                return False

    @classmethod
    def sync_from_mongodb(cls, mongo_comment):
        """Create or update a Django Comment model from MongoDB data"""
        from bson.objectid import ObjectId

        # Check if we already have this comment in Django
        mongo_id = str(mongo_comment.get('_id'))
        comment = None

        try:
            # Try to find by MongoDB ID
            comment = cls.objects.get(mongo_id=mongo_id)
        except cls.DoesNotExist:
            # If not found, create a new one
            comment = cls()
            comment.mongo_id = mongo_id

        # Get required related objects
        try:
            # Get author
            author_id = mongo_comment.get('author_id')
            if author_id:
                try:
                    author = User.objects.get(id=author_id)
                    comment.author = author
                except User.DoesNotExist:
                    # Cannot create a comment without an author
                    return None
            else:
                # Cannot create a comment without an author
                return None

            # Get wallpaper
            wallpaper_id = mongo_comment.get('wallpaper_id')
            wallpaper_mongo_id = mongo_comment.get('wallpaper_mongo_id')

            wallpaper = None
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
                # Cannot create a comment without a wallpaper
                return None

            comment.wallpaper = wallpaper

            # Get parent comment if this is a reply
            parent_id = mongo_comment.get('parent_id')
            parent_mongo_id = mongo_comment.get('parent_mongo_id')

            if parent_id or parent_mongo_id:
                parent = None

                if parent_id:
                    try:
                        parent = cls.objects.get(id=parent_id)
                    except cls.DoesNotExist:
                        pass

                if not parent and parent_mongo_id:
                    try:
                        parent = cls.objects.get(mongo_id=parent_mongo_id)
                    except cls.DoesNotExist:
                        pass

                if parent:
                    comment.parent = parent
        except Exception as e:
            print(f"Error getting related objects for comment: {e}")
            return None

        # Update fields from MongoDB data
        comment.content = mongo_comment.get('content', '')
        comment.status = mongo_comment.get('status', 'approved')
        comment.likes = mongo_comment.get('likes', 0)
        comment.edited = mongo_comment.get('edited', False)
        comment.ip_address = mongo_comment.get('ip_address')
        comment.user_agent = mongo_comment.get('user_agent', '')

        # Handle timestamps
        if 'created_at' in mongo_comment:
            # Convert string to datetime if needed
            created_at = mongo_comment['created_at']
            if isinstance(created_at, str):
                from dateutil import parser
                try:
                    comment.created_at = parser.parse(created_at)
                except:
                    pass
            elif hasattr(created_at, 'strftime'):  # It's already a datetime
                comment.created_at = created_at

        if 'updated_at' in mongo_comment:
            # Convert string to datetime if needed
            updated_at = mongo_comment['updated_at']
            if isinstance(updated_at, str):
                from dateutil import parser
                try:
                    comment.updated_at = parser.parse(updated_at)
                except:
                    pass
            elif hasattr(updated_at, 'strftime'):  # It's already a datetime
                comment.updated_at = updated_at

        # Handle moderation data
        if 'moderated_by_id' in mongo_comment:
            try:
                moderator = User.objects.get(id=mongo_comment['moderated_by_id'])
                comment.moderated_by = moderator
            except User.DoesNotExist:
                pass

        if 'moderated_at' in mongo_comment:
            # Convert string to datetime if needed
            moderated_at = mongo_comment['moderated_at']
            if isinstance(moderated_at, str):
                from dateutil import parser
                try:
                    comment.moderated_at = parser.parse(moderated_at)
                except:
                    pass
            elif hasattr(moderated_at, 'strftime'):  # It's already a datetime
                comment.moderated_at = moderated_at

        comment.moderation_reason = mongo_comment.get('moderation_reason', '')

        # Save the comment
        comment.save()

        return comment


def create_comment(user, wallpaper, content, parent=None, request=None):
    """Create a new comment on a wallpaper"""
    if not user or not user.is_authenticated:
        return None, 'You must be logged in to comment'

    if not wallpaper or not isinstance(wallpaper, Wallpaper):
        return None, 'Invalid wallpaper'

    if not content or not content.strip():
        return None, 'Comment cannot be empty'

    # Create the comment
    comment = Comment(
        author=user,
        wallpaper=wallpaper,
        content=content.strip(),
        status='approved'  # Default to approved, can be changed based on moderation settings
    )

    # If this is a reply, set the parent
    if parent and isinstance(parent, Comment):
        # Make sure the parent comment is for the same wallpaper
        if parent.wallpaper != wallpaper:
            return None, 'Parent comment is for a different wallpaper'

        comment.parent = parent

    # If request is provided, extract IP and user agent
    if request:
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            comment.ip_address = x_forwarded_for.split(',')[0]
        else:
            comment.ip_address = request.META.get('REMOTE_ADDR')

        # Get user agent
        comment.user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Save the comment
    comment.save()

    return comment, 'Comment posted successfully'


def get_wallpaper_comments(wallpaper, include_replies=False, status='approved'):
    """Get comments for a wallpaper"""
    if not wallpaper or not isinstance(wallpaper, Wallpaper):
        return []

    # Get base query for comments on this wallpaper with the specified status
    comments_query = Comment.objects.filter(wallpaper=wallpaper, status=status)

    if include_replies:
        # Return all comments, including replies
        return comments_query.order_by('-created_at')
    else:
        # Return only top-level comments (not replies)
        return comments_query.filter(parent=None).order_by('-created_at')


def get_comment_replies(comment, status='approved'):
    """Get replies to a specific comment"""
    if not comment or not isinstance(comment, Comment):
        return []

    return Comment.objects.filter(parent=comment, status=status).order_by('created_at')


def get_user_comments(user, limit=None):
    """Get comments made by a specific user"""
    if not user or not user.is_authenticated:
        return []

    comments = Comment.objects.filter(author=user).order_by('-created_at')

    if limit:
        return comments[:limit]
    return comments


def get_popular_tags(limit=20):
    """Get the most popular tags based on usage count"""
    return Tag.objects.order_by('-usage_count')[:limit]


def get_trending_tags(limit=20):
    """Get trending tags based on search count"""
    return Tag.objects.order_by('-search_count')[:limit]


def search_tags(query, limit=20):
    """Search for tags by name or description"""
    from django.db.models import Q

    if not query:
        return Tag.objects.none()

    return Tag.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    ).order_by('-usage_count')[:limit]


def add_to_collection(user, wallpaper, collection_name=None, collection_id=None, create_if_not_exists=True):
    """Add a wallpaper to a user's collection"""
    if not user or not user.is_authenticated or not wallpaper or not isinstance(wallpaper, Wallpaper):
        return None, 'Invalid user or wallpaper'

    collection = None

    # Try to find the collection by ID if provided
    if collection_id:
        try:
            collection = Collection.objects.get(id=collection_id, owner=user)
        except Collection.DoesNotExist:
            return None, f'Collection with ID {collection_id} not found'

    # Try to find the collection by name if provided
    elif collection_name:
        try:
            collection = Collection.objects.get(name=collection_name, owner=user)
        except Collection.DoesNotExist:
            # Create a new collection if requested
            if create_if_not_exists:
                collection = Collection(
                    name=collection_name,
                    owner=user,
                    privacy='private'  # Default to private for new collections
                )
                collection.save()
            else:
                return None, f'Collection "{collection_name}" not found'

    # If no collection was found or created, return an error
    if not collection:
        return None, 'No collection specified'

    # Add the wallpaper to the collection
    if wallpaper not in collection.wallpapers.all():
        collection.wallpapers.add(wallpaper)
        collection.last_modified_at = timezone.now()

        # If this is the first wallpaper, set it as the cover image
        if collection.wallpapers.count() == 1 and not collection.cover_image and not collection.custom_cover_url:
            collection.cover_image = wallpaper

        collection.save()
        return collection, f'Added to collection "{collection.name}"'
    else:
        return collection, f'Already in collection "{collection.name}"'


# Signal handlers moved to signals.py
