# Autonomous UX Analysis Agent

Production-ready AI-powered tool for comprehensive website UX analysis.

## Quick Start

### 1. Installation
```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

### 2. Configuration

Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Run Tests
```bash
python test_agent.py
```

### 4. Launch Gradio Interface
```bash
python gradio_app.py
```

Then open your browser to: `http://localhost:7860`

## Usage

### Via Gradio Interface (Recommended)

1. Enter website URL (e.g., `https://example.com`)
2. Enter website name (e.g., `Example Company`)
3. Configure analysis settings
4. Optionally add login credentials
5. Click "Analyze Website"
6. View results in Summary or JSON tab

### Via Python Code
```python
import asyncio
from ux_agent import UXAnalysisAgent

async def analyze():
    agent = UXAnalysisAgent(headless=True, max_pages=5)
    
    report = await agent.analyze_website(
        target_url="https://example.com"
    )
    
    print(f"Score: {report.overall_design_score}/10")
    print(report.model_dump_json(indent=2))

asyncio.run(analyze())
```

## Project Structure
```
.
├── models.py              # Pydantic data models
├── config.py             # Configuration management
├── browser_manager.py    # Playwright browser control
├── page_analyzer.py      # LLM-powered analysis
├── navigator.py          # Navigation logic
├── session_handler.py    # Login/auth handling
├── ux_agent.py          # Main orchestration
├── gradio_app.py        # Web interface
├── test_agent.py        # Test suite
├── requirements.txt     # Dependencies
└── .env                 # Configuration (create this)
```

## Features

-  Autonomous website navigation
-  AI-powered UX analysis
-  Automatic login handling
-  Cookie consent management
-  Stealth mode (anti-detection)
-  Structured JSON output
-  Web interface (Gradio)
-  Comprehensive error handling

## Troubleshooting

### "OPENAI_API_KEY is required"
Edit `.env` and add your API key.

### "Playwright browsers not installed"
Run: `playwright install chromium`

### "Module not found"
Activate venv: `source venv/bin/activate`
Install deps: `pip install -r requirements.txt`

## Output Format
```json
{
  "url": "https://example.com",
  "overall_design_score": 8.5,
  "pages_analyzed": 5,
  "key_strengths": [...],
  "critical_issues": [...],
  "recommendations": [...],
  "page_analyses": [...]
}
```

## 🤝 Contributing

This is a production-ready POC. Feel free to extend and customize!

## 📄 License

MIT License - Use freely for your agency work.