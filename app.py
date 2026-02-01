"""
Enterprise Streamlit interface.
Professional, minimal, functional.
"""
import streamlit as st
import asyncio
import json
from datetime import datetime
from pathlib import Path

from agent import ReverseEngineeringAgent
from config import settings

# Config
st.set_page_config(
    page_title="Reverse Engineering System",
    page_icon="🔧",
    layout="wide"
)

# Styles
st.markdown("""
<style>
    .main {background-color: #0e1117;}
    .stButton>button {
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        padding: 0.5rem 2rem;
    }
    h1, h2, h3 {color: #e0e0e0; font-weight: 600;}
    .metric-box {
        background: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 3px solid #2563eb;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.title("Web Reverse Engineering System")
    st.caption("Enterprise functional decomposition and architecture analysis")
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        target_url = st.text_input(
            "Target URL",
            placeholder="https://example.com"
        )
        
        headless = st.checkbox("Headless Browser", value=True)
        
        st.divider()
        st.info("**Scope:** System auto-discovers all templates via sitemap analysis")
        
        analyze_btn = st.button("Start Analysis", type="primary", use_container_width=True)
    
    # Main
    if analyze_btn and target_url:
        run_analysis(target_url, headless)
    else:
        show_info()


def show_info():
    """Welcome screen."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("System Capabilities")
        st.markdown("""
        - Autonomous sitemap crawling
        - Template pattern detection
        - Functional decomposition
        - Tech stack identification
        - Blueprint export (JSON)
        """)
    
    with col2:
        st.subheader("Output Format")
        st.markdown("""
        - URL template patterns
        - Interaction behaviors
        - Data collection specs
        - Design system tokens
        - API endpoints
        """)


def run_analysis(url: str, headless: bool):
    """Execute analysis."""
    progress = st.progress(0)
    status = st.empty()
    
    def update(p: float, msg: str):
        progress.progress(p)
        status.text(msg)
    
    agent = ReverseEngineeringAgent(headless=headless)
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        arch = loop.run_until_complete(
            agent.analyze_site(url, progress_callback=update)
        )
        
        display_results(arch)
        
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        st.exception(e)
    finally:
        loop.close()


def display_results(arch):
    """Display results."""
    st.success("Analysis Complete")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("URLs Found", arch.total_urls_discovered)
    col2.metric("Templates", arch.unique_templates_identified)
    col3.metric("Analyzed", len(arch.template_specs))
    col4.metric("Duration", f"{arch.analysis_duration_seconds}s")
    
    st.divider()
    
    # Template tree
    st.subheader("Template Structure")
    tree = {t.pattern: {"type": t.template_type, "matches": t.total_matches} for t in arch.templates}
    st.json(tree)
    
    st.divider()
    
    # Specs - Handle both dict and object formats
    st.subheader("Functional Specifications")
    
    # Count successful vs failed
    success_count = sum(1 for s in arch.template_specs if isinstance(s, dict) and s.get('status') != 'failed')
    failed_count = len(arch.template_specs) - success_count
    
    if failed_count > 0:
        st.warning(f"Warning: {failed_count} template(s) failed to analyze. Check logs for details.")
    
    for spec in arch.template_specs:
        # Handle both dict and Pydantic model
        if isinstance(spec, dict):
            template_pattern = spec.get('template_pattern', 'unknown')
            template_name = spec.get('template_name', 'Unknown')
            status = spec.get('status', 'success')
            
            # Show status indicator
            status_indicator = "[SUCCESS]" if status == "success" else "[FAILED]"
            
            with st.expander(f"{status_indicator} {template_pattern} ({template_name})"):
                
                if status == "failed":
                    st.error(f"Analysis failed: {spec.get('error_message', 'Unknown error')}")
                    st.write(f"URL: {spec.get('analyzed_url', 'N/A')}")
                    continue
                
                # Layout
                layout_engine = spec.get('layout_engine', 'unknown')
                st.markdown("**Layout:**")
                st.write(f"Engine: {layout_engine}")
                
                # Design System
                design = spec.get('design_system', {})
                if design:
                    st.markdown("**Design System:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Primary Color: {design.get('primary_color', 'N/A')}")
                        st.write(f"Background: {design.get('background_color', 'N/A')}")
                    with col2:
                        st.write(f"Text Color: {design.get('text_color', 'N/A')}")
                        st.write(f"Font: {design.get('font_family', 'N/A')}")
                
                # Components
                components = spec.get('components', [])
                if components:
                    st.markdown(f"**Components ({len(components)}):**")
                    for idx, comp in enumerate(components[:5]):  # Show first 5
                        with st.container():
                            st.markdown(f"**{idx+1}. {comp.get('name', 'Unnamed')}**")
                            st.write(f"Location: {comp.get('location', 'N/A')}")
                            st.write(f"Function: {comp.get('functionality', 'N/A')}")
                            
                            if comp.get('trigger_events'):
                                st.write(f"Events: {', '.join(comp['trigger_events'][:3])}")
                    
                    if len(components) > 5:
                        st.info(f"+ {len(components) - 5} more components (see JSON export)")
                
                # Screenshot
                screenshot_path = spec.get('screenshot_path')
                if screenshot_path:
                    img_path = Path(screenshot_path)
                    if img_path.exists():
                        st.markdown("**Screenshot:**")
                        st.image(str(img_path), width=600)
        
        else:
            # Fallback for Pydantic models (shouldn't happen but just in case)
            with st.expander(f"Template: {spec.template_pattern} ({spec.template_name})"):
                st.json(spec.model_dump())
    
    st.divider()
    
    # Tech Stack
    if arch.tech_stack:
        st.subheader("Technology Stack")
        st.json(arch.tech_stack)
    
    st.divider()
    
    # Export
    st.subheader("Export")
    json_data = arch.model_dump_json(indent=2)
    
    st.download_button(
        "Download Blueprint (JSON)",
        json_data,
        file_name=f"architecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
    
    # Summary stats
    st.divider()
    st.subheader("Analysis Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Success Rate", f"{(success_count/len(arch.template_specs)*100):.0f}%")
    with col2:
        st.metric("Successful", success_count)
    with col3:
        st.metric("Failed", failed_count)


if __name__ == "__main__":
    main()