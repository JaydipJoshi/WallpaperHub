from django.core.management.base import BaseCommand
from accounts.models_category import create_default_categories

class Command(BaseCommand):
    help = 'Create default categories for WallpaperHub'

    def handle(self, *args, **options):
        self.stdout.write('Creating default categories...')
        create_default_categories()
        self.stdout.write(self.style.SUCCESS('Default categories created successfully'))
