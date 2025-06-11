from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Import and register signals
        from . import signals
        signals.register_signals()

        # Apply the JWT patches to fix Google OAuth
        from .direct_jwt_patch import apply_direct_patch
        from .google_jwt_patch import direct_patch_google_oauth
        from .google_adapter import setup_custom_google_adapter
        from .bypass_jwt import bypass_google_jwt_verification

        # Apply all patches for maximum compatibility
        apply_direct_patch()
        direct_patch_google_oauth()
        setup_custom_google_adapter()
        bypass_google_jwt_verification()
