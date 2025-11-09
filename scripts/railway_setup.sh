#!/bin/bash
# Railway setup script - runs before starting the app

echo "🚂 Starting Railway setup..."

# Create necessary directories
mkdir -p storage/sqlite
mkdir -p storage/chroma
mkdir -p logs

echo "✅ Directories created"

# Initialize databases if needed
if [ ! -f "storage/sqlite/sessions.db" ]; then
    echo "📊 Initializing SQLite database..."
    python -c "from app.database.sqlite_db import init_db; init_db()"
fi

# Check if assessment data exists
if [ ! -f "data/shl_assessments.json" ] || [ ! -s "data/shl_assessments.json" ]; then
    echo "🔄 Scraping assessment data..."
    python scripts/scrape_catalog.py
fi

# Initialize ChromaDB if collection doesn't exist
echo "🗄️ Initializing vector database..."
python scripts/init_vector_db.py

echo "✅ Railway setup complete!"