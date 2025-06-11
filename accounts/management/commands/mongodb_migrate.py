from django.core.management.base import BaseCommand
from accounts.mongodb_migrations import run_migrations

class Command(BaseCommand):
    help = 'Run MongoDB migrations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting MongoDB migrations...'))
        
        success = run_migrations()
        
        if success:
            self.stdout.write(self.style.SUCCESS('MongoDB migrations completed successfully!'))
        else:
            self.stdout.write(self.style.ERROR('MongoDB migrations failed!'))
