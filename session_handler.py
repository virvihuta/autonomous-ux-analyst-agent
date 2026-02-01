"""
Handles authentication flows including login and signup.
"""
import asyncio
from typing import Dict, Optional
from playwright.async_api import Page
import logging

logger = logging.getLogger(__name__)


class SessionHandler:
    """
    Universal session handler for login and authentication flows.
    """
    
    def __init__(self):
        self.credentials: Optional[Dict[str, str]] = None
        self.login_attempted = False
    
    def set_credentials(self, credentials: Dict[str, str]) -> None:
        """
        Set credentials for login.
        
        Expected format:
        {
            'username': 'user@example.com',
            'password': 'secret123',
            'username_field': 'email'  # optional, defaults to 'username'
        }
        """
        self.credentials = credentials
        logger.info("Credentials configured")
    
    async def detect_login_page(self, page: Page) -> bool:
        """Detect if current page is a login page."""
        try:
            # Common login indicators
            login_indicators = [
                'input[type="password"]',
                'input[name*="password"]',
                'input[name*="login"]',
                'input[name*="email"]',
                'button:has-text("Log in")',
                'button:has-text("Sign in")',
                'form[action*="login"]',
                'form[action*="signin"]',
            ]
            
            for selector in login_indicators:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=2000):
                        logger.info(f"Login page detected via selector: {selector}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting login page: {e}")
            return False
    
    async def attempt_login(self, page: Page) -> bool:
        """
        Attempt to login using provided credentials.
        Returns True if login was successful.
        """
        if not self.credentials or self.login_attempted:
            return False
        
        try:
            self.login_attempted = True
            logger.info("Attempting login...")
            
            # Find username/email field
            username = self.credentials.get('username', '')
            password = self.credentials.get('password', '')
            username_field_name = self.credentials.get('username_field', 'username')
            
            if not username or not password:
                logger.warning("Missing username or password")
                return False
            
            # Try to find and fill username field
            username_selectors = [
                f'input[name="{username_field_name}"]',
                'input[name="email"]',
                'input[name="username"]',
                'input[type="email"]',
                'input[type="text"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]',
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    field = page.locator(selector).first
                    if await field.is_visible(timeout=2000):
                        await field.fill(username)
                        username_filled = True
                        logger.info(f"Filled username field: {selector}")
                        break
                except:
                    continue
            
            if not username_filled:
                logger.warning("Could not find username field")
                return False
            
            # Find and fill password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    field = page.locator(selector).first
                    if await field.is_visible(timeout=2000):
                        await field.fill(password)
                        password_filled = True
                        logger.info(f"Filled password field: {selector}")
                        break
                except:
                    continue
            
            if not password_filled:
                logger.warning("Could not find password field")
                return False
            
            # Find and click submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Sign in")',
                'button:has-text("Login")',
                'button:has-text("Submit")',
            ]
            
            for selector in submit_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=2000):
                        await button.click()
                        logger.info(f"Clicked login button: {selector}")
                        
                        # Wait for navigation or error
                        await asyncio.sleep(3)
                        
                        # Check if login was successful
                        is_still_login_page = await self.detect_login_page(page)
                        
                        if not is_still_login_page:
                            logger.info("Login appears successful")
                            return True
                        else:
                            logger.warning("Still on login page after submit")
                            return False
                except:
                    continue
            
            logger.warning("Could not find submit button")
            return False
            
        except Exception as e:
            logger.error(f"Login attempt failed: {e}")
            return False
    
    def reset(self) -> None:
        """Reset login state for new session."""
        self.login_attempted = False
