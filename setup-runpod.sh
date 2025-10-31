#!/bin/bash

set -e

echo "╔════════════════════════════════════════╗"
echo "║    Nexva Backend Setup (RunPod)        ║"
echo "╔════════════════════════════════════════╗"
echo ""

PORT=8001

echo "🧹 Cleaning up..."
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name '*.pyc' -delete 2>/dev/null || true
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true
sleep 2

echo ""
echo "📦 Installing PostgreSQL..."
if ! command -v psql &> /dev/null; then
    apt-get update -qq
    apt-get install -y postgresql postgresql-contrib >/dev/null 2>&1
fi
service postgresql start || true
sleep 3

su - postgres -c "psql -c \"CREATE USER admin WITH PASSWORD 'admin123';\"" 2>/dev/null || true
su - postgres -c "psql -c \"ALTER USER admin WITH SUPERUSER;\"" 2>/dev/null || true
su - postgres -c "psql -c \"CREATE DATABASE products_db OWNER admin;\"" 2>/dev/null || true
echo "   ✅ PostgreSQL ready"

echo ""
echo "📦 Installing Elasticsearch..."
if ! command -v elasticsearch &> /dev/null; then
    wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add - >/dev/null 2>&1
    echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list >/dev/null
    apt-get update -qq
    apt-get install -y elasticsearch >/dev/null 2>&1
    
    echo "xpack.security.enabled: false" >> /etc/elasticsearch/elasticsearch.yml
    echo "xpack.security.enrollment.enabled: false" >> /etc/elasticsearch/elasticsearch.yml
fi

service elasticsearch start || true
sleep 10

if curl -s http://localhost:9200 > /dev/null 2>&1; then
    echo "   ✅ Elasticsearch ready"
else
    echo "   ⚠️  Elasticsearch starting (may take a moment)"
fi

echo ""
echo "🤖 Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
fi

if ! pgrep -f "ollama serve" > /dev/null 2>&1; then
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
fi

echo ""
echo "📦 Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo ""
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip -q
    pip install -q -r requirements.txt
    echo "   ✅ Dependencies installed"
fi

echo ""
echo "🤖 Loading ML Models..."
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" 2>/dev/null && echo "   ✅ Whisper ready" || echo "   ⚠️  Will load on first use"
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" 2>/dev/null && echo "   ✅ Embeddings ready" || echo "   ⚠️  Will load on first use"

echo ""
echo "🗄️  Initializing database..."
python3 -c "import models; models.init_db()" && echo "   ✅ Database initialized"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║         Starting Nexva Backend         ║"
echo "╔════════════════════════════════════════╗"
echo ""
echo "🚀 Backend API: http://localhost:$PORT"
echo "📚 API Docs: http://localhost:$PORT/docs"
echo ""

source venv/bin/activate
exec uvicorn main:app --reload --host 0.0.0.0 --port $PORT

