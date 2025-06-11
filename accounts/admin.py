from django.contrib import admin
from .models import Wallpaper, WallpaperInteraction, Collection, Comment, Tag, NewsletterSubscriber, PasswordResetOTP
from .models_user_extensions import UserProfile, UserSettings, UserPreferences, UserStatistics
from .models_category import Category

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'formatted_phone', 'phone_verified', 'created_at')
    list_filter = ('phone_verified', 'receive_sms_notifications', 'receive_email_notifications', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at', 'mongo_id')

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'first_name', 'last_name', 'date_of_birth', 'bio', 'location', 'website')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'phone_verified', 'phone_verified_at')
        }),
        ('Profile Settings', {
            'fields': ('profile_picture', 'receive_sms_notifications', 'receive_email_notifications')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'mongo_id'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'subscribed_at', 'source', 'user')
    list_filter = ('is_active', 'source', 'subscribed_at')
    search_fields = ('email', 'user__username', 'user__email')
    readonly_fields = ('unsubscribe_token', 'subscribed_at', 'ip_address', 'user_agent')
    ordering = ('-subscribed_at',)

    fieldsets = (
        ('Subscription Info', {
            'fields': ('email', 'is_active', 'subscribed_at', 'source')
        }),
        ('User Info', {
            'fields': ('user',)
        }),
        ('Technical Info', {
            'fields': ('unsubscribe_token', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    actions = ['activate_subscribers', 'deactivate_subscribers']

    def activate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscribers activated.')
    activate_subscribers.short_description = 'Activate selected subscribers'

    def deactivate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscribers deactivated.')
    deactivate_subscribers.short_description = 'Deactivate selected subscribers'


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ('contact_value', 'contact_type', 'otp_code', 'is_used', 'is_verified', 'attempts', 'created_at', 'expires_at')
    list_filter = ('contact_type', 'is_used', 'is_verified', 'created_at', 'expires_at')
    search_fields = ('contact_value', 'otp_code', 'user__username', 'user__email')
    readonly_fields = ('otp_code', 'created_at', 'expires_at', 'ip_address', 'user_agent')
    ordering = ('-created_at',)

    fieldsets = (
        ('Contact Info', {
            'fields': ('contact_value', 'contact_type', 'user')
        }),
        ('OTP Details', {
            'fields': ('otp_code', 'is_used', 'is_verified', 'attempts')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at')
        }),
        ('Technical Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def has_add_permission(self, request):
        return False  # Don't allow manual creation

    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing

    actions = ['mark_as_used']

    def mark_as_used(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f'{updated} OTP(s) marked as used.')
    mark_as_used.short_description = 'Mark selected OTPs as used'

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'layout_density', 'last_active')
    list_filter = ('theme', 'layout_density', 'show_email', 'email_notifications')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('last_active',)
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Appearance', {
            'fields': ('theme', 'accent_color', 'layout_density')
        }),
        ('Privacy', {
            'fields': ('show_email', 'show_activity', 'allow_data_collection')
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'site_notifications')
        }),
        ('Connected Accounts', {
            'fields': ('connected_google',)
        }),
        ('Session Data', {
            'fields': ('last_login_ip', 'last_active')
        }),
    )

# UserSession admin removed

@admin.register(Wallpaper)
class WallpaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'views', 'likes', 'downloads', 'shares', 'created_at')
    list_filter = ('category', 'custom_upload', 'created_at')
    search_fields = ('title', 'description', 'tags', 'unsplash_id')
    readonly_fields = ('id', 'views', 'likes', 'downloads', 'shares', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'tags', 'category')
        }),
        ('Image URLs', {
            'fields': ('image_url', 'image_path', 'small_url', 'regular_url', 'full_url')
        }),
        ('Statistics', {
            'fields': ('views', 'likes', 'downloads', 'shares')
        }),
        ('Source Information', {
            'fields': ('unsplash_id', 'custom_upload', 'uploaded_by')
        }),
        ('MongoDB Integration', {
            'fields': ('mongo_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(WallpaperInteraction)
class WallpaperInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallpaper', 'interaction_type', 'timestamp', 'device_type')
    list_filter = ('interaction_type', 'device_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'wallpaper__title', 'ip_address')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    fieldsets = (
        ('User & Wallpaper', {
            'fields': ('user', 'wallpaper')
        }),
        ('Interaction Details', {
            'fields': ('interaction_type', 'timestamp', 'duration')
        }),
        ('Device Information', {
            'fields': ('ip_address', 'user_agent', 'device_type', 'session_id')
        }),
        ('Share Information', {
            'fields': ('share_platform',)
        }),
        ('Analytics', {
            'fields': ('referrer',)
        }),
        ('MongoDB Integration', {
            'fields': ('mongo_id',)
        }),
    )

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'privacy', 'featured', 'get_wallpaper_count', 'view_count', 'created_at')
    list_filter = ('privacy', 'featured', 'created_at')
    search_fields = ('name', 'description', 'owner__username', 'owner__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_modified_at', 'view_count')
    filter_horizontal = ('wallpapers',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'owner')
        }),
        ('Cover Image', {
            'fields': ('cover_image', 'custom_cover_url')
        }),
        ('Wallpapers', {
            'fields': ('wallpapers',)
        }),
        ('Settings', {
            'fields': ('privacy', 'featured', 'sort_order')
        }),
        ('Statistics', {
            'fields': ('view_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_modified_at')
        }),
        ('MongoDB Integration', {
            'fields': ('mongo_id',)
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'wallpaper', 'content_preview', 'status', 'likes', 'created_at', 'is_reply')
    list_filter = ('status', 'created_at', 'edited')
    search_fields = ('content', 'author__username', 'author__email', 'wallpaper__title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'edited')
    date_hierarchy = 'created_at'

    def content_preview(self, obj):
        """Return a preview of the comment content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def is_reply(self, obj):
        """Return whether this comment is a reply"""
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = 'Reply'

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'content', 'author', 'wallpaper')
        }),
        ('Reply Information', {
            'fields': ('parent',),
            'classes': ('collapse',),
        }),
        ('Moderation', {
            'fields': ('status', 'moderated_by', 'moderated_at', 'moderation_reason')
        }),
        ('Engagement', {
            'fields': ('likes',)
        }),
        ('Tracking', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'edited')
        }),
        ('MongoDB Integration', {
            'fields': ('mongo_id',)
        }),
    )

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_aspect_ratio', 'default_download_quality', 'created_at')
    list_filter = ('preferred_aspect_ratio', 'show_nsfw_content', 'hide_viewed_wallpapers', 'hide_downloaded_wallpapers')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Categories and Tags', {
            'fields': ('preferred_categories', 'preferred_tags', 'preferred_colors')
        }),
        ('Display Preferences', {
            'fields': ('preferred_aspect_ratio', 'show_nsfw_content', 'hide_viewed_wallpapers', 'hide_downloaded_wallpapers')
        }),
        ('Discovery Preferences', {
            'fields': ('show_trending', 'show_featured', 'show_new', 'show_recommendations')
        }),
        ('Download Preferences', {
            'fields': ('default_download_quality', 'auto_resize_to_screen')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
        ('MongoDB Integration', {
            'fields': ('mongo_id',)
        }),
    )

@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_views', 'total_downloads', 'total_likes', 'total_shares', 'last_interaction_at')
    list_filter = ('created_at', 'last_interaction_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('total_views', 'total_downloads', 'total_likes', 'total_shares', 'total_saves',
                       'total_uploads', 'total_collections', 'total_comments', 'total_time_spent',
                       'category_interactions', 'tag_interactions', 'daily_activity', 'weekly_activity',
                       'monthly_activity', 'device_usage', 'created_at', 'updated_at', 'last_interaction_at')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('General Statistics', {
            'fields': ('total_views', 'total_downloads', 'total_likes', 'total_shares', 'total_saves',
                      'total_uploads', 'total_collections', 'total_comments', 'total_time_spent')
        }),
        ('Interaction Patterns', {
            'fields': ('category_interactions', 'tag_interactions', 'device_usage')
        }),
        ('Activity Timeline', {
            'fields': ('daily_activity', 'weekly_activity', 'monthly_activity')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_interaction_at')
        }),
        ('MongoDB Integration', {
            'fields': ('mongo_id',)
        }),
    )

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'usage_count', 'search_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'slug', 'description')
    readonly_fields = ('usage_count', 'search_count', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Statistics', {
            'fields': ('usage_count', 'search_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
        ('MongoDB Integration', {
            'fields': ('mongo_id',)
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'is_featured', 'wallpaper_count', 'view_count')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('name', 'slug', 'description')
    readonly_fields = ('wallpaper_count', 'view_count', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'cover_image_url', 'display_order')
        }),
        ('Featured Status', {
            'fields': ('is_featured', 'featured_at')
        }),
        ('Statistics', {
            'fields': ('wallpaper_count', 'view_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
        ('MongoDB Integration', {
            'fields': ('mongo_id',)
        }),
    )