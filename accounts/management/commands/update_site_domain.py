from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Update the Site domain to match the current host'

    def add_arguments(self, parser):
        parser.add_argument('domain', type=str, help='The domain to set for the site')

    def handle(self, *args, **options):
        domain = options['domain']
        
        # Get the current site
        site = Site.objects.get_current()
        
        # Update the domain and name
        old_domain = site.domain
        site.domain = domain
        site.name = 'WallpaperHub'
        site.save()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated site domain from "{old_domain}" to "{domain}"'))
