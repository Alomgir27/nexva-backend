#!/bin/bash

set -e

echo "╔════════════════════════════════════════╗"
echo "║    Nexva Backend Setup (RunPod)        ║"
echo "╚════════════════════════════════════════╝"
echo ""

PORT=5000

echo "🧹 Cleaning up..."
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name '*.pyc' -delete 2>/dev/null || true

echo "🔪 Freeing port $PORT..."
apt-get install -y lsof psmisc net-tools ffmpeg >/dev/null 2>&1 || true

# Kill existing processes
pkill -9 -f "/workspace/nexva-backend.*uvicorn" 2>/dev/null || true
pkill -9 -f "uvicorn main:app" 2>/dev/null || true

# Force kill port connections
ss -K dport = $PORT 2>/dev/null || true
fuser -9 -k $PORT/tcp 2>/dev/null || true
sleep 3

# Verify port is free
if ss -tulpn | grep -q ":$PORT "; then
    echo "   ⚠️  Port $PORT still in use, forcing kill..."
    ss -tulpn | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | xargs -r kill -9 2>/dev/null || true
    sleep 2
fi

echo "   ✅ Port $PORT ready"

echo ""
echo "📦 Installing PostgreSQL..."
if ! command -v psql &> /dev/null; then
    apt-get update -qq
    apt-get install -y postgresql postgresql-contrib >/dev/null 2>&1
fi
service postgresql restart || service postgresql start || true
sleep 3

# Idempotent user/database creation
su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='admin'\" | grep -q 1 || psql -c \"CREATE USER admin WITH PASSWORD 'admin123' SUPERUSER;\"" 2>/dev/null || true
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='products_db'\" | grep -q 1 || psql -c \"CREATE DATABASE products_db OWNER admin;\"" 2>/dev/null || true
echo "   ✅ PostgreSQL ready"

echo ""
echo "📦 Installing Elasticsearch..."
if ! pgrep -f "org.elasticsearch.bootstrap.Elasticsearch" > /dev/null 2>&1; then
    if ! command -v elasticsearch &> /dev/null; then
        wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch 2>/dev/null | apt-key add - >/dev/null 2>&1
        echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" > /etc/apt/sources.list.d/elastic-8.x.list
        apt-get update -qq 2>/dev/null
        apt-get install -y elasticsearch >/dev/null 2>&1
        
        cat > /etc/elasticsearch/elasticsearch.yml << EOF
cluster.name: nexva-cluster
node.name: nexva-node
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 127.0.0.1
http.port: 9200
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false
discovery.type: single-node
EOF
        
        chown -R elasticsearch:elasticsearch /var/lib/elasticsearch /var/log/elasticsearch /etc/elasticsearch
    fi
    
    pkill -9 -f "org.elasticsearch.bootstrap.Elasticsearch" 2>/dev/null || true
    sleep 2
    
    rm -f /etc/elasticsearch/elasticsearch.keystore 2>/dev/null || true
    sysctl -w vm.max_map_count=262144 >/dev/null 2>&1 || true
    
    echo "   🚀 Starting Elasticsearch..."
    runuser -u elasticsearch -- /usr/share/elasticsearch/bin/elasticsearch -d -p /tmp/elasticsearch.pid 2>/dev/null || \
    su -s /bin/bash elasticsearch -c "ES_JAVA_HOME=/usr/share/elasticsearch/jdk /usr/share/elasticsearch/bin/elasticsearch -d" 2>/dev/null
    
    echo "   Waiting for Elasticsearch..."
    for i in {1..20}; do
        if curl -s http://localhost:9200 | grep -q "You Know, for Search"; then
            echo "   ✅ Elasticsearch ready"
            break
        fi
        sleep 2
        if [ $i -eq 20 ]; then
            echo "   ⚠️  Elasticsearch not responding (non-critical, continuing)"
        fi
    done
else
    echo "   ✅ Elasticsearch already running"
fi

echo ""
echo "🤖 Installing Ollama (CPU mode)..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
fi

if ! pgrep -f "ollama serve" > /dev/null 2>&1; then
    pkill -f "ollama serve" 2>/dev/null || true
    nohup ollama serve > /dev/null 2>&1 &
    sleep 5
fi

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama running (CPU)"
    
    if curl -s http://localhost:11434/api/tags | grep -q "llama3.2"; then
        echo "   ✅ Llama 3.2 model found"
    else
        echo "   📥 Pulling Llama 3.2:3b model (CPU)..."
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

# echo ""
# echo "🤖 Loading ML Models..."
# python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" 2>/dev/null && echo "   ✅ Whisper ready" || echo "   ⚠️  Will load on first use"
# python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" 2>/dev/null && echo "   ✅ Embeddings ready" || echo "   ⚠️  Will load on first use"

echo ""
echo "🗄️  Initializing database..."
python3 -c "import models; models.init_db()" && echo "   ✅ Database initialized"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║         Starting Nexva Backend         ║"
echo "╔════════════════════════════════════════╗"
echo ""
echo "🚀 Backend API: http://0.0.0.0:$PORT"
echo "📚 API Docs: http://localhost:$PORT/docs"
echo ""
echo "📝 Server running in background..."
echo "   • View logs: tail -f nohup.out"
echo "   • Stop server: pkill -f 'uvicorn main:app'"
echo ""

source venv/bin/activate
nohup uvicorn main:app --reload --host 0.0.0.0 --port $PORT > nohup.out 2>&1 &
BACKEND_PID=$!

echo "   Waiting for backend to start..."
sleep 5

if curl -s http://localhost:$PORT/docs > /dev/null 2>&1; then
    echo "✅ Backend started successfully (PID: $BACKEND_PID)"
    echo ""
    echo "🌐 Access your API:"
    echo "   Local:  http://localhost:$PORT"
    echo "   Docs:   http://localhost:$PORT/docs"
    echo "   RunPod: https://yueihds3xl383a-$PORT.proxy.runpod.net/docs"
    echo ""
    echo "📋 Management:"
    echo "   • View logs: tail -f nohup.out"
    echo "   • Stop: pkill -f 'uvicorn main:app'"
    echo ""
elif ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "⚠️  Backend process running but not responding yet"
    echo "   Wait ~10 seconds, then check: curl http://localhost:$PORT"
    echo "   View logs: tail -f nohup.out"
    echo ""
else
    echo "❌ Backend failed to start"
    echo ""
    echo "📋 Recent logs:"
    tail -20 nohup.out
    echo ""
    exit 1
fi

