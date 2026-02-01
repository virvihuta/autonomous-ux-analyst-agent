"""
Production browser management with enterprise features.
"""
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

logger = logging.getLogger(__name__)


class BrowserManager:
    """Enterprise-grade browser automation."""
    
    def __init__(
        self,
        headless: bool = True,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        timeout: int = 30000
    ):
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.timeout = timeout
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def initialize(self) -> None:
        """Initialize browser with anti-detection."""
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': self.viewport_width, 'height': self.viewport_height},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        
        self.context.set_default_timeout(self.timeout)
        self.page = await self.context.new_page()
        
        logger.info("Browser initialized")
        
    async def navigate(self, url: str, retries: int = 2) -> None:
        """Navigate with error handling and retries."""
        last_error = None
        
        for attempt in range(retries):
            try:
                logger.info(f"Navigating to {url} (attempt {attempt + 1}/{retries})")
                
                # Try with networkidle first (most reliable but slower)
                try:
                    await self.page.goto(url, wait_until='networkidle', timeout=30000)
                except Exception as e:
                    logger.warning(f"networkidle failed, trying 'load': {e}")
                    # Fallback to 'load' (faster, less strict)
                    await self.page.goto(url, wait_until='load', timeout=20000)
                
                # Give page time to settle
                await asyncio.sleep(2)
                
                # Dismiss popups
                await self._dismiss_popups()
                
                logger.info(f"Successfully navigated to {url}")
                return
                
            except Exception as e:
                last_error = e
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                
                if attempt < retries - 1:
                    logger.info(f"Retrying in 3 seconds...")
                    await asyncio.sleep(3)
                else:
                    logger.error(f"All navigation attempts failed for {url}")
                    raise last_error
    
    async def _dismiss_popups(self) -> None:
        """Auto-dismiss cookie banners and popups."""
        selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("Accept All")',
            'button:has-text("I agree")',
            'button:has-text("I Agree")',
            '[aria-label*="Accept"]',
            '[aria-label*="accept"]',
            'button:has-text("OK")',
            'button:has-text("Close")',
            '.cookie-accept',
            '#cookie-accept',
            '.accept-cookies'
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible(timeout=2000):
                    await element.click(timeout=2000)
                    await asyncio.sleep(0.5)
                    logger.info(f"Dismissed popup: {selector}")
                    break
            except:
                continue
    
    async def close(self) -> None:
        """Clean shutdown."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")