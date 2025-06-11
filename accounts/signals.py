from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from pymongo import MongoClient
from bson.objectid import ObjectId

# These imports will be used at the end of the file
# to avoid circular imports
Tag = None
Wallpaper = None
WallpaperInteraction = None
Collection = None
Comment = None


def register_signals():
    """Register all signal handlers"""
    # Import models here to avoid circular imports
    from .models import Tag, Wallpaper, WallpaperInteraction, Collection, Comment
    
    # Update model references
    globals()['Tag'] = Tag
    globals()['Wallpaper'] = Wallpaper
    globals()['WallpaperInteraction'] = WallpaperInteraction
    globals()['Collection'] = Collection
    globals()['Comment'] = Comment
    
    # Connect signals
    post_save.connect(tag_post_save, sender=Tag)
    post_delete.connect(tag_post_delete, sender=Tag)
    post_save.connect(wallpaper_post_save, sender=Wallpaper)
    post_delete.connect(wallpaper_post_delete, sender=Wallpaper)
    post_save.connect(interaction_post_save, sender=WallpaperInteraction)
    post_save.connect(collection_post_save, sender=Collection)
    post_save.connect(comment_post_save, sender=Comment)
    post_delete.connect(comment_post_delete, sender=Comment)
    post_delete.connect(collection_post_delete, sender=Collection)


def tag_post_save(sender, instance, created, **kwargs):
    """Sync Tag model to MongoDB after save"""
    # Only sync if we're not already in the middle of a sync operation
    if not getattr(instance, '_syncing', False):
        instance._syncing = True
        instance.sync_to_mongodb()
        instance._syncing = False


def tag_post_delete(sender, instance, **kwargs):
    """Delete Tag from MongoDB when deleted from Django"""
    if instance.mongo_id:
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            tags = db.tags
            
            tags.delete_one({'_id': ObjectId(instance.mongo_id)})
        except Exception as e:
            print(f"Error deleting tag from MongoDB: {e}")


def wallpaper_post_save(sender, instance, created, **kwargs):
    """Sync Wallpaper model to MongoDB after save"""
    # Only sync if we're not already in the middle of a sync operation
    if not getattr(instance, '_syncing', False):
        instance._syncing = True
        instance.sync_to_mongodb()
        instance._syncing = False


def wallpaper_post_delete(sender, instance, **kwargs):
    """Delete Wallpaper from MongoDB when deleted from Django"""
    if instance.mongo_id:
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            wallpapers = db.wallpapers
            
            wallpapers.delete_one({'_id': ObjectId(instance.mongo_id)})
        except Exception as e:
            print(f"Error deleting wallpaper from MongoDB: {e}")


def interaction_post_save(sender, instance, created, **kwargs):
    """Sync WallpaperInteraction model to MongoDB after save"""
    # Only sync if we're not already in the middle of a sync operation
    if not getattr(instance, '_syncing', False):
        instance._syncing = True
        instance.sync_to_mongodb()
        instance._syncing = False


def collection_post_save(sender, instance, created, **kwargs):
    """Sync Collection model to MongoDB after save"""
    # Only sync if we're not already in the middle of a sync operation
    if not getattr(instance, '_syncing', False):
        instance._syncing = True
        instance.sync_to_mongodb()
        instance._syncing = False


def comment_post_save(sender, instance, created, **kwargs):
    """Sync Comment model to MongoDB after save"""
    # Only sync if we're not already in the middle of a sync operation
    if not getattr(instance, '_syncing', False):
        instance._syncing = True
        instance.sync_to_mongodb()
        instance._syncing = False


def comment_post_delete(sender, instance, **kwargs):
    """Delete Comment from MongoDB when deleted from Django"""
    if instance.mongo_id:
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            comments = db.comments
            
            comments.delete_one({'_id': ObjectId(instance.mongo_id)})
        except Exception as e:
            print(f"Error deleting comment from MongoDB: {e}")


def collection_post_delete(sender, instance, **kwargs):
    """Delete Collection from MongoDB when deleted from Django"""
    if instance.mongo_id:
        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client['wallpaperhub_db']
            collections = db.collections
            
            collections.delete_one({'_id': ObjectId(instance.mongo_id)})
        except Exception as e:
            print(f"Error deleting collection from MongoDB: {e}")
