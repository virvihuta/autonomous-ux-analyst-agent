"""
Manages Playwright browser lifecycle, stealth configuration, and session persistence.
"""
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Handles browser initialization, stealth mode, and context management.
    """
    
    def __init__(
        self,
        headless: bool = False,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        timeout: int = 30000,
        use_stealth: bool = True
    ):
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.timeout = timeout
        self.use_stealth = use_stealth
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def initialize(self) -> None:
        """Initialize Playwright and browser instance with stealth configuration."""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with stealth arguments
            launch_args = []
            if self.use_stealth:
                launch_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=launch_args
            )
            
            # Create context with stealth settings
            self.context = await self.browser.new_context(
                viewport={'width': self.viewport_width, 'height': self.viewport_height},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
            )
            
            # Add stealth scripts
            if self.use_stealth:
                await self.context.add_init_script("""
                    // Overwrite the `navigator.webdriver` property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // Overwrite the `plugins` property
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Overwrite the `languages` property
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                """)
            
            # Set default timeout
            self.context.set_default_timeout(self.timeout)
            
            # Create initial page
            self.page = await self.context.new_page()
            
            logger.info("Browser initialized successfully with stealth mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def save_cookies(self, filepath: Path) -> None:
        """Save current browser cookies to file."""
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        try:
            cookies = await self.context.cookies()
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"Cookies saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            raise
    
    async def load_cookies(self, filepath: Path) -> None:
        """Load cookies from file into browser context."""
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        try:
            if filepath.exists():
                with open(filepath, 'r') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                logger.info(f"Cookies loaded from {filepath}")
            else:
                logger.warning(f"Cookie file not found: {filepath}")
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            raise
    
    async def handle_popups(self) -> None:
        """Automatically handle common popups and cookie consents."""
        if not self.page:
            return
        
        try:
            # Common cookie consent selectors
            consent_selectors = [
                'button:has-text("Accept")',
                'button:has-text("Accept all")',
                'button:has-text("I agree")',
                'button:has-text("Allow")',
                'button:has-text("Got it")',
                '[id*="cookie"] button',
                '[class*="cookie"] button',
                '[aria-label*="Accept"]',
            ]
            
            for selector in consent_selectors:
                try:
                    button = self.page.locator(selector).first
                    if await button.is_visible(timeout=2000):
                        await button.click(timeout=2000)
                        logger.info(f"Clicked consent button: {selector}")
                        await asyncio.sleep(1)
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"No popups to handle or error: {e}")
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> None:
        """Navigate to URL and wait for page load."""
        if not self.page:
            raise RuntimeError("Page not initialized")
        
        try:
            await self.page.goto(url, wait_until=wait_until)
            await self.handle_popups()
            logger.info(f"Navigated to {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise
    
    async def close(self) -> None:
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
