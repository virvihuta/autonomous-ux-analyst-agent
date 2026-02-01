"""
Test script to verify all components work correctly.
"""
import asyncio
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_imports():
    """Test that all imports work correctly."""
    logger.info("Testing imports...")
    try:
        from config import settings
        from models import PageAnalysis, FinalReport, NavigationAction
        from browser_manager import BrowserManager
        from page_analyzer import PageAnalyzer
        from navigator import Navigator
        from session_handler import SessionHandler
        from ux_agent import UXAnalysisAgent
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False


async def test_config():
    """Test configuration loading."""
    logger.info("Testing configuration...")
    try:
        from config import settings
        settings.validate_settings()
        logger.info("✓ Configuration valid")
        logger.info(f"  - LLM Model: {settings.llm_model}")
        logger.info(f"  - Browser Headless: {settings.browser_headless}")
        logger.info(f"  - Max Pages: {settings.max_pages_to_explore}")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration error: {e}")
        return False


async def test_browser_manager():
    """Test browser manager initialization."""
    logger.info("Testing browser manager...")
    try:
        from browser_manager import BrowserManager
        browser = BrowserManager(headless=True)
        await browser.initialize()
        await browser.navigate("https://example.com")
        logger.info("✓ Browser manager works")
        await browser.close()
        return True
    except Exception as e:
        logger.error(f"✗ Browser manager error: {e}")
        return False


async def test_models():
    """Test Pydantic models."""
    logger.info("Testing Pydantic models...")
    try:
        from models import PageAnalysis, UXElement, FrictionPoint
        
        # Test UXElement
        element = UXElement(
            element_type="button",
            description="Primary CTA",
            location="Header",
            quality_score=8
        )
        
        # Test FrictionPoint
        friction = FrictionPoint(
            issue="Hard to find",
            severity="medium",
            recommendation="Make more prominent"
        )
        
        # Test PageAnalysis
        analysis = PageAnalysis(
            page_type="landing",
            key_elements=[element],
            ux_friction_points=[friction],
            design_score=7
        )
        
        # Test JSON serialization
        json_output = analysis.model_dump_json()
        logger.info("✓ Models work correctly")
        return True
    except Exception as e:
        logger.error(f"✗ Model error: {e}")
        return False


async def test_full_analysis():
    """Test complete analysis workflow."""
    logger.info("Testing full analysis workflow...")
    try:
        from ux_agent import UXAnalysisAgent
        
        agent = UXAnalysisAgent(
            headless=True,
            max_pages=2,  # Just test with 2 pages
            max_depth=1
        )
        
        # Test with example.com (simple, reliable site)
        report = await agent.analyze_website(
            target_url="https://example.com"
        )
        
        logger.info("✓ Full analysis successful")
        logger.info(f"  - Pages analyzed: {report.pages_analyzed}")
        logger.info(f"  - Overall score: {report.overall_design_score}/10")
        logger.info(f"  - Critical issues: {len(report.critical_issues)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Full analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    logger.info("="*60)
    logger.info("STARTING COMPREHENSIVE TESTS")
    logger.info("="*60)
    
    results = {}
    
    # Run tests
    results['imports'] = await test_imports()
    results['config'] = await test_config()
    results['models'] = await test_models()
    results['browser'] = await test_browser_manager()
    results['full_analysis'] = await test_full_analysis()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    logger.info("="*60)
    if all_passed:
        logger.info("ALL TESTS PASSED! 🎉")
        logger.info("System is ready for production use.")
    else:
        logger.error("SOME TESTS FAILED")
        logger.error("Please fix errors before proceeding.")
    logger.info("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)