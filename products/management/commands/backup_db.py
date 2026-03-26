from django.core.management.base import BaseCommand

from utils.db_backup import backup_database


class Command(BaseCommand):
    help = "Create a PostgreSQL database backup (pg_dump + gzip) at 18:00 via OS scheduler."

    def handle(self, *args, **options):
        try:
            result = backup_database()
            self.stdout.write(self.style.SUCCESS(f"Backup successful: {result.get('backup_path')}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Backup failed: {e}"))
            raise

"""
Django management command to perform database backup.

Usage:
    python manage.py backup_db

This command will:
- Create a timestamped PostgreSQL database backup
- Compress it using gzip
- Verify the backup integrity
- Log all operations
"""

from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured
import sys
from pathlib import Path

# Add the utils module to the path so we can import it
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from utils.db_backup import backup_database


class Command(BaseCommand):
    help = 'Create a compressed PostgreSQL database backup with verification and logging'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating the backup',
        )
    
    def handle(self, *args, **options):
        """Execute the backup command."""
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN: This would create a database backup without actually doing it.')
            )
            return
        
        try:
            self.stdout.write(
                self.style.SUCCESS('Starting database backup process...')
            )
            
            # Call the backup function
            backup_file = backup_database()
            
            # Success message
            self.stdout.write(
                self.style.SUCCESS(
                    f'Database backup completed successfully!\n'
                    f'Backup file: {backup_file}\n'
                    f'Log file: logs/backup.log'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Database backup failed: {str(e)}')
            )
            self.stdout.write(
                self.style.ERROR('Check logs/backup.log for detailed error information.')
            )
            # Exit with error code
            sys.exit(1)