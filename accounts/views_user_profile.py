from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Wallpaper, Collection
from .models_user_extensions import UserSettings, UserPreferences, UserStatistics
import json

@login_required
def user_profile(request):
    """View for user profile page with statistics and preferences"""
    # Get user profile extensions
    settings = UserSettings.objects.get_or_create(user=request.user)[0]
    preferences = UserPreferences.objects.get_or_create(user=request.user)[0]
    statistics = UserStatistics.objects.get_or_create(user=request.user)[0]
    
    # Get user collections
    collections = Collection.objects.filter(owner=request.user)
    
    # Get user's saved, liked, and uploaded wallpapers
    saved_wallpapers = request.user.saved_wallpapers.all()
    liked_wallpapers = request.user.liked_wallpapers.all()
    uploaded_wallpapers = request.user.uploaded_wallpapers.all()
    
    # Get activity summary
    activity_summary = statistics.get_activity_summary(days=30)
    
    # Get most viewed categories
    most_viewed_categories = statistics.get_most_viewed_categories()
    
    # Get most used tags
    most_used_tags = statistics.get_most_used_tags()
    
    # Prepare context
    context = {
        'user': request.user,
        'settings': settings,
        'preferences': preferences,
        'statistics': statistics,
        'collections': collections,
        'saved_wallpapers': saved_wallpapers,
        'liked_wallpapers': liked_wallpapers,
        'uploaded_wallpapers': uploaded_wallpapers,
        'activity_summary': activity_summary,
        'most_viewed_categories': most_viewed_categories,
        'most_used_tags': most_used_tags,
    }
    
    return render(request, 'user_profile.html', context)

@login_required
def update_preferences(request):
    """Update user preferences"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'})
    
    # Get user preferences
    preferences = UserPreferences.objects.get_or_create(user=request.user)[0]
    
    # Update preferences from POST data
    try:
        data = json.loads(request.body)
        
        # Update aspect ratio preference
        if 'preferred_aspect_ratio' in data:
            preferences.preferred_aspect_ratio = data['preferred_aspect_ratio']
        
        # Update content preferences
        if 'show_nsfw_content' in data:
            preferences.show_nsfw_content = data['show_nsfw_content']
        if 'hide_viewed_wallpapers' in data:
            preferences.hide_viewed_wallpapers = data['hide_viewed_wallpapers']
        if 'hide_downloaded_wallpapers' in data:
            preferences.hide_downloaded_wallpapers = data['hide_downloaded_wallpapers']
        
        # Update discovery preferences
        if 'show_trending' in data:
            preferences.show_trending = data['show_trending']
        if 'show_featured' in data:
            preferences.show_featured = data['show_featured']
        if 'show_new' in data:
            preferences.show_new = data['show_new']
        if 'show_recommendations' in data:
            preferences.show_recommendations = data['show_recommendations']
        
        # Update download preferences
        if 'default_download_quality' in data:
            preferences.default_download_quality = data['default_download_quality']
        if 'auto_resize_to_screen' in data:
            preferences.auto_resize_to_screen = data['auto_resize_to_screen']
        
        # Update category preferences
        if 'preferred_categories' in data:
            preferences.preferred_categories = data['preferred_categories']
        
        # Update tag preferences
        if 'preferred_tags' in data:
            preferences.preferred_tags = data['preferred_tags']
        
        # Update color preferences
        if 'preferred_colors' in data:
            preferences.preferred_colors = data['preferred_colors']
        
        # Save preferences
        preferences.save()
        
        return JsonResponse({'status': 'success', 'message': 'Preferences updated successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def update_settings(request):
    """Update user settings"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'})
    
    # Get user settings
    settings = UserSettings.objects.get_or_create(user=request.user)[0]
    
    # Update settings from POST data
    try:
        data = json.loads(request.body)
        
        # Update appearance settings
        if 'theme' in data:
            settings.theme = data['theme']
        if 'accent_color' in data:
            settings.accent_color = data['accent_color']
        if 'layout_density' in data:
            settings.layout_density = data['layout_density']
        
        # Update privacy settings
        if 'show_email' in data:
            settings.show_email = data['show_email']
        if 'show_activity' in data:
            settings.show_activity = data['show_activity']
        if 'allow_data_collection' in data:
            settings.allow_data_collection = data['allow_data_collection']
        
        # Update notification settings
        if 'email_notifications' in data:
            settings.email_notifications = data['email_notifications']
        if 'site_notifications' in data:
            settings.site_notifications = data['site_notifications']
        
        # Update last active timestamp
        settings.update_last_active()
        
        return JsonResponse({'status': 'success', 'message': 'Settings updated successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def get_user_stats(request):
    """Get user statistics as JSON for charts"""
    # Get user statistics
    statistics = UserStatistics.objects.get_or_create(user=request.user)[0]
    
    # Get activity summary
    activity_summary = statistics.get_activity_summary(days=30)
    
    # Prepare data for charts
    daily_activity = []
    for date, count in activity_summary['daily_activity'].items():
        daily_activity.append({
            'date': date,
            'count': count
        })
    
    # Sort daily activity by date
    daily_activity.sort(key=lambda x: x['date'])
    
    # Prepare category data
    category_data = []
    for category, count in statistics.get_most_viewed_categories():
        category_data.append({
            'category': category,
            'count': count
        })
    
    # Prepare tag data
    tag_data = []
    for tag, count in statistics.get_most_used_tags():
        tag_data.append({
            'tag': tag,
            'count': count
        })
    
    # Prepare device usage data
    device_data = []
    for device, count in statistics.device_usage.items():
        device_data.append({
            'device': device,
            'count': count
        })
    
    # Prepare response data
    data = {
        'total_views': statistics.total_views,
        'total_downloads': statistics.total_downloads,
        'total_likes': statistics.total_likes,
        'total_shares': statistics.total_shares,
        'total_saves': statistics.total_saves,
        'total_uploads': statistics.total_uploads,
        'total_collections': statistics.total_collections,
        'total_comments': statistics.total_comments,
        'total_time_spent': statistics.total_time_spent,
        'daily_activity': daily_activity,
        'category_data': category_data,
        'tag_data': tag_data,
        'device_data': device_data
    }
    
    return JsonResponse(data)

@login_required
def add_preferred_category(request, category):
    """Add a category to user's preferred categories"""
    # Get user preferences
    preferences = UserPreferences.objects.get_or_create(user=request.user)[0]
    
    # Add category to preferred categories
    result = preferences.add_preferred_category(category)
    
    if result:
        return JsonResponse({'status': 'success', 'message': f'Added {category} to preferred categories'})
    else:
        return JsonResponse({'status': 'info', 'message': f'{category} is already in preferred categories'})

@login_required
def remove_preferred_category(request, category):
    """Remove a category from user's preferred categories"""
    # Get user preferences
    preferences = UserPreferences.objects.get_or_create(user=request.user)[0]
    
    # Remove category from preferred categories
    result = preferences.remove_preferred_category(category)
    
    if result:
        return JsonResponse({'status': 'success', 'message': f'Removed {category} from preferred categories'})
    else:
        return JsonResponse({'status': 'info', 'message': f'{category} is not in preferred categories'})

@login_required
def add_preferred_tag(request, tag):
    """Add a tag to user's preferred tags"""
    # Get user preferences
    preferences = UserPreferences.objects.get_or_create(user=request.user)[0]
    
    # Add tag to preferred tags
    result = preferences.add_preferred_tag(tag)
    
    if result:
        return JsonResponse({'status': 'success', 'message': f'Added {tag} to preferred tags'})
    else:
        return JsonResponse({'status': 'info', 'message': f'{tag} is already in preferred tags'})

@login_required
def remove_preferred_tag(request, tag):
    """Remove a tag from user's preferred tags"""
    # Get user preferences
    preferences = UserPreferences.objects.get_or_create(user=request.user)[0]
    
    # Remove tag from preferred tags
    result = preferences.remove_preferred_tag(tag)
    
    if result:
        return JsonResponse({'status': 'success', 'message': f'Removed {tag} from preferred tags'})
    else:
        return JsonResponse({'status': 'info', 'message': f'{tag} is not in preferred tags'})

@login_required
def add_preferred_color(request, color):
    """Add a color to user's preferred colors"""
    # Get user preferences
    preferences = UserPreferences.objects.get_or_create(user=request.user)[0]
    
    # Add color to preferred colors
    result = preferences.add_preferred_color(color)
    
    if result:
        return JsonResponse({'status': 'success', 'message': f'Added {color} to preferred colors'})
    else:
        return JsonResponse({'status': 'info', 'message': f'{color} is already in preferred colors'})

@login_required
def remove_preferred_color(request, color):
    """Remove a color from user's preferred colors"""
    # Get user preferences
    preferences = UserPreferences.objects.get_or_create(user=request.user)[0]
    
    # Remove color from preferred colors
    result = preferences.remove_preferred_color(color)
    
    if result:
        return JsonResponse({'status': 'success', 'message': f'Removed {color} from preferred colors'})
    else:
        return JsonResponse({'status': 'info', 'message': f'{color} is not in preferred colors'})

@login_required
def get_recommended_wallpapers(request):
    """Get recommended wallpapers based on user preferences and statistics"""
    from .models_user_extensions import get_recommended_wallpapers as get_recommendations
    
    # Get recommended wallpapers
    recommended = get_recommendations(request.user, limit=20)
    
    # Prepare response data
    data = []
    for wallpaper in recommended:
        data.append({
            'id': str(wallpaper.id),
            'title': wallpaper.title,
            'image_url': wallpaper.get_image_url(),
            'views': wallpaper.views,
            'likes': wallpaper.likes,
            'downloads': wallpaper.downloads
        })
    
    return JsonResponse({'wallpapers': data})
