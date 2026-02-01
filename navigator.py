"""
Navigation logic engine that executes actions based on LLM decisions.
"""
import asyncio
from typing import Optional
from playwright.async_api import Page
import logging

from models import NavigationAction

logger = logging.getLogger(__name__)


class Navigator:
    """
    Executes navigation actions decided by the PageAnalyzer.
    """
    
    def __init__(self):
        self.navigation_history = []
    
    async def execute_action(self, page: Page, action: NavigationAction) -> bool:
        """
        Execute the decided navigation action.
        Returns True if action was successful, False otherwise.
        """
        try:
            logger.info(f"Executing action: {action.action} - {action.reasoning}")
            
            if action.action == "click":
                return await self._execute_click(page, action)
            elif action.action == "scroll":
                return await self._execute_scroll(page)
            elif action.action == "wait":
                return await self._execute_wait(page)
            elif action.action == "fill":
                return await self._execute_fill(page, action)
            elif action.action == "complete":
                logger.info("Navigation complete")
                return True
            else:
                logger.warning(f"Unknown action type: {action.action}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to execute action {action.action}: {e}")
            return False
    
    async def _execute_click(self, page: Page, action: NavigationAction) -> bool:
        """Execute a click action."""
        try:
            if not action.target_description and not action.selector_hint:
                logger.warning("No target specified for click action")
                return False
            
            # Try to find element by selector hint first
            if action.selector_hint:
                try:
                    # Try direct selector
                    element = page.locator(action.selector_hint).first
                    if await element.is_visible(timeout=5000):
                        await element.click()
                        logger.info(f"Clicked element by selector: {action.selector_hint}")
                        await asyncio.sleep(2)  # Wait for navigation
                        return True
                except:
                    pass
                
                # Try text-based selector
                try:
                    element = page.get_by_text(action.selector_hint).first
                    if await element.is_visible(timeout=5000):
                        await element.click()
                        logger.info(f"Clicked element by text: {action.selector_hint}")
                        await asyncio.sleep(2)
                        return True
                except:
                    pass
            
            # Try by description (partial text match)
            if action.target_description:
                # Split description into keywords
                keywords = action.target_description.lower().split()
                
                for keyword in keywords:
                    if len(keyword) < 3:  # Skip very short keywords
                        continue
                    try:
                        element = page.get_by_text(keyword, exact=False).first
                        if await element.is_visible(timeout=3000):
                            await element.click()
                            logger.info(f"Clicked element by keyword: {keyword}")
                            await asyncio.sleep(2)
                            return True
                    except:
                        continue
            
            logger.warning("Could not find element to click")
            return False
            
        except Exception as e:
            logger.error(f"Click action failed: {e}")
            return False
    
    async def _execute_scroll(self, page: Page) -> bool:
        """Execute a scroll action."""
        try:
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1)
            logger.info("Scrolled page")
            return True
        except Exception as e:
            logger.error(f"Scroll action failed: {e}")
            return False
    
    async def _execute_wait(self, page: Page) -> bool:
        """Execute a wait action."""
        try:
            await asyncio.sleep(3)
            logger.info("Waited for page load")
            return True
        except Exception as e:
            logger.error(f"Wait action failed: {e}")
            return False
    
    async def _execute_fill(self, page: Page, action: NavigationAction) -> bool:
        """Execute a form fill action."""
        # This is a simplified version
        # In production, you'd need more context about what to fill
        logger.warning("Fill action not fully implemented")
        return False
    
    def add_to_history(self, url: str, page_type: str) -> None:
        """Track navigation history."""
        self.navigation_history.append({
            'url': url,
            'page_type': page_type
        })
    
    def get_visited_page_types(self) -> list:
        """Get list of visited page types."""
        return [item['page_type'] for item in self.navigation_history]
