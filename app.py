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
    page_icon="⚙️",
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
    st.title("⚙️ Web Reverse Engineering System")
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
        
        analyze_btn = st.button("🚀 Start Analysis", type="primary", use_container_width=True)
    
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
        st.error(f"❌ Analysis failed: {e}")
        st.exception(e)
    finally:
        loop.close()


def display_results(arch):
    """Display results."""
    st.success("✓ Analysis Complete")
    
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
    
    # Specs
    st.subheader("Functional Specifications")
    
    for spec in arch.template_specs:
        with st.expander(f"📄 {spec.template_pattern} ({spec.page_template_type})"):
            
            # Layout
            st.markdown("**Layout:**")
            st.write(f"Grid: {spec.layout_structure.grid_system}")
            st.write(f"Sections: {', '.join(spec.layout_structure.main_sections)}")
            
            # Interactions
            if spec.interactive_components:
                st.markdown("**Components:**")
                for comp in spec.interactive_components[:3]:
                    st.code(f"""
Name: {comp.name}
Location: {comp.location}
Triggers: {', '.join(comp.trigger_events[:2])}
                    """)
            
            # Design
            st.markdown("**Design System:**")
            st.write(f"Primary: {spec.design_system.primary_color}")
            st.write(f"Font: {spec.design_system.font_family}")
            
            # Screenshot
            if spec.screenshot_path:
                img_path = Path(spec.screenshot_path)
                if img_path.exists():
                    st.image(str(img_path), width=400)
    
    st.divider()
    
    # Export
    st.subheader("Export")
    json_data = arch.model_dump_json(indent=2)
    
    st.download_button(
        "📥 Download Blueprint (JSON)",
        json_data,
        file_name=f"architecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )


if __name__ == "__main__":
    main()