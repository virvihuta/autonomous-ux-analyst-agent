"""
Configuration management for the UX Analysis Agent.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    openai_api_key: str = ""
    llm_model: str = "gpt-4-vision-preview"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4000
    
    # Browser Configuration
    browser_headless: bool = False
    browser_viewport_width: int = 1920
    browser_viewport_height: int = 1080
    browser_timeout: int = 30000
    
    # Analysis Configuration
    max_pages_to_explore: int = 5
    screenshot_quality: int = 80
    max_navigation_depth: int = 3
    
    # Stealth Configuration
    use_stealth_mode: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    def validate_settings(self) -> bool:
        """Validate that required settings are present."""
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. Please set it in .env file or environment variable."
            )
        return True


# Initialize settings
try:
    settings = Settings()
except Exception as e:
    # Provide helpful error message
    print(f"Error loading settings: {e}")
    print("\nPlease create a .env file with the following variables:")
    print("OPENAI_API_KEY=your-api-key-here")
    raise