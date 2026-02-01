#!/bin/bash

echo "🚀 Setting up UX Analysis Agent..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p reports
mkdir -p cookies

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# OpenAI API Key (required)
OPENAI_API_KEY=your-api-key-here

# LLM Configuration
LLM_MODEL=gpt-4-vision-preview
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4000

# Browser Configuration
BROWSER_HEADLESS=false
BROWSER_VIEWPORT_WIDTH=1920
BROWSER_VIEWPORT_HEIGHT=1080
BROWSER_TIMEOUT=30000

# Analysis Configuration
MAX_PAGES_TO_EXPLORE=5
SCREENSHOT_QUALITY=80
MAX_NAVIGATION_DEPTH=3

# Stealth Mode
USE_STEALTH_MODE=true
EOL
    echo "⚠️  Please edit .env and add your OpenAI API key!"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. Run tests: python test_agent.py"
echo "3. Launch Gradio: python gradio_app.py"
echo ""