# Nexva Backend API

AI-powered chatbot platform with voice chat, document processing, and real-time websocket support.

🌐 **Live Demo**: https://nexva.pages.dev/

## Features

- 🤖 **AI Chatbot** - LLM-powered conversations using Ollama (Llama 3.2)
- 🎙️ **Voice Chat** - Real-time voice interaction with STT/TTS
- 📄 **Document Processing** - Upload and process PDF, DOCX, TXT files
- 🔍 **Smart Search** - Vector search with Elasticsearch + semantic embeddings
- 🌐 **Web Scraping** - Automated content extraction from domains
- 💬 **WebSocket** - Real-time chat and voice streaming
- 👥 **Human Support** - Live agent handoff capability
- ☁️ **Cloud Storage** - Cloudflare R2 integration for file uploads
- 🔐 **Authentication** - JWT-based user authentication

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL + SQLAlchemy
- **Search**: Elasticsearch 8.x
- **LLM**: Ollama (Llama 3.2:3b)
- **Voice**: Faster-Whisper (STT) + Kokoro TTS
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Storage**: Cloudflare R2 (S3-compatible)
- **Web Scraping**: Selenium + BeautifulSoup

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Elasticsearch 8.x
- Ollama with Llama 3.2:3b model
- Cloudflare R2 account (optional, for cloud storage)

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Alomgir27/nexva-backend.git
cd nexva-backend
```

### 2. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Setup Environment

Create `.env` file in project root:

```env
# Database
DATABASE_URL=postgresql://admin:admin123@localhost:5432/products_db

# Security
SECRET_KEY=your-secret-key-change-this-in-production

# Ollama LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Cloudflare R2 Storage (Optional)
USE_R2_STORAGE=false
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=your-bucket-name
R2_PUBLIC_URL=https://pub-xxxxxxxx.r2.dev

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@example.com

# Stripe (Optional)
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

### 4. Setup Services

#### PostgreSQL
```bash
# Install PostgreSQL
brew install postgresql  # macOS
# or: apt-get install postgresql  # Linux

# Start service
brew services start postgresql  # macOS
# or: sudo service postgresql start  # Linux

# Create database
psql postgres
CREATE DATABASE products_db;
CREATE USER admin WITH PASSWORD 'admin123';
GRANT ALL PRIVILEGES ON DATABASE products_db TO admin;
\q
```

#### Elasticsearch
```bash
# Install Elasticsearch 8.x
brew tap elastic/tap
brew install elastic/tap/elasticsearch-full

# Configure (disable security for local dev)
echo "xpack.security.enabled: false" >> /usr/local/etc/elasticsearch/elasticsearch.yml

# Start service
brew services start elasticsearch
# or: sudo systemctl start elasticsearch
```

#### Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start service
ollama serve &

# Pull model
ollama pull llama3.2:3b
```

### 5. Run Backend

```bash
# Development mode (auto-reload)
python run.py

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or use setup script (installs all dependencies)
./setup.sh
```

API will be available at:
- **Docs**: http://localhost:8000/docs
- **API**: http://localhost:8000/api

## Project Structure

```
nexva-backend/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoints
│   │       ├── auth.py      # Authentication
│   │       ├── chatbots.py  # Chatbot management
│   │       ├── domains.py   # Domain & document upload
│   │       ├── scraping.py  # Web scraping
│   │       ├── support.py   # Human support
│   │       └── websockets.py # WebSocket handlers
│   ├── core/
│   │   └── config.py        # App configuration
│   ├── database/
│   │   ├── models.py        # SQLAlchemy models
│   │   └── session.py       # DB session management
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── auth.py          # Auth service
│   │   ├── chat.py          # Chat logic
│   │   ├── search.py        # Elasticsearch + embeddings
│   │   ├── scraper.py       # Web scraping
│   │   ├── realtime_voice_service.py  # Voice chat
│   │   ├── r2_storage.py    # Cloudflare R2 uploads
│   │   └── websocket_handler.py
│   └── main.py              # FastAPI app
├── widget/                  # Chat widget (vanilla JS)
├── requirements.txt
└── run.py
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Chatbots
- `GET /api/chatbots` - List user's chatbots
- `POST /api/chatbots` - Create chatbot
- `PUT /api/chatbots/{id}` - Update chatbot
- `DELETE /api/chatbots/{id}` - Delete chatbot

### Domains & Documents
- `POST /api/domains` - Add domain to chatbot
- `POST /api/domains/{id}/scrape` - Scrape domain content
- `POST /api/domains/{id}/documents` - Upload document
- `GET /api/domains/{id}/documents` - List documents
- `DELETE /api/documents/{id}` - Delete document

### WebSocket
- `ws://localhost:8000/ws/chat/{api_key}` - Text chat
- `ws://localhost:8000/ws/voice-chat/{api_key}` - Voice chat
- `ws://localhost:8000/ws/support/{ticket_id}` - Support chat

## Voice Chat

The voice chat feature provides real-time voice interaction:

### Features
- **Speech-to-Text**: Faster-Whisper (local)
- **Text-to-Speech**: Kokoro TTS (neural voice)
- **Streaming**: Real-time audio streaming via WebSocket
- **Low Latency**: Optimized for fast responses
  - Context limited to 600 chars (standard) / 1600 chars (code)
  - Searches top 4 results, uses top 2 for context
  - Responses capped at 60 words for natural voice delivery

### Usage
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/voice-chat/YOUR_API_KEY');

ws.onopen = () => {
  // Send text query
  ws.send(JSON.stringify({
    type: "text_query",
    text: "What are your pricing plans?"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "text_chunk") {
    console.log("Text:", data.text);
  }
  
  if (data.type === "audio_chunk") {
    // Play audio (base64 encoded WAV)
    const audioBlob = new Blob([
      Uint8Array.from(atob(data.audio), c => c.charCodeAt(0))
    ], { type: 'audio/wav' });
    // ... play audioBlob
  }
};
```

## Storage Configuration

### Local Storage (Default)
Files stored in `uploads/documents/` directory.

### Cloudflare R2 (Recommended for Production)
1. Create R2 bucket at https://dash.cloudflare.com/
2. Generate API token
3. Update `.env`:
```env
USE_R2_STORAGE=true
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-key
R2_SECRET_ACCESS_KEY=your-secret
R2_BUCKET_NAME=your-bucket
R2_PUBLIC_URL=https://pub-xxxxx.r2.dev
```

Files will be uploaded to R2 with public URLs.

## Deployment

### RunPod (GPU Cloud)
```bash
./setup-runpod.sh
```

### Docker
```bash
docker-compose up -d
```

### Manual
```bash
# Install dependencies
pip install -r requirements.txt

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | JWT signing key |
| `OLLAMA_HOST` | Yes | http://localhost:11434 | Ollama API endpoint |
| `OLLAMA_MODEL` | Yes | llama3.2:3b | LLM model name |
| `USE_R2_STORAGE` | No | false | Enable Cloudflare R2 |
| `R2_ACCOUNT_ID` | No | - | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | No | - | R2 access key |
| `R2_SECRET_ACCESS_KEY` | No | - | R2 secret key |
| `R2_BUCKET_NAME` | No | - | R2 bucket name |
| `R2_PUBLIC_URL` | No | - | R2 public URL |

## Performance Optimizations

- **Embedding Model**: Lazy-loaded on first search
- **Search**: Vector + keyword hybrid with cosine similarity
- **Voice Chat**: 
  - Query keyword extraction reduces context overhead
  - Limited to 2 context chunks (600 chars each)
  - TTS triggers every 140 chars or after first sentence
- **WebSocket**: Concurrent task handling with interruption support

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Elasticsearch Connection Failed
```bash
# Check status
curl http://localhost:9200

# Restart service
brew services restart elasticsearch
```

### Ollama Model Not Found
```bash
ollama pull llama3.2:3b
```

### R2 Upload Failed
- Verify credentials in `.env`
- Check bucket permissions (public read)
- Ensure `boto3` is installed: `pip install boto3`

## License

MIT

## Support

- **Issues**: https://github.com/Alomgir27/nexva-backend/issues
- **Docs**: http://localhost:8000/docs

