"""
Main reverse engineering orchestrator.
Enterprise-grade architecture analysis system.
"""
import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
import logging

from core import BrowserManager, SitemapCrawler, TemplateDetector, FunctionalAnalyzer
from models import SiteArchitecture
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReverseEngineeringAgent:
    """
    Production reverse engineering system.
    Analyzes websites to extract functional blueprints.
    """
    
    def __init__(self, headless: bool = True):
        self.browser = BrowserManager(headless=headless)
        self.crawler = SitemapCrawler(max_urls=settings.max_urls_to_discover)
        self.detector = TemplateDetector()
        self.analyzer = FunctionalAnalyzer()
        
    async def analyze_site(self, target_url: str, progress_callback=None) -> SiteArchitecture:
        """
        Complete site analysis.
        
        Returns: SiteArchitecture with functional blueprint
        """
        start_time = time.time()
        
        try:
            logger.info(f"=== Starting analysis: {target_url} ===")
            
            # Phase 1: Initialize
            if progress_callback:
                progress_callback(0.05, "Initializing browser...")
            
            await self.browser.initialize()
            page = self.browser.page
            
            # Phase 2: Discover URLs
            if progress_callback:
                progress_callback(0.15, "Discovering site structure...")
            
            urls = await self.crawler.discover_urls(page, target_url)
            logger.info(f"Discovered {len(urls)} URLs")
            
            # Phase 3: Detect templates
            if progress_callback:
                progress_callback(0.25, "Identifying page templates...")
            
            templates = self.detector.detect_templates(urls)
            logger.info(f"Identified {len(templates)} templates")
            
            # Phase 4: Analyze templates
            if progress_callback:
                progress_callback(0.35, "Analyzing functional specifications...")
            
            # Limit analysis
            templates_to_analyze = templates[:settings.max_templates_to_analyze]
            template_specs = []
            
            for idx, template in enumerate(templates_to_analyze):
                rep_url = self.detector.get_representative_url(template)
                if not rep_url:
                    continue
                
                progress = 0.35 + (0.55 * (idx / len(templates_to_analyze)))
                if progress_callback:
                    progress_callback(
                        progress,
                        f"Analyzing {idx+1}/{len(templates_to_analyze)}: {template.template_type}"
                    )
                
                try:
                    await self.browser.navigate(rep_url)
                    await asyncio.sleep(2)
                    
                    spec = await self.analyzer.analyze(
                        page,
                        template.pattern,
                        settings.screenshots_dir
                    )
                    template_specs.append(spec)
                    
                except Exception as e:
                    logger.error(f"Failed to analyze {rep_url}: {e}")
                    continue
            
            # Phase 5: Global analysis
            if progress_callback:
                progress_callback(0.90, "Extracting global elements...")
            
            await self.browser.navigate(target_url)
            global_nav = await self._extract_global_nav(page)
            tech_stack = await self._detect_tech_stack(page)
            
            # Build architecture
            duration = time.time() - start_time
            
            architecture = SiteArchitecture(
                target_url=target_url,
                crawl_timestamp=datetime.now(),
                total_urls_discovered=len(urls),
                unique_templates_identified=len(templates),
                templates=templates,
                template_specs=template_specs,
                global_navigation=global_nav,
                tech_stack=tech_stack,
                analysis_duration_seconds=round(duration, 2)
            )
            
            # Save report
            self._save_report(architecture)
            
            logger.info(f"=== Analysis complete: {duration:.1f}s ===")
            
            if progress_callback:
                progress_callback(1.0, "Complete!")
            
            return architecture
            
        finally:
            await self.browser.close()
    
    async def _extract_global_nav(self, page) -> list:
        """Extract global navigation."""
        try:
            nav = await page.evaluate("""
                () => Array.from(document.querySelectorAll('nav a, header a'))
                    .map(a => ({text: a.textContent.trim(), target: a.href, type: 'main_nav'}))
                    .filter(i => i.text.length > 0)
                    .slice(0, 15)
            """)
            return nav
        except:
            return []
    
    async def _detect_tech_stack(self, page) -> dict:
        """Detect technology stack."""
        try:
            return await page.evaluate("""
                () => {
                    const stack = {};
                    if (window.React) stack.frontend = 'React';
                    else if (window.Vue) stack.frontend = 'Vue';
                    else if (window.Angular) stack.frontend = 'Angular';
                    if (window.ga || window.gtag) stack.analytics = 'Google Analytics';
                    const gen = document.querySelector('meta[name="generator"]');
                    if (gen) stack.cms = gen.content;
                    return stack;
                }
            """)
        except:
            return {}
    
    def _save_report(self, architecture: SiteArchitecture) -> Path:
        """Save JSON report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"architecture_{timestamp}.json"
        filepath = settings.reports_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(architecture.model_dump_json(indent=2))
        
        logger.info(f"Report saved: {filepath}")
        return filepath