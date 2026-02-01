"""Core modules."""
from .browser_manager import BrowserManager
from .sitemap_crawler import SitemapCrawler
from .template_detector import TemplateDetector
from .functional_analyzer import FunctionalAnalyzer

__all__ = [
    'BrowserManager',
    'SitemapCrawler',
    'TemplateDetector',
    'FunctionalAnalyzer'
]