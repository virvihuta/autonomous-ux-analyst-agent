"""
LLM-powered functional specification extractor.
"""
import base64
import json
import re
from typing import Dict, Any
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import Page
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import logging

from config import settings

logger = logging.getLogger(__name__)


REVERSE_ENGINEERING_PROMPT = """You are a Replication Engineer analyzing web pages to create implementation blueprints.

**YOUR GOAL:** Extract precise specifications that allow a developer to recreate this page from scratch.

**ANALYSIS FRAMEWORK:**

1. **Layout Engine:** Identify the CSS layout system
   - "CSS Grid", "Flexbox", "12-column Bootstrap", "Custom Grid", "Float-based", "Absolute Positioning"

2. **Design System Tokens:**
   - Primary color (hex code from main CTAs/brand elements)
   - Secondary color (hex code from accents)
   - Background color (hex code)
   - Text color (hex code for body text)
   - Font family (e.g., "Inter, sans-serif")
   - Button style (comprehensive description: "8px radius, 600 weight, 12px vertical padding, 24px horizontal, solid background")

3. **Components:** For each interactive/major component, document:
   - **Name:** Descriptive name (e.g., "Hero CTA Button", "Product Filter Sidebar")
   - **Location:** Where it appears (e.g., "Top right header", "Left sidebar", "Center of hero section")
   - **Functionality:** What it does (e.g., "Filters product list by category", "Opens signup modal")
   - **Data Inputs:** List field names/types if it's a form (e.g., ["email: type=email, required", "password: type=password, minLength=8"])
   - **Trigger Events:** User interactions (e.g., ["onClick -> POST /api/subscribe", "onHover -> show dropdown"])

**CRITICAL RULES:**
- Be DESCRIPTIVE, not judgmental
- Extract exact hex codes from the screenshot
- Focus on "how to rebuild it", not "how good it is"
- Return ONLY valid JSON

**OUTPUT SCHEMA:**
```json
{{
  "template_name": "Homepage | Product Detail | Category Listing | etc",
  "layout_engine": "CSS Grid | Flexbox | etc",
  "design_system": {{
    "primary_color": "#RRGGBB",
    "secondary_color": "#RRGGBB or null",
    "background_color": "#RRGGBB",
    "text_color": "#RRGGBB",
    "font_family": "Font Name, fallback",
    "button_style": "detailed description"
  }},
  "components": [
    {{
      "name": "Component Name",
      "location": "where it appears",
      "functionality": "what it does",
      "data_inputs": ["field descriptions"],
      "trigger_events": ["interaction descriptions"]
    }}
  ]
}}
```

**DOM CONTEXT:**
{dom}

**URL:**
{url}

Analyze the screenshot and DOM to produce the replication blueprint JSON.
"""


class FunctionalAnalyzer:
    """Reverse engineering analysis engine."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key
        )
    
    async def analyze(self, page: Page, template_pattern: str, output_dir: Path) -> Dict[str, Any]:
        """Analyze page and return blueprint data."""
        try:
            logger.info(f"Analyzing: {template_pattern}")
            
            # Capture state
            screenshot_b64 = await self._capture_screenshot(page)
            dom = await self._extract_dom(page)
            url = page.url
            
            # Save screenshot
            screenshot_path = output_dir / f"screenshot_{template_pattern.replace('/', '_')}.png"
            screenshot_bytes = base64.b64decode(screenshot_b64)
            screenshot_path.write_bytes(screenshot_bytes)
            
            # Analyze with LLM
            prompt = REVERSE_ENGINEERING_PROMPT.format(dom=dom, url=url)
            
            response = await self.llm.ainvoke([
                HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
                ])
            ])
            
            # Parse JSON
            spec_data = self._extract_json(response.content)
            
            # Add metadata
            spec_data['template_pattern'] = template_pattern
            spec_data['analyzed_url'] = url
            spec_data['screenshot_path'] = str(screenshot_path.relative_to(output_dir.parent))
            spec_data['status'] = 'success'
            
            return spec_data
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return failed spec
            return {
                'template_name': 'unknown',
                'template_pattern': template_pattern,
                'layout_engine': 'unknown',
                'design_system': {
                    'primary_color': '#000000',
                    'background_color': '#ffffff',
                    'text_color': '#000000',
                    'font_family': 'unknown',
                    'button_style': 'unknown'
                },
                'components': [],
                'analyzed_url': page.url,
                'status': 'failed',
                'error_message': str(e)
            }
    
    async def _capture_screenshot(self, page: Page) -> str:
        """Capture and encode screenshot."""
        screenshot = await page.screenshot(full_page=False, type='png')
        return base64.b64encode(screenshot).decode()
    
    async def _extract_dom(self, page: Page) -> str:
        """Simplify DOM for analysis."""
        html = await page.content()
        soup = BeautifulSoup(html, 'lxml')
        
        for tag in soup(['script', 'style', 'noscript', 'svg']):
            tag.decompose()
        
        parts = []
        
        if soup.title:
            parts.append(f"<title>{soup.title.string}</title>")
        
        for h in soup.find_all(['h1', 'h2', 'h3']):
            parts.append(f"<{h.name}>{h.get_text()[:100]}</{h.name}>")
        
        for form in soup.find_all('form'):
            parts.append(f"<form action='{form.get('action', '')}' method='{form.get('method', 'GET')}'>")
            for inp in form.find_all(['input', 'select']):
                parts.append(f"  <input type='{inp.get('type', 'text')}' name='{inp.get('name', '')}'>")
            parts.append("</form>")
        
        for btn in soup.find_all(['button', 'a'])[:30]:
            text = btn.get_text()[:50]
            if text:
                parts.append(f"<{btn.name} href='{btn.get('href', '')}'>{text}</{btn.name}>")
        
        return '\n'.join(parts)[:6000]
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from response."""
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text).strip()
        
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        
        raise ValueError("No valid JSON in response")