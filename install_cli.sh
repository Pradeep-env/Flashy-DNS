#!/bin/bash

set -e

REPO_RAW="https://raw.githubusercontent.com/Pradeep-env/Flashy-DNS/main/backend"
INSTALL_DIR="$HOME/flashy-dns-cli"

echo "⚡ Installing Flashy DNS (CLI only)"
echo "📁 Target directory: $INSTALL_DIR"

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "⬇️  Downloading CLI files..."
curl -fsSL "$REPO_RAW/benchmark.py" -o benchmark.py
curl -fsSL "$REPO_RAW/flashy_dns.py" -o flashy_dns.py

echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Try installing requirements.txt if it exists remotely
echo "📦 Installing dependencies..."
if curl -fsSL "$REPO_RAW/requirements.txt" -o requirements.txt; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, installing minimal dependencies"
    pip install dnspython
fi

echo ""
echo "✅ Flashy DNS CLI installed successfully"
echo ""
echo "👉 Change Directory:"
echo "   cd $INSTALL_DIR/"
echo ""
echo "👉 Activate environment:"
echo "   source venv/bin/activate"
echo ""
echo "👉 Run:"
echo "   python flashy_dns.py -r 1.1.1.1 8.8.8.8 -t 20 --live"
