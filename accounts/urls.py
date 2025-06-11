from django.urls import path
from . import views
from . import views_featured
from . import views_user_profile

urlpatterns = [
    # Authentication URLs
    path('signup/', views.register_user, name='signup'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('oauth-check/', views.check_oauth_urls, name='check_oauth_urls'),

    # User Profile URLs
    path('user/profile/', views_user_profile.user_profile, name='user_profile'),
    path('user/preferences/update/', views_user_profile.update_preferences, name='update_preferences'),
    path('user/settings/update/', views_user_profile.update_settings, name='update_settings'),
    path('user/stats/', views_user_profile.get_user_stats, name='get_user_stats'),
    path('user/category/add/<str:category>/', views_user_profile.add_preferred_category, name='add_preferred_category'),
    path('user/category/remove/<str:category>/', views_user_profile.remove_preferred_category, name='remove_preferred_category'),
    path('user/tag/add/<str:tag>/', views_user_profile.add_preferred_tag, name='add_preferred_tag'),
    path('user/tag/remove/<str:tag>/', views_user_profile.remove_preferred_tag, name='remove_preferred_tag'),
    path('user/color/add/<str:color>/', views_user_profile.add_preferred_color, name='add_preferred_color'),
    path('user/color/remove/<str:color>/', views_user_profile.remove_preferred_color, name='remove_preferred_color'),
    path('user/recommended/', views_user_profile.get_recommended_wallpapers, name='get_recommended_wallpapers'),

    # Featured and Category URLs
    path('featured/', views_featured.featured_wallpapers, name='featured_wallpapers'),
    path('categories/', views_featured.category_list, name='category_list'),
    path('category/<slug:slug>/', views_featured.category_detail, name='category_detail'),
    path('wallpaper/<int:wallpaper_id>/toggle-featured/', views_featured.toggle_featured_wallpaper, name='toggle_featured_wallpaper'),
    path('category/<int:category_id>/toggle-featured/', views_featured.toggle_featured_category, name='toggle_featured_category'),
]
