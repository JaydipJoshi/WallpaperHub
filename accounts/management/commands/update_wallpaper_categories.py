from django.core.management.base import BaseCommand
from accounts.models import Wallpaper
from accounts.models_category import get_or_create_category

class Command(BaseCommand):
    help = 'Update existing wallpapers with category relationships'

    def handle(self, *args, **options):
        self.stdout.write('Updating wallpaper categories...')
        
        # Get all wallpapers
        wallpapers = Wallpaper.objects.all()
        self.stdout.write(f'Found {wallpapers.count()} wallpapers')
        
        # Update category relationships
        updated_count = 0
        for wallpaper in wallpapers:
            if wallpaper.category and not wallpaper.category_obj:
                # Get or create the category
                category = get_or_create_category(wallpaper.category)
                
                # Update the wallpaper
                wallpaper.category_obj = category
                wallpaper.save(update_fields=['category_obj'])
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    self.stdout.write(f'Updated {updated_count} wallpapers')
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} wallpapers with category relationships'))
