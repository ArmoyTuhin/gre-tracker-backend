#!/usr/bin/env python3
"""
Database backup script for GRE Error Tracker.
Creates a backup of the database (SQLite or PostgreSQL).
"""
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import DATABASE_URL

def backup_sqlite(db_path: str, backup_dir: str):
    """Backup SQLite database."""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'gre_tracker_backup_{timestamp}.db')
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ SQLite backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Error backing up SQLite: {e}")
        return None

def backup_postgresql(db_url: str, backup_dir: str):
    """Backup PostgreSQL database using pg_dump."""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'gre_tracker_backup_{timestamp}.sql')
    
    try:
        # Extract connection details from DATABASE_URL
        # Format: postgresql://user:password@host:port/dbname
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        cmd = [
            'pg_dump',
            '-h', parsed.hostname or 'localhost',
            '-p', str(parsed.port or 5432),
            '-U', parsed.username or 'postgres',
            '-d', parsed.path[1:] if parsed.path else 'gre_tracker',
            '-f', backup_path,
            '-F', 'c'  # Custom format (compressed)
        ]
        
        # Set password from URL or environment
        env = os.environ.copy()
        if parsed.password:
            env['PGPASSWORD'] = parsed.password
        
        subprocess.run(cmd, env=env, check=True)
        print(f"✅ PostgreSQL backup created: {backup_path}")
        return backup_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Error backing up PostgreSQL: {e}")
        return None
    except FileNotFoundError:
        print("❌ pg_dump not found. Please install PostgreSQL client tools.")
        return None

def main():
    """Main backup function."""
    backup_dir = os.getenv('BACKUP_DIR', os.path.join(backend_dir, 'backups'))
    
    if DATABASE_URL.startswith('sqlite'):
        # Extract SQLite path
        db_path = DATABASE_URL.replace('sqlite:///', '').replace('sqlite:////', '/')
        if not os.path.isabs(db_path):
            db_path = os.path.join(backend_dir, db_path)
        backup_sqlite(db_path, backup_dir)
    elif DATABASE_URL.startswith('postgresql') or DATABASE_URL.startswith('postgres'):
        backup_postgresql(DATABASE_URL, backup_dir)
    else:
        print(f"❌ Unsupported database type: {DATABASE_URL}")

if __name__ == '__main__':
    main()

