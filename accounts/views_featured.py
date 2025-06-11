from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Wallpaper
from .models_category import Category, get_featured_categories, get_all_categories, get_category_by_slug

def featured_wallpapers(request):
    """View for featured wallpapers"""
    # Get featured wallpapers
    featured = Wallpaper.objects.filter(is_featured=True).order_by('-featured_at')
    
    # Paginate the results
    paginator = Paginator(featured, 20)  # Show 20 wallpapers per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get featured categories
    featured_categories = get_featured_categories()
    
    context = {
        'page_obj': page_obj,
        'featured_categories': featured_categories,
        'title': 'Featured Wallpapers',
        'description': 'Explore our handpicked collection of featured wallpapers',
    }
    
    return render(request, 'featured.html', context)

def category_list(request):
    """View for category list"""
    # Get all categories
    categories = get_all_categories()
    
    # Get featured categories
    featured_categories = get_featured_categories()
    
    context = {
        'categories': categories,
        'featured_categories': featured_categories,
        'title': 'Categories',
        'description': 'Browse wallpapers by category',
    }
    
    return render(request, 'category_list.html', context)

def category_detail(request, slug):
    """View for category detail"""
    # Get the category
    category = get_object_or_404(Category, slug=slug)
    
    # Increment view count
    category.increment_view_count()
    
    # Get wallpapers in this category
    wallpapers = Wallpaper.objects.filter(category_obj=category).order_by('-created_at')
    
    # Paginate the results
    paginator = Paginator(wallpapers, 20)  # Show 20 wallpapers per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get featured categories
    featured_categories = get_featured_categories()
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'featured_categories': featured_categories,
        'title': f'{category.name} Wallpapers',
        'description': category.description,
    }
    
    return render(request, 'category_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def toggle_featured_wallpaper(request, wallpaper_id):
    """Toggle featured status of a wallpaper"""
    # Get the wallpaper
    wallpaper = get_object_or_404(Wallpaper, id=wallpaper_id)
    
    # Toggle featured status
    wallpaper.is_featured = not wallpaper.is_featured
    
    # Update featured_at timestamp
    if wallpaper.is_featured:
        from django.utils import timezone
        wallpaper.featured_at = timezone.now()
    else:
        wallpaper.featured_at = None
    
    # Save the wallpaper
    wallpaper.save(update_fields=['is_featured', 'featured_at'])
    
    return JsonResponse({
        'success': True,
        'is_featured': wallpaper.is_featured,
        'message': f'Wallpaper {"featured" if wallpaper.is_featured else "unfeatured"} successfully'
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def toggle_featured_category(request, category_id):
    """Toggle featured status of a category"""
    # Get the category
    category = get_object_or_404(Category, id=category_id)
    
    # Toggle featured status
    is_featured = category.toggle_featured()
    
    return JsonResponse({
        'success': True,
        'is_featured': is_featured,
        'message': f'Category {"featured" if is_featured else "unfeatured"} successfully'
    })
