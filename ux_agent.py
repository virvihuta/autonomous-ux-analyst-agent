"""
Main autonomous UX analysis agent orchestrating all components.
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from statistics import mean

from browser_manager import BrowserManager
from page_analyzer import PageAnalyzer
from navigator import Navigator
from session_handler import SessionHandler
from models import FinalReport, PageAnalysis
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UXAnalysisAgent:
    """
    Autonomous agent for comprehensive UX analysis of websites.
    """
    
    def __init__(
        self,
        headless: bool = False,
        max_pages: int = 5,
        max_depth: int = 3
    ):
        self.browser_manager = BrowserManager(
            headless=headless,
            viewport_width=settings.browser_viewport_width,
            viewport_height=settings.browser_viewport_height,
            timeout=settings.browser_timeout,
            use_stealth=settings.use_stealth_mode
        )
        
        self.page_analyzer = PageAnalyzer(
            llm_model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        
        self.navigator = Navigator()
        self.session_handler = SessionHandler()
        
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.page_analyses = []
    
    async def analyze_website(
        self,
        target_url: str,
        credentials: Optional[Dict[str, str]] = None,
        cookie_file: Optional[Path] = None
    ) -> FinalReport:
        """
        Main entry point: Analyze a website and return comprehensive UX report.
        
        Args:
            target_url: The website URL to analyze
            credentials: Optional login credentials
            cookie_file: Optional path to saved cookies
            
        Returns:
            FinalReport with complete analysis
        """
        try:
            logger.info(f"Starting UX analysis of {target_url}")
            
            # Initialize browser
            await self.browser_manager.initialize()
            
            # Load cookies if provided
            if cookie_file:
                await self.browser_manager.load_cookies(cookie_file)
            
            # Set credentials if provided
            if credentials:
                self.session_handler.set_credentials(credentials)
            
            # Navigate to target URL
            await self.browser_manager.navigate(target_url)
            
            # Check for login page
            page = self.browser_manager.page
            if await self.session_handler.detect_login_page(page):
                logger.info("Login page detected")
                login_success = await self.session_handler.attempt_login(page)
                if login_success:
                    logger.info("Login successful")
                else:
                    logger.warning("Login failed or not configured")
            
            # Start autonomous exploration
            await self._explore_website()
            
            # Save cookies for future sessions
            if cookie_file:
                await self.browser_manager.save_cookies(cookie_file)
            
            # Generate final report
            report = self._generate_report(target_url)
            
            logger.info(f"Analysis complete. Analyzed {len(self.page_analyses)} pages")
            
            return report
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
        finally:
            await self.browser_manager.close()
    
    async def _explore_website(self) -> None:
        """Autonomously explore the website and collect UX analyses."""
        page = self.browser_manager.page
        depth = 0
        
        while len(self.page_analyses) < self.max_pages and depth < self.max_depth:
            try:
                # Analyze current page
                logger.info(f"Analyzing page {len(self.page_analyses) + 1}/{self.max_pages}")
                analysis = await self.page_analyzer.analyze_page(page)
                self.page_analyses.append(analysis)
                
                # Track navigation
                current_url = page.url
                self.navigator.add_to_history(current_url, analysis.page_type)
                
                # Decide next action
                visited_types = self.navigator.get_visited_page_types()
                action = await self.page_analyzer.decide_next_action(
                    page, analysis, visited_types
                )
                
                # Check if exploration should stop
                if action.action == "complete":
                    logger.info("LLM decided exploration is complete")
                    break
                
                # Execute action
                success = await self.navigator.execute_action(page, action)
                
                if not success:
                    logger.warning("Action failed, trying alternative navigation")
                    # Try scrolling or waiting as fallback
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await asyncio.sleep(2)
                
                depth += 1
                
                # Small delay between actions
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error during exploration: {e}")
                break
    
    def _generate_report(self, target_url: str) -> FinalReport:
        """Generate comprehensive final report from collected analyses."""
        if not self.page_analyses:
            raise ValueError("No page analyses collected")
        
        # Calculate overall design score
        design_scores = [analysis.design_score for analysis in self.page_analyses]
        overall_score = mean(design_scores)
        
        # Aggregate key strengths
        strengths = set()
        for analysis in self.page_analyses:
            for element in analysis.key_elements:
                if element.quality_score >= 8:
                    strengths.add(f"{element.element_type}: {element.description}")
        
        # Aggregate critical issues
        critical_issues = []
        for analysis in self.page_analyses:
            for friction in analysis.ux_friction_points:
                if friction.severity == "high":
                    critical_issues.append(friction.issue)
        
        # Generate recommendations
        recommendations = []
        friction_points_by_severity = {"high": [], "medium": [], "low": []}
        
        for analysis in self.page_analyses:
            for friction in analysis.ux_friction_points:
                friction_points_by_severity[friction.severity].append(friction.recommendation)
        
        # Prioritize high severity recommendations
        recommendations.extend(friction_points_by_severity["high"][:3])
        recommendations.extend(friction_points_by_severity["medium"][:2])
        
        return FinalReport(
            url=target_url,
            timestamp=datetime.now().isoformat(),
            pages_analyzed=len(self.page_analyses),
            page_analyses=self.page_analyses,
            overall_design_score=round(overall_score, 2),
            key_strengths=list(strengths)[:5],
            critical_issues=critical_issues[:5],
            recommendations=recommendations[:5]
        )
