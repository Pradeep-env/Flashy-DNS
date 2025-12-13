#!/bin/bash

set -e

REPO_URL="https://github.com/Pradeep-env/Flashy-DNS.git"
INSTALL_DIR="$HOME/Flashy-DNS"

echo "⚡ Installing Flashy DNS (Full version)"
echo "📁 Target directory: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "❌ Directory already exists: $INSTALL_DIR"
    echo "Remove it or choose another location."
    exit 1
fi

git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

echo ""
echo "✅ Flashy DNS full installation complete"
echo ""
echo "👉 Activate environment:"
echo "   source $INSTALL_DIR/venv/bin/activate"
echo ""
echo "👉 Start GUI server:"
echo "   uvicorn backend.server:app --reload"
echo ""
echo "👉 Open browser:"
echo "   http://127.0.0.1:8000"
