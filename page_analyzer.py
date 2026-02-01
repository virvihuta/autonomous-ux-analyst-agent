"""
LLM-powered page analysis component for UX evaluation.
"""
import base64
import json
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.async_api import Page
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import logging

from models import PageAnalysis, NavigationAction

logger = logging.getLogger(__name__)


class PageAnalyzer:
    """
    Analyzes page screenshots and DOM using LLM vision capabilities.
    """
    
    # System prompt for UX analysis
    UX_ANALYSIS_PROMPT = """You are an expert UX Analyst and Senior Product Designer with 15+ years of experience evaluating digital products.

Your task is to analyze a website page and provide a comprehensive UX evaluation.

**Analysis Framework:**

1. **Page Type Identification**: Determine what type of page this is (landing page, login, dashboard, product page, checkout, etc.)

2. **Key Elements**: Identify the most important UI elements:
   - Primary CTAs (calls-to-action)
   - Navigation patterns
   - Form elements
   - Visual hierarchy elements
   - Interactive components
   
   For each element, assess its quality (1-10) based on:
   - Visibility and prominence
   - Clarity of purpose
   - Accessibility
   - Visual design quality

3. **UX Friction Points**: Identify usability issues:
   - **High severity**: Blocks users from completing tasks
   - **Medium severity**: Creates confusion or extra steps
   - **Low severity**: Minor annoyances
   
   For each friction point, provide a specific recommendation.

4. **Overall Design Score**: Rate the page design 1-10 considering:
   - Visual hierarchy
   - Consistency
   - Accessibility
   - Modern design principles
   - Mobile responsiveness (if visible)
   - Information architecture

**CRITICAL: You MUST return ONLY valid JSON. No markdown, no code blocks, no explanations.**

Return your analysis as a JSON object matching this EXACT schema:
{
    "page_type": "string",
    "key_elements": [
        {
            "element_type": "string",
            "description": "string",
            "location": "string",
            "quality_score": 8
        }
    ],
    "ux_friction_points": [
        {
            "issue": "string",
            "severity": "low",
            "recommendation": "string"
        }
    ],
    "design_score": 7,
    "accessibility_notes": "string or null",
    "mobile_readiness": "string or null"
}

Be specific, actionable, and honest in your assessment. Focus on what matters most for user experience.
"""

    NAVIGATION_PROMPT = """You are a strategic web navigation agent. Based on the current page analysis, determine the next best action to explore this website's UX.

**Your Goals:**
1. Discover key user flows (signup, login, product browsing, checkout)
2. Explore different page types to get comprehensive UX coverage
3. Avoid repetitive navigation (don't click the same type of element twice)

**Current Context:**
- Pages already visited: {visited_pages}
- Current page type: {current_page_type}

**Available Actions:**
- "click": Click on an interactive element (button, link, etc.)
- "fill": Fill out a form field
- "scroll": Scroll the page to reveal more content
- "wait": Wait for dynamic content to load
- "complete": Analysis is complete, stop exploration

**CRITICAL: You MUST return ONLY valid JSON. No markdown, no code blocks, no explanations.**

Return a JSON object:
{{
    "action": "click",
    "target_description": "what element to interact with (if applicable)",
    "selector_hint": "CSS selector hint or text content (if applicable)",
    "reasoning": "why this action advances our UX exploration"
}}

**Decision Criteria:**
- Prioritize unexplored page types
- Focus on primary user journeys
- Avoid redundant navigation
- If no valuable actions remain, return action: "complete"

Be strategic and efficient in your exploration.
"""
    
    def __init__(self, llm_model: str = "gpt-4-vision-preview", temperature: float = 0.3, max_tokens: int = 4000):
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def capture_page_state(self, page: Page) -> Dict[str, Any]:
        """Capture screenshot and simplified DOM of the current page."""
        try:
            # Capture screenshot
            screenshot_bytes = await page.screenshot(full_page=False, type='png')
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Get and simplify HTML
            html_content = await page.content()
            simplified_dom = self._simplify_html(html_content)
            
            # Get current URL
            current_url = page.url
            
            return {
                'screenshot': screenshot_b64,
                'dom': simplified_dom,
                'url': current_url
            }
        except Exception as e:
            logger.error(f"Failed to capture page state: {e}")
            raise
    
    def _simplify_html(self, html: str, max_length: int = 5000) -> str:
        """Simplify HTML to essential structure for LLM context."""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script and style tags
            for tag in soup(['script', 'style', 'noscript', 'svg']):
                tag.decompose()
            
            # Extract text and basic structure
            simplified_parts = []
            
            # Get title
            title = soup.find('title')
            if title:
                simplified_parts.append(f"<title>{title.get_text().strip()}</title>")
            
            # Get main headings
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                text = heading.get_text().strip()
                if text:
                    simplified_parts.append(f"<{heading.name}>{text}</{heading.name}>")
            
            # Get buttons and links
            for element in soup.find_all(['button', 'a']):
                text = element.get_text().strip()
                if text:
                    tag_name = element.name
                    simplified_parts.append(f"<{tag_name}>{text}</{tag_name}>")
            
            # Get form inputs
            for input_elem in soup.find_all('input'):
                input_type = input_elem.get('type', 'text')
                placeholder = input_elem.get('placeholder', '')
                name = input_elem.get('name', '')
                simplified_parts.append(f"<input type='{input_type}' name='{name}' placeholder='{placeholder}'>")
            
            simplified_html = '\n'.join(simplified_parts)
            
            # Truncate if too long
            if len(simplified_html) > max_length:
                simplified_html = simplified_html[:max_length] + "... [truncated]"
            
            return simplified_html
            
        except Exception as e:
            logger.error(f"Failed to simplify HTML: {e}")
            return html[:max_length]
    
    async def analyze_page(self, page: Page) -> PageAnalysis:
        """Analyze current page and return structured UX evaluation."""
        try:
            # Capture page state
            page_state = await self.capture_page_state(page)
            
            # Construct message with screenshot
            message_content = [
                {
                    "type": "text",
                    "text": f"{self.UX_ANALYSIS_PROMPT}\n\n**Simplified DOM Context:**\n{page_state['dom']}\n\n**Current URL:** {page_state['url']}\n\nPlease analyze this page and return a JSON response."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{page_state['screenshot']}"
                    }
                }
            ]
            
            # Call LLM
            response = await self.llm.ainvoke([HumanMessage(content=message_content)])
            
            # Parse response
            analysis_json = self._extract_json(response.content)
            
            # Validate and return
            return PageAnalysis(**analysis_json)
            
        except Exception as e:
            logger.error(f"Failed to analyze page: {e}")
            # Return default analysis on failure
            return PageAnalysis(
                page_type="unknown",
                key_elements=[],
                ux_friction_points=[],
                design_score=5
            )
    
    async def decide_next_action(
        self,
        page: Page,
        current_analysis: PageAnalysis,
        visited_pages: list
    ) -> NavigationAction:
        """Determine the next navigation action based on current page analysis."""
        try:
            page_state = await self.capture_page_state(page)
            
            # Format the navigation prompt
            prompt = self.NAVIGATION_PROMPT.format(
                visited_pages=", ".join([p for p in visited_pages]) if visited_pages else "None",
                current_page_type=current_analysis.page_type
            )
            
            message_content = [
                {
                    "type": "text",
                    "text": f"{prompt}\n\n**Current Page Analysis:**\n{current_analysis.model_dump_json(indent=2)}\n\n**Simplified DOM:**\n{page_state['dom']}\n\nWhat should be the next action?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{page_state['screenshot']}"
                    }
                }
            ]
            
            response = await self.llm.ainvoke([HumanMessage(content=message_content)])
            
            action_json = self._extract_json(response.content)
            
            return NavigationAction(**action_json)
            
        except Exception as e:
            logger.error(f"Failed to decide next action: {e}")
            # Return complete action on failure
            return NavigationAction(
                action="complete",
                reasoning="Error occurred during decision making"
            )
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text with robust error handling."""
        try:
            # Remove markdown code blocks if present
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            text = text.strip()
            
            # Try to find JSON block
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Try parsing entire text
                return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Response text: {text}")
            
            # Try to extract JSON more aggressively
            try:
                # Look for array or object patterns
                json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
                matches = re.findall(json_pattern, text, re.DOTALL)
                if matches:
                    # Try the longest match
                    longest_match = max(matches, key=len)
                    return json.loads(longest_match)
            except:
                pass
            
            raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")