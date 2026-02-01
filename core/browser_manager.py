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
        
    async def navigate(self, url: str) -> None:
        """Navigate with error handling."""
        try:
            await self.page.goto(url, wait_until='networkidle', timeout=self.timeout)
            await asyncio.sleep(1)
            await self._dismiss_popups()
            logger.info(f"Navigated to {url}")
        except Exception as e:
            logger.error(f"Navigation failed for {url}: {e}")
            raise
    
    async def _dismiss_popups(self) -> None:
        """Auto-dismiss cookie banners and popups."""
        selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("I agree")',
            '[aria-label*="Accept"]'
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible(timeout=2000):
                    await element.click(timeout=2000)
                    await asyncio.sleep(0.5)
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