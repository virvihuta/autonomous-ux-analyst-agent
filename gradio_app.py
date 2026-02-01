"""
Gradio web interface for the UX Analysis Agent.
"""
import asyncio
import gradio as gr
from pathlib import Path
import json
from datetime import datetime
import logging
from typing import Optional, Tuple

from ux_agent import UXAnalysisAgent
from config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GradioUXAnalyzer:
    """Wrapper class for Gradio interface."""
    
    def __init__(self):
        self.current_agent: Optional[UXAnalysisAgent] = None
        
    async def analyze_website_async(
        self,
        website_url: str,
        website_name: str,
        max_pages: int,
        use_headless: bool,
        enable_login: bool,
        username: str,
        password: str,
        progress=gr.Progress()
    ) -> Tuple[str, str, str]:
        """
        Analyze a website and return results.
        
        Returns:
            Tuple of (summary_text, json_report, status_message)
        """
        try:
            # Validate inputs
            if not website_url:
                return "❌ Error: Please enter a website URL", "", "Error: No URL provided"
            
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            
            # Update progress
            progress(0.1, desc="Initializing browser...")
            
            # Initialize agent
            self.current_agent = UXAnalysisAgent(
                headless=use_headless,
                max_pages=max_pages,
                max_depth=3
            )
            
            # Prepare credentials if login is enabled
            credentials = None
            if enable_login and username and password:
                credentials = {
                    'username': username,
                    'password': password,
                    'username_field': 'email'
                }
            
            progress(0.2, desc=f"Navigating to {website_url}...")
            
            # Run analysis
            report = await self.current_agent.analyze_website(
                target_url=website_url,
                credentials=credentials
            )
            
            progress(0.9, desc="Generating report...")
            
            # Generate summary text
            summary = self._generate_summary(report, website_name or website_url)
            
            # Generate JSON report
            json_report = report.model_dump_json(indent=2)
            
            # Save report to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in website_name if c.isalnum() or c in (' ', '-', '_'))[:50]
            filename = f"ux_report_{safe_name}_{timestamp}.json"
            
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            report_path = reports_dir / filename
            with open(report_path, 'w') as f:
                f.write(json_report)
            
            progress(1.0, desc="Complete!")
            
            status = f"✅ Analysis complete! Report saved to: {report_path}"
            
            return summary, json_report, status
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            import traceback
            error_details = traceback.format_exc()
            return (
                f"❌ Error during analysis: {str(e)}",
                f"{{'error': '{str(e)}', 'traceback': '{error_details}'}}",
                f"❌ Failed: {str(e)}"
            )
    
    def _generate_summary(self, report, website_name: str) -> str:
        """Generate human-readable summary from report."""
        summary_parts = []
        
        # Header
        summary_parts.append(f"# UX Analysis Report: {website_name}")
        summary_parts.append(f"\n📊 **Overall Design Score:** {report.overall_design_score}/10")
        summary_parts.append(f"📄 **Pages Analyzed:** {report.pages_analyzed}")
        summary_parts.append(f"🕐 **Analysis Date:** {report.timestamp}\n")
        
        # Key Strengths
        if report.key_strengths:
            summary_parts.append("\n## ✨ Key Strengths\n")
            for strength in report.key_strengths:
                summary_parts.append(f"- {strength}")
        
        # Critical Issues
        if report.critical_issues:
            summary_parts.append("\n## ⚠️ Critical Issues\n")
            for issue in report.critical_issues:
                summary_parts.append(f"- {issue}")
        
        # Recommendations
        if report.recommendations:
            summary_parts.append("\n## 💡 Recommendations\n")
            for i, rec in enumerate(report.recommendations, 1):
                summary_parts.append(f"{i}. {rec}")
        
        # Page-by-Page Analysis
        summary_parts.append("\n## 📑 Page-by-Page Analysis\n")
        for i, page_analysis in enumerate(report.page_analyses, 1):
            summary_parts.append(f"\n### Page {i}: {page_analysis.page_type.title()}")
            summary_parts.append(f"**Design Score:** {page_analysis.design_score}/10\n")
            
            # Key elements
            if page_analysis.key_elements:
                summary_parts.append("**Key Elements:**")
                for elem in page_analysis.key_elements[:3]:  # Top 3
                    summary_parts.append(f"- {elem.element_type}: {elem.description} (Quality: {elem.quality_score}/10)")
            
            # Friction points
            if page_analysis.ux_friction_points:
                summary_parts.append("\n**UX Issues:**")
                for friction in page_analysis.ux_friction_points[:3]:  # Top 3
                    emoji = "🔴" if friction.severity == "high" else "🟡" if friction.severity == "medium" else "🟢"
                    summary_parts.append(f"- {emoji} {friction.issue}")
        
        return "\n".join(summary_parts)
    
    def analyze_website(
        self,
        website_url: str,
        website_name: str,
        max_pages: int,
        use_headless: bool,
        enable_login: bool,
        username: str,
        password: str,
        progress=gr.Progress()
    ) -> Tuple[str, str, str]:
        """Synchronous wrapper for async analysis."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.analyze_website_async(
                    website_url,
                    website_name,
                    max_pages,
                    use_headless,
                    enable_login,
                    username,
                    password,
                    progress
                )
            )
            return result
        finally:
            loop.close()


def create_gradio_interface():
    """Create and configure the Gradio interface."""
    
    analyzer = GradioUXAnalyzer()
    
    with gr.Blocks(title="UX Analysis Agent", theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
            # 🎨 Autonomous UX Analysis Agent
            
            Analyze any website's UX patterns, design choices, and functionality flows using AI.
            
            **How it works:**
            1. Enter the website URL and name
            2. Configure analysis settings
            3. Optionally provide login credentials
            4. Click "Analyze Website"
            5. Get comprehensive UX insights!
            """
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🌐 Website Information")
                
                website_url = gr.Textbox(
                    label="Website URL",
                    placeholder="https://example.com",
                    info="The website you want to analyze"
                )
                
                website_name = gr.Textbox(
                    label="Website Name",
                    placeholder="Example Company",
                    info="A friendly name for the report"
                )
                
                gr.Markdown("### ⚙️ Analysis Settings")
                
                max_pages = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="Maximum Pages to Analyze",
                    info="More pages = more comprehensive analysis (but slower)"
                )
                
                use_headless = gr.Checkbox(
                    label="Headless Mode",
                    value=True,
                    info="Run browser in background (faster, but you won't see it)"
                )
                
                gr.Markdown("### 🔐 Login Credentials (Optional)")
                
                enable_login = gr.Checkbox(
                    label="Enable Auto-Login",
                    value=False,
                    info="Attempt to login if a login page is detected"
                )
                
                username = gr.Textbox(
                    label="Username/Email",
                    placeholder="user@example.com",
                    type="text",
                    visible=False
                )
                
                password = gr.Textbox(
                    label="Password",
                    placeholder="password",
                    type="password",
                    visible=False
                )
                
                # Toggle credential fields visibility
                def toggle_credentials(enabled):
                    return {
                        username: gr.update(visible=enabled),
                        password: gr.update(visible=enabled)
                    }
                
                enable_login.change(
                    toggle_credentials,
                    inputs=[enable_login],
                    outputs=[username, password]
                )
                
                analyze_btn = gr.Button(
                    "🚀 Analyze Website",
                    variant="primary",
                    size="lg"
                )
        
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Analysis Results")
                
                status_text = gr.Textbox(
                    label="Status",
                    value="Ready to analyze...",
                    interactive=False
                )
                
                with gr.Tab("Summary"):
                    summary_output = gr.Markdown(
                        value="Analysis results will appear here..."
                    )
                
                with gr.Tab("JSON Report"):
                    json_output = gr.Code(
                        label="Full JSON Report",
                        language="json",
                        value="{}"
                    )
                
                gr.Markdown(
                    """
                    ### 💾 Reports
                    
                    All reports are automatically saved to the `reports/` directory with timestamps.
                    """
                )
        
        # Connect the analyze button
        analyze_btn.click(
            fn=analyzer.analyze_website,
            inputs=[
                website_url,
                website_name,
                max_pages,
                use_headless,
                enable_login,
                username,
                password
            ],
            outputs=[summary_output, json_output, status_text]
        )
        
        gr.Markdown(
            """
            ---
            **Tips:**
            - Start with 2-3 pages for quick tests
            - Use headless mode for production
            - Login credentials are optional but unlock deeper analysis
            - Check the `reports/` folder for saved JSON files
            """
        )
    
    return interface


def main():
    """Launch the Gradio interface."""
    try:
        # Validate settings first
        settings.validate_settings()
        
        # Create and launch interface
        interface = create_gradio_interface()
        
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,  # Set to True to create a public link
            show_error=True
        )
        
    except Exception as e:
        logger.error(f"Failed to launch Gradio interface: {e}")
        print(f"\n❌ Error: {e}")
        print("\nPlease ensure:")
        print("1. You have created a .env file with OPENAI_API_KEY")
        print("2. All dependencies are installed (pip install -r requirements.txt)")
        print("3. Playwright browsers are installed (playwright install)")


if __name__ == "__main__":
    main()