#!/bin/bash
# Quick setup script for the Lightweight Coding Assistant

echo "🚀 Setting up Lightweight Local Coding Assistant"
echo "================================================"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found!"
    echo "📥 Install from: https://ollama.ai"
    echo ""
    echo "Installation commands:"
    echo "  macOS/Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  Windows: Download from https://ollama.ai/download"
    exit 1
fi

echo "✅ Ollama found: $(which ollama)"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama service not running"
    echo "🔄 Starting Ollama..."
    ollama serve &> /dev/null &
    sleep 2
fi

echo "✅ Ollama service is running"
echo ""

# Check for available models
echo "📦 Checking for coding models..."
MODELS=$(ollama list 2>/dev/null | grep -E 'codellama|deepseek-coder|qwen.*coder' | wc -l)

if [ "$MODELS" -eq 0 ]; then
    echo "⚠️  No coding models found"
    echo "📥 Pulling recommended model: codellama (7B)"
    echo "   This may take a few minutes..."
    ollama pull codellama
else
    echo "✅ Found $MODELS coding model(s)"
    ollama list | grep -E 'codellama|deepseek-coder|qwen.*coder'
fi

echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt

echo "✅ Dependencies installed"
echo ""

# Make executable
chmod +x coding_agent.py

echo "🎉 Setup complete!"
echo ""
echo "Usage examples:"
echo "  Interactive mode:     python coding_agent.py"
echo "  Analyze file:         python coding_agent.py --file example_test.py --task review"
echo "  Quick question:       python coding_agent.py --prompt 'How do I...?'"
echo "  List models:          python coding_agent.py --list-models"
echo ""
echo "See README.md for full documentation"
