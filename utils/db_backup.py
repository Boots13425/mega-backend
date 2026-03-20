"""
Database backup utility module for Django PostgreSQL backups.

This module provides functionality to:
- Create timestamped PostgreSQL database backups using pg_dump
- Compress backups using gzip
- Verify backup integrity
- Log all operations for auditing
"""

import os
import gzip
import logging
import subprocess
import datetime
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


# Configure logging for backup operations
logger = logging.getLogger('backup')
logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(settings.BASE_DIR) / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for backup logs
log_file = logs_dir / 'backup.log'
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Create console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and add it to handlers
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_database_config():
    """Extract database configuration from Django settings."""
    db_config = settings.DATABASES['default']
    
    if db_config['ENGINE'] != 'django.db.backends.postgresql':
        raise ImproperlyConfigured("This backup utility only supports PostgreSQL databases.")
    
    return {
        'host': db_config.get('HOST', 'localhost'),
        'port': db_config.get('PORT', '5432'),
        'user': db_config['USER'],
        'password': db_config['PASSWORD'],
        'name': db_config['NAME']
    }


def create_backups_directory():
    """Create the backups directory if it doesn't exist."""
    backups_dir = Path(settings.BASE_DIR) / 'backups'
    backups_dir.mkdir(exist_ok=True)
    return backups_dir


def generate_timestamped_filename():
    """Generate a timestamped filename for the backup."""
    timestamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')
    filename = f'db_backup_{timestamp}.dump.gz'
    return filename


def execute_pg_dump(db_config, backup_file):
    """Execute pg_dump command to create database backup."""
    # Set environment variable for password
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    # Build pg_dump command
    cmd = [
        'pg_dump',
        '-h', db_config['host'],
        '-p', str(db_config['port']),
        '-U', db_config['user'],
        '-F', 'c',  # Custom format
        '-b',      # Include large objects
        '-f', str(backup_file),
        db_config['name']
    ]
    
    logger.info(f"Executing: {' '.join(cmd)}")
    
    try:
        # Execute the command
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("pg_dump completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump failed with return code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.error("pg_dump command not found. Please ensure PostgreSQL client tools are installed and in PATH.")
        raise


def compress_backup(backup_file):
    """Compress the backup file using gzip."""
    compressed_file = backup_file.with_suffix('.dump.gz')
    
    logger.info(f"Compressing backup to: {compressed_file}")
    
    try:
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                f_out.writelines(f_in)
        
        # Remove the uncompressed file
        backup_file.unlink()
        logger.info("Backup compression completed successfully")
        return compressed_file
        
    except Exception as e:
        logger.error(f"Compression failed: {str(e)}")
        raise


def verify_backup(compressed_file):
    """Verify the integrity of the compressed backup file."""
    logger.info("Verifying backup integrity...")
    
    # Check if file exists
    if not compressed_file.exists():
        logger.error("Backup file does not exist")
        raise FileNotFoundError("Backup file verification failed: file not found")
    
    # Check file size
    file_size = compressed_file.stat().st_size
    if file_size == 0:
        logger.error("Backup file is empty")
        raise ValueError("Backup file verification failed: file is empty")
    
    # Attempt to read the gzip file
    try:
        with gzip.open(compressed_file, 'rb') as f:
            # Read first few bytes to verify it's a valid gzip file
            f.read(10)
        logger.info(f"Backup verification successful. File size: {file_size / (1024*1024):.2f} MB")
        return True
        
    except gzip.BadGzipFile:
        logger.error("Backup file is not a valid gzip file")
        raise
    except Exception as e:
        logger.error(f"Backup verification failed: {str(e)}")
        raise


def backup_database():
    """
    Main backup function that orchestrates the entire backup process.
    
    Returns:
        Path: Path to the created backup file
        
    Raises:
        Exception: If any step in the backup process fails
    """
    logger.info("=" * 50)
    logger.info("Starting database backup")
    logger.info("=" * 50)
    
    try:
        # Get database configuration
        db_config = get_database_config()
        logger.info(f"Database: {db_config['name']} on {db_config['host']}:{db_config['port']}")
        
        # Create backups directory
        backups_dir = create_backups_directory()
        logger.info(f"Backups directory: {backups_dir}")
        
        # Generate timestamped filename
        filename = generate_timestamped_filename()
        backup_file = backups_dir / filename.replace('.gz', '')  # pg_dump creates uncompressed file first
        
        logger.info(f"Backup filename: {filename}")
        
        # Execute pg_dump
        execute_pg_dump(db_config, backup_file)
        
        # Compress the backup
        compressed_file = compress_backup(backup_file)
        
        # Verify the backup
        verify_backup(compressed_file)
        
        logger.info("=" * 50)
        logger.info("Database backup completed successfully")
        logger.info(f"Backup file: {compressed_file}")
        logger.info("=" * 50)
        
        return compressed_file
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error(f"Database backup failed: {str(e)}")
        logger.error("=" * 50)
        raise