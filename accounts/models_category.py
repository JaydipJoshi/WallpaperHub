from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from pymongo import MongoClient
from bson.objectid import ObjectId

class Category(models.Model):
    """Model for wallpaper categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Display settings
    icon = models.CharField(max_length=100, blank=True)  # Font Awesome icon name or similar
    color = models.CharField(max_length=20, blank=True)  # Hex color code or color name
    
    # Cover image
    cover_image_url = models.URLField(max_length=500, blank=True)
    
    # Ordering
    display_order = models.PositiveIntegerField(default=0)  # Lower numbers appear first
    
    # Statistics
    wallpaper_count = models.PositiveIntegerField(default=0)  # Number of wallpapers in this category
    view_count = models.PositiveIntegerField(default=0)  # Number of times this category has been viewed
    
    # Featured status
    is_featured = models.BooleanField(default=False)  # Whether this category is featured on the homepage
    featured_at = models.DateTimeField(null=True, blank=True)  # When this category was featured
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # MongoDB integration
    mongo_id = models.CharField(max_length=24, blank=True)  # Store MongoDB ObjectId as string
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['display_order']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Generate slug from name if not provided
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Update featured_at timestamp if featured status changes
        if self.is_featured and not self.featured_at:
            self.featured_at = timezone.now()
        elif not self.is_featured and self.featured_at:
            self.featured_at = None
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('category_detail', args=[str(self.slug)])
    
    def get_wallpapers(self):
        """Get all wallpapers in this category"""
        from .models import Wallpaper
        return Wallpaper.objects.filter(category_obj=self)
    
    def update_wallpaper_count(self):
        """Update the wallpaper count based on actual wallpaper count"""
        from .models import Wallpaper
        self.wallpaper_count = Wallpaper.objects.filter(category_obj=self).count()
        self.save(update_fields=['wallpaper_count'])
    
    def increment_view_count(self):
        """Increment the view count for this category"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def toggle_featured(self):
        """Toggle the featured status of this category"""
        self.is_featured = not self.is_featured
        self.save()
        return self.is_featured
    
    def sync_to_mongodb(self):
        """Sync this category to MongoDB"""
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            
            # Ensure the categories collection exists
            if 'categories' not in db.list_collection_names():
                db.create_collection('categories')
                
            categories = db.categories
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None
        
        # Prepare data for MongoDB
        mongo_data = {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'cover_image_url': self.cover_image_url,
            'display_order': self.display_order,
            'wallpaper_count': self.wallpaper_count,
            'view_count': self.view_count,
            'is_featured': self.is_featured,
            'featured_at': self.featured_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # If we have a mongo_id, update the existing document
        if self.mongo_id:
            try:
                result = categories.update_one(
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
                result = categories.insert_one(mongo_data)
                self.mongo_id = str(result.inserted_id)
                self.save(update_fields=['mongo_id'])
                return True
            except Exception as e:
                print(f"Error inserting MongoDB document: {e}")
                return False
    
    @classmethod
    def sync_from_mongodb(cls, mongo_category):
        """Create or update a Django Category model from MongoDB data"""
        # Check if we already have this category in Django
        mongo_id = str(mongo_category.get('_id'))
        category = None
        
        try:
            # Try to find by MongoDB ID
            category = cls.objects.get(mongo_id=mongo_id)
        except cls.DoesNotExist:
            # If not found by mongo_id, try to find by name or slug
            name = mongo_category.get('name')
            slug = mongo_category.get('slug')
            
            if name:
                try:
                    category = cls.objects.get(name=name)
                except cls.DoesNotExist:
                    pass
                    
            if not category and slug:
                try:
                    category = cls.objects.get(slug=slug)
                except cls.DoesNotExist:
                    pass
        
        # If not found, create a new one
        if not category:
            category = cls()
            category.mongo_id = mongo_id
        
        # Update fields from MongoDB data
        category.name = mongo_category.get('name', 'Unnamed Category')
        category.slug = mongo_category.get('slug', slugify(category.name))
        category.description = mongo_category.get('description', '')
        category.icon = mongo_category.get('icon', '')
        category.color = mongo_category.get('color', '')
        category.cover_image_url = mongo_category.get('cover_image_url', '')
        category.display_order = mongo_category.get('display_order', 0)
        category.wallpaper_count = mongo_category.get('wallpaper_count', 0)
        category.view_count = mongo_category.get('view_count', 0)
        category.is_featured = mongo_category.get('is_featured', False)
        
        # Handle timestamps
        if 'featured_at' in mongo_category and mongo_category['featured_at']:
            # Convert string to datetime if needed
            featured_at = mongo_category['featured_at']
            if isinstance(featured_at, str):
                from dateutil import parser
                try:
                    category.featured_at = parser.parse(featured_at)
                except:
                    pass
            elif hasattr(featured_at, 'strftime'):  # It's already a datetime
                category.featured_at = featured_at
        
        if 'created_at' in mongo_category:
            # Convert string to datetime if needed
            created_at = mongo_category['created_at']
            if isinstance(created_at, str):
                from dateutil import parser
                try:
                    category.created_at = parser.parse(created_at)
                except:
                    pass
            elif hasattr(created_at, 'strftime'):  # It's already a datetime
                category.created_at = created_at
        
        # Save the category
        category.save()
        
        return category


# Default categories to create
DEFAULT_CATEGORIES = [
    {
        'name': 'Abstract',
        'description': 'Abstract and geometric wallpapers',
        'icon': 'fa-shapes',
        'color': '#FF5733',
        'is_featured': True,
        'display_order': 1
    },
    {
        'name': 'Nature',
        'description': 'Beautiful landscapes, plants, and animals',
        'icon': 'fa-leaf',
        'color': '#33FF57',
        'is_featured': True,
        'display_order': 2
    },
    {
        'name': 'City',
        'description': 'Urban landscapes and cityscapes',
        'icon': 'fa-city',
        'color': '#3357FF',
        'is_featured': True,
        'display_order': 3
    },
    {
        'name': 'Space',
        'description': 'Galaxies, stars, and cosmic scenes',
        'icon': 'fa-star',
        'color': '#5733FF',
        'is_featured': True,
        'display_order': 4
    },
    {
        'name': 'Minimal',
        'description': 'Clean, simple, and minimalist designs',
        'icon': 'fa-minus',
        'color': '#FFFFFF',
        'is_featured': True,
        'display_order': 5
    },
    {
        'name': 'Neon',
        'description': 'Bright, colorful, and glowing designs',
        'icon': 'fa-lightbulb',
        'color': '#FF33F5',
        'is_featured': True,
        'display_order': 6
    },
    {
        'name': 'Landscape',
        'description': 'Beautiful natural landscapes',
        'icon': 'fa-mountain',
        'color': '#33FFF5',
        'is_featured': True,
        'display_order': 7
    },
    {
        'name': 'Sunset',
        'description': 'Beautiful sunset and sunrise scenes',
        'icon': 'fa-sun',
        'color': '#FFA500',
        'is_featured': True,
        'display_order': 8
    },
    {
        'name': 'Animals',
        'description': 'Cute and majestic animals',
        'icon': 'fa-paw',
        'color': '#8B4513',
        'is_featured': False,
        'display_order': 9
    },
    {
        'name': 'Technology',
        'description': 'Gadgets, computers, and tech-related wallpapers',
        'icon': 'fa-laptop',
        'color': '#808080',
        'is_featured': False,
        'display_order': 10
    },
    {
        'name': 'Art',
        'description': 'Artistic and creative wallpapers',
        'icon': 'fa-palette',
        'color': '#800080',
        'is_featured': False,
        'display_order': 11
    },
    {
        'name': 'Anime',
        'description': 'Anime and manga-inspired wallpapers',
        'icon': 'fa-user-ninja',
        'color': '#FF69B4',
        'is_featured': False,
        'display_order': 12
    },
    {
        'name': 'Gaming',
        'description': 'Video game-related wallpapers',
        'icon': 'fa-gamepad',
        'color': '#32CD32',
        'is_featured': False,
        'display_order': 13
    },
    {
        'name': 'Movies',
        'description': 'Movie and TV show-related wallpapers',
        'icon': 'fa-film',
        'color': '#DC143C',
        'is_featured': False,
        'display_order': 14
    },
    {
        'name': 'Cars',
        'description': 'Automotive and vehicle wallpapers',
        'icon': 'fa-car',
        'color': '#B22222',
        'is_featured': False,
        'display_order': 15
    },
    {
        'name': 'Other',
        'description': 'Miscellaneous wallpapers',
        'icon': 'fa-ellipsis-h',
        'color': '#A9A9A9',
        'is_featured': False,
        'display_order': 16
    }
]


def create_default_categories():
    """Create default categories if they don't exist"""
    for category_data in DEFAULT_CATEGORIES:
        name = category_data['name']
        if not Category.objects.filter(name=name).exists():
            category = Category(
                name=name,
                description=category_data['description'],
                icon=category_data['icon'],
                color=category_data['color'],
                is_featured=category_data['is_featured'],
                display_order=category_data['display_order']
            )
            category.save()
            print(f"Created category: {name}")


def get_featured_categories(limit=8):
    """Get featured categories"""
    return Category.objects.filter(is_featured=True).order_by('display_order')[:limit]


def get_all_categories():
    """Get all categories ordered by display order"""
    return Category.objects.all().order_by('display_order')


def get_category_by_slug(slug):
    """Get a category by slug"""
    try:
        return Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        return None


def get_or_create_category(name):
    """Get or create a category by name"""
    try:
        return Category.objects.get(name=name)
    except Category.DoesNotExist:
        category = Category(name=name)
        category.save()
        return category
