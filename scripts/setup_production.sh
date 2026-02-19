#!/bin/bash
# Production setup script for GRE Error Tracker

set -e

echo "🚀 Setting up GRE Error Tracker for production..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your production values!"
fi

# Create backups directory
echo "📁 Creating backups directory..."
mkdir -p backups

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Create initial backup
echo "💾 Creating initial database backup..."
python3 scripts/backup_db.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your production database URL"
echo "2. Run: uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "3. Set up automated backups (see README_DEPLOYMENT.md)"

