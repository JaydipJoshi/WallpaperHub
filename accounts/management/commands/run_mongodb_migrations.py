from django.core.management.base import BaseCommand
from accounts.mongodb_migrations import run_migrations

class Command(BaseCommand):
    help = 'Run MongoDB migrations'

    def handle(self, *args, **options):
        self.stdout.write('Running MongoDB migrations...')
        success = run_migrations()
        
        if success:
            self.stdout.write(self.style.SUCCESS('Successfully ran MongoDB migrations'))
        else:
            self.stdout.write(self.style.ERROR('Failed to run MongoDB migrations'))
