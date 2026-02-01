"""
Intelligent URL discovery engine.
"""
import asyncio
import re
from typing import List, Set
from urllib.parse import urljoin, urlparse
from playwright.async_api import Page
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


class SitemapCrawler:
    """Discovers URLs via sitemap and intelligent crawling."""
    
    def __init__(self, max_urls: int = 500):
        self.max_urls = max_urls
        self.discovered_urls: Set[str] = set()
        
    async def discover_urls(self, page: Page, base_url: str) -> List[str]:
        """Main discovery orchestration."""
        logger.info(f"Starting URL discovery for {base_url}")
        
        # Try sitemap first
        sitemap_urls = await self._fetch_sitemap(page, base_url)
        self.discovered_urls.update(sitemap_urls)
        
        # Fallback to crawling if needed
        if len(self.discovered_urls) < 20:
            logger.info("Sitemap insufficient, initiating crawl")
            crawled = await self._crawl_links(page, base_url)
            self.discovered_urls.update(crawled)
        
        result = list(self.discovered_urls)[:self.max_urls]
        logger.info(f"Discovered {len(result)} URLs")
        return result
    
    async def _fetch_sitemap(self, page: Page, base_url: str) -> Set[str]:
        """Parse sitemap.xml."""
        urls = set()
        sitemap_paths = ['/sitemap.xml', '/sitemap_index.xml', '/sitemap-index.xml']
        
        for path in sitemap_paths:
            sitemap_url = urljoin(base_url, path)
            try:
                response = await page.goto(sitemap_url, wait_until='load', timeout=10000)
                if response and response.status == 200:
                    content = await page.content()
                    parsed = self._parse_sitemap_xml(content, base_url)
                    urls.update(parsed)
                    logger.info(f"Found {len(parsed)} URLs in {path}")
                    if len(urls) > 100:
                        break
            except:
                continue
        
        return urls
    
    def _parse_sitemap_xml(self, xml_content: str, base_url: str) -> Set[str]:
        """Extract URLs from sitemap XML."""
        urls = set()
        try:
            xml_content = re.sub(r' xmlns="[^"]+"', '', xml_content)
            root = ET.fromstring(xml_content)
            base_domain = urlparse(base_url).netloc
            
            for loc in root.findall('.//loc'):
                if loc.text:
                    url = loc.text.strip()
                    if urlparse(url).netloc == base_domain:
                        urls.add(url)
        except Exception as e:
            logger.debug(f"XML parse error: {e}")
        
        return urls
    
    async def _crawl_links(self, page: Page, base_url: str, max_depth: int = 2) -> Set[str]:
        """Crawl internal links."""
        visited = set()
        to_visit = {base_url}
        urls = set()
        base_domain = urlparse(base_url).netloc
        depth = 0
        
        while to_visit and depth < max_depth and len(urls) < self.max_urls:
            current = to_visit.pop()
            if current in visited:
                continue
            
            visited.add(current)
            
            try:
                await page.goto(current, wait_until='networkidle', timeout=15000)
                await asyncio.sleep(0.5)
                
                links = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('a[href]'))
                            .map(a => a.href)
                            .filter(h => h.startsWith('http'))
                """)
                
                for link in links:
                    if urlparse(link).netloc == base_domain:
                        clean = f"{urlparse(link).scheme}://{urlparse(link).netloc}{urlparse(link).path}"
                        urls.add(clean)
                        if len(visited) < 15:
                            to_visit.add(clean)
            except:
                continue
            
            depth += 1
        
        return urls