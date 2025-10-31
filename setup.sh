#!/bin/bash

set -e

echo "╔════════════════════════════════════════╗"
echo "║       Nexva Backend Setup & Start      ║"
echo "╔════════════════════════════════════════╗"
echo ""

BACKUP_DIR="./backups"
DB_BACKUP_FILE="$BACKUP_DIR/postgres_latest.sql"
PORT=8001

echo "🧹 Cleaning up..."
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name '*.pyc' -delete 2>/dev/null || true
find . -name '.DS_Store' -delete 2>/dev/null || true

echo "🔪 Killing previous processes on port $PORT..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true
sleep 2

echo "🐳 Checking Docker services..."
if docker ps &>/dev/null; then
    if ! docker ps | grep -q "learning_postgres\|learning_elasticsearch"; then
        echo "   Starting Docker containers..."
        docker-compose up -d
        echo "   Waiting for services to initialize..."
        sleep 20
    else
        echo "   ✅ Docker containers running"
    fi
else
    echo "   ⚠️  Docker not accessible (running inside container?)"
    echo "   Assuming services are running on host..."
fi

echo ""
echo "📦 Checking Elasticsearch..."
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    echo "   ✅ Elasticsearch is ready"
else
    echo "   ❌ Elasticsearch not accessible. Restarting..."
    docker-compose restart elasticsearch
    sleep 15
    if ! curl -s http://localhost:9200 > /dev/null 2>&1; then
        echo "   ❌ Elasticsearch failed to start"
        exit 1
    fi
fi

echo ""
echo "📦 Checking PostgreSQL..."
if docker exec learning_postgres pg_isready -U admin > /dev/null 2>&1; then
    echo "   ✅ PostgreSQL is ready"
else
    echo "   ❌ PostgreSQL not accessible. Restarting..."
    docker-compose restart postgres
    sleep 10
    if ! docker exec learning_postgres pg_isready -U admin > /dev/null 2>&1; then
        echo "   ❌ PostgreSQL failed to start"
        exit 1
    fi
fi

echo ""
echo "💾 Database Backup System..."
mkdir -p "$BACKUP_DIR"

if [ -f "$DB_BACKUP_FILE" ]; then
    echo "   📥 Restoring from backup: $DB_BACKUP_FILE"
    docker exec -i learning_postgres psql -U admin -d products_db < "$DB_BACKUP_FILE" 2>/dev/null || echo "   ⚠️  Restore warning (may be ok if fresh)"
    echo "   ✅ Database restored"
else
    echo "   ℹ️  No backup found. Fresh database."
fi

echo ""
echo "🤖 Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "   ✅ Ollama installed"
    
    if ! pgrep -f "ollama serve" > /dev/null 2>&1; then
        echo "   🚀 Starting Ollama..."
        nohup ollama serve > /dev/null 2>&1 &
        sleep 5
    fi
    
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "   ✅ Ollama running"
        
        if curl -s http://localhost:11434/api/tags | grep -q "llama3.2"; then
            echo "   ✅ Llama 3.2 model found"
        else
            echo "   📥 Pulling Llama 3.2:3b model..."
            ollama pull llama3.2:3b
        fi
    else
        echo "   ❌ Ollama not responding"
        exit 1
    fi
else
    echo "   ❌ Ollama not installed"
    echo "   Install: brew install ollama (macOS) or visit https://ollama.ai"
    exit 1
fi

echo ""
echo "📦 Python Virtual Environment..."
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi
echo "   Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment ready"

echo ""
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip -q
    pip install -q -r requirements.txt
    echo "   ✅ Dependencies installed"
else
    echo "   ❌ requirements.txt not found"
    exit 1
fi

echo ""
echo "🤖 Loading ML Models..."

echo "   📥 Downloading Whisper model (faster-whisper small)..."
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" 2>/dev/null && echo "   ✅ Whisper model ready" || echo "   ⚠️  Whisper will load on first use"

echo "   📥 Downloading Sentence Transformer (all-MiniLM-L6-v2)..."
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" 2>/dev/null && echo "   ✅ Embedding model ready" || echo "   ⚠️  Embedding model will load on first use"

echo "   📥 Downloading Kokoro TTS model..."
python3 -c "from kokoro import KPipeline; KPipeline(lang_code='a')" 2>/dev/null && echo "   ✅ Kokoro TTS ready" || echo "   ⚠️  Kokoro will load on first use"

echo ""
echo "🗄️  Initializing database..."
python3 -c "import models; models.init_db()" && echo "   ✅ Database initialized" || echo "   ❌ Database initialization failed"

echo ""
echo "⏰ Setting up auto-backup (every 30 minutes)..."
cat > "$BACKUP_DIR/backup_db.sh" << 'BACKUP_SCRIPT'
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec learning_postgres pg_dump -U admin -d products_db > "$BACKUP_DIR/postgres_$TIMESTAMP.sql" 2>/dev/null
cp "$BACKUP_DIR/postgres_$TIMESTAMP.sql" "$BACKUP_DIR/postgres_latest.sql"
find "$BACKUP_DIR" -name "postgres_*.sql" -type f -mmin +1440 -delete
echo "$(date): Backup completed"
BACKUP_SCRIPT

chmod +x "$BACKUP_DIR/backup_db.sh"

# Stop any existing backup cron
pkill -f "backup_db.sh" 2>/dev/null || true

# Start background backup loop
(while true; do
    sleep 1800  # 30 minutes
    "$BACKUP_DIR/backup_db.sh" >> "$BACKUP_DIR/backup.log" 2>&1
done) &

echo "   ✅ Auto-backup enabled (30-minute intervals)"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║         Starting Nexva Backend         ║"
echo "╔════════════════════════════════════════╗"
echo ""
echo "🚀 Backend API: http://localhost:$PORT"
echo "📚 API Documentation: http://localhost:$PORT/docs"
echo ""
echo "📝 Quick Commands:"
echo "   • Stop server: Ctrl+C"
echo "   • View logs: tail -f backups/backup.log"
echo "   • Manual backup: ./backups/backup_db.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

source venv/bin/activate
exec uvicorn main:app --reload --host 0.0.0.0 --port $PORT
