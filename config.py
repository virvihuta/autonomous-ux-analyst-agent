"""
Enterprise configuration management.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration."""
    
    # OpenAI API
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 8000
    
    # Browser settings
    browser_headless: bool = True
    browser_viewport_width: int = 1920
    browser_viewport_height: int = 1080
    browser_timeout: int = 45000  # Increased to 45 seconds
    use_stealth_mode: bool = True
    
    # Crawler settings
    max_urls_to_discover: int = 500
    max_crawl_depth: int = 2
    crawl_timeout_seconds: int = 300
    
    # Analysis settings
    max_templates_to_analyze: int = 20
    screenshot_quality: int = 85
    
    # Storage
    reports_dir: Path = Path("reports")
    screenshots_dir: Path = Path("screenshots")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        self.reports_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)


settings = Settings()