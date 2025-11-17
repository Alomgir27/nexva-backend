#!/bin/bash

set -e

echo "🚀 Nexva Backend Setup"
echo "======================"
echo ""

# Check for Python 3.11
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✅ Using Python 3.11: $(python3.11 --version)"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" == "3.11" ]] || [[ "$PYTHON_VERSION" == "3.12" ]]; then
        PYTHON_CMD="python3"
        echo "✅ Using: $(python3 --version)"
    else
        echo "❌ Python 3.11 or 3.12 required (you have $(python3 --version))"
        echo ""
        echo "Install Python 3.11:"
        echo "  macOS: brew install python@3.11"
        echo "  Ubuntu: sudo apt install python3.11 python3.11-venv"
        exit 1
    fi
else
    echo "❌ Python 3 not installed"
    echo ""
    echo "Install Python 3.11:"
    echo "  macOS: brew install python@3.11"
    echo "  Ubuntu: sudo apt install python3.11 python3.11-venv"
    exit 1
fi

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment exists"
    read -p "Recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        $PYTHON_CMD -m venv venv
    fi
else
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate and install
echo "📚 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if needed
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file..."
    cat > .env << 'EOF'
DATABASE_URL=postgresql://admin:admin123@localhost:5432/products_db
SECRET_KEY=yes-i-can-i-win
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
CORS_ORIGINS=*
EOF
    echo "✅ .env created - update with your settings"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "📝 Note: Using $PYTHON_CMD"
echo ""
