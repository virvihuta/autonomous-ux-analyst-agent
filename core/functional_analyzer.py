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

from models import FunctionalSpec
from config import settings

logger = logging.getLogger(__name__)


REVERSE_ENGINEERING_PROMPT = """You are a Senior Software Architect performing reverse engineering analysis.

**YOUR ROLE:** Produce FUNCTIONAL SPECIFICATIONS describing HOW this page works for reimplementation.

**RULES:**
1. DESCRIPTIVE, not judgmental
2. PRECISE technical terminology
3. COMPREHENSIVE documentation
4. Return ONLY valid JSON

**OUTPUT SCHEMA:**
```json
{
  "page_template_type": "homepage|product_detail|product_listing|article_content|user_dashboard|auth_portal|checkout_flow|profile_page|search_results|static_page|custom_application",
  
  "layout_structure": {
    "grid_system": "describe layout system",
    "responsive_behavior": "breakpoint behavior",
    "main_sections": ["header", "hero", "content", "footer"]
  },
  
  "interactive_components": [
    {
      "name": "Component Name",
      "location": "where it appears",
      "trigger_events": ["onClick -> action", "onSubmit -> POST /api/endpoint"],
      "data_inputs": ["field: type, required, validation"],
      "visual_state": "state changes description"
    }
  ],
  
  "design_system": {
    "primary_color": "#RRGGBB",
    "secondary_color": "#RRGGBB",
    "background_color": "#RRGGBB",
    "text_color": "#RRGGBB",
    "font_family": "font name",
    "heading_font": "heading font or null",
    "button_styles": "comprehensive button description",
    "spacing_system": "spacing pattern or null"
  },
  
  "navigation": [
    {"text": "Link Text", "target": "/url", "type": "main_nav|footer_nav|cta"}
  ],
  
  "technical_details": {
    "javascript_framework": "React|Vue|Angular|null",
    "form_submission_method": "POST|GET|null",
    "ajax_behavior": true|false,
    "lazy_loading": true|false,
    "api_endpoints": ["/api/endpoint1"]
  },
  
  "third_party_integrations": ["service names"]
}
```

**ANALYZE:** Describe what exists. Extract colors from screenshot. Document all interactions.

**DOM:**
{dom}

**URL:** {url}
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
    
    async def analyze(self, page: Page, template_pattern: str, output_dir: Path) -> FunctionalSpec:
        """Analyze page and return specification."""
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
            
            # Build spec
            spec = FunctionalSpec(
                **spec_data,
                template_pattern=template_pattern,
                analyzed_url=url,
                screenshot_path=str(screenshot_path.relative_to(output_dir.parent))
            )
            
            return spec
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
    
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