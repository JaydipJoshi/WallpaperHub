"""
URL configuration for WallpaperHub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from accounts import password_reset_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landingPage, name='landing_page'),
    path('userHome/', views.userHome, name='user_home'),
    path('loginpage/', views.loginpage, name='loginpage'),
    path('signUpPage/', views.signUpPage, name='signuppage'),
    path('landingPage/', views.landingPage, name='landingpage'),

    # Static pages
    path('termsOfService.html', views.termsOfService, name='terms_of_service'),
    path('privacyPolicy.html', views.privacyPolicy, name='privacy_policy'),
    path('aboutUs.html', views.aboutUs, name='about_us'),
    path('smooth-scroll-demo/', views.smooth_scroll_demo, name='smooth_scroll_demo'),

    # Wallpaper detail page
    path('wallpaper/<str:id>/', views.wallpaper_detail, name='wallpaper_detail'),

    # Categories pages
    path('categories/', views.categories, name='categories'),
    path('category-preview/<str:category>/', views.category_preview, name='category_preview'),

    # User profile and settings
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('upload-wallpaper/', views.upload_wallpaper, name='upload_wallpaper'),
    path('settings/', views.settings_page, name='settings'),

    # API endpoints
    path('api/wallpapers/<str:id>/like/', views.wallpaper_like, name='wallpaper_like'),
    path('api/wallpapers/<str:id>/download/', views.wallpaper_download, name='wallpaper_download'),
    path('api/wallpapers/<str:id>/download-file/', views.wallpaper_download_file, name='wallpaper_download_file'),
    path('api/wallpapers/<str:id>/share/', views.wallpaper_share, name='wallpaper_share'),
    path('api/wallpapers/<str:id>/save/', views.wallpaper_save, name='wallpaper_save'),

    # Newsletter endpoints
    path('api/newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/unsubscribe/<uuid:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    path('newsletter/preferences/<uuid:token>/', views.newsletter_preferences, name='newsletter_preferences'),

    # Test endpoint
    path('api/newsletter/test/', views.newsletter_test, name='newsletter_test'),

    # Password Reset endpoints
    path('forgot-password/', password_reset_views.forgot_password, name='forgot_password'),
    path('forgot-password/step1/', password_reset_views.forgot_password_step1, name='forgot_password_step1'),
    path('forgot-password/step2/', password_reset_views.forgot_password_step2, name='forgot_password_step2'),
    path('forgot-password/step3/', password_reset_views.forgot_password_step3, name='forgot_password_step3'),
    path('forgot-password/resend-otp/', password_reset_views.forgot_password_resend_otp, name='forgot_password_resend_otp'),
    path('api/password-strength/', password_reset_views.check_password_strength, name='check_password_strength'),

    # Include accounts app URLs
    path('', include('accounts.urls')),

    # Django AllAuth URLs
    path('accounts/', include('allauth.urls')),
]



