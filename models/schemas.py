"""
Enterprise data schemas for reverse engineering.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from enum import Enum


class PageTemplateType(str, Enum):
    """Standard page template classifications."""
    HOMEPAGE = "homepage"
    PRODUCT_DETAIL = "product_detail"
    PRODUCT_LISTING = "product_listing"
    ARTICLE_CONTENT = "article_content"
    USER_DASHBOARD = "user_dashboard"
    AUTH_PORTAL = "auth_portal"
    CHECKOUT_FLOW = "checkout_flow"
    PROFILE_PAGE = "profile_page"
    SEARCH_RESULTS = "search_results"
    STATIC_PAGE = "static_page"
    CUSTOM_APPLICATION = "custom_application"


class URLTemplate(BaseModel):
    """Represents a detected URL pattern."""
    pattern: str
    example_urls: List[str]
    template_type: str
    parameter_count: int
    total_matches: int


class LayoutStructure(BaseModel):
    """Page layout structure."""
    grid_system: str
    responsive_behavior: str
    main_sections: List[str]


class InteractiveComponent(BaseModel):
    """Interactive element specification."""
    name: str
    location: str
    trigger_events: List[str]
    data_inputs: List[str]
    visual_state: str


class DesignSystem(BaseModel):
    """Design tokens and styling."""
    primary_color: str
    secondary_color: Optional[str] = None
    background_color: str
    text_color: str
    font_family: str
    heading_font: Optional[str] = None
    button_styles: str
    spacing_system: Optional[str] = None


class NavigationItem(BaseModel):
    """Navigation link."""
    text: str
    target: str
    nav_type: str = Field(alias="type")
    
    class Config:
        populate_by_name = True


class TechnicalDetails(BaseModel):
    """Technical implementation details."""
    javascript_framework: Optional[str] = None
    form_submission_method: Optional[str] = None
    ajax_behavior: bool = False
    lazy_loading: bool = False
    api_endpoints: List[str] = Field(default_factory=list)


class FunctionalSpec(BaseModel):
    """Complete functional specification for a template."""
    page_template_type: str
    layout_structure: LayoutStructure
    interactive_components: List[InteractiveComponent]
    design_system: DesignSystem
    navigation: List[NavigationItem]
    technical_details: TechnicalDetails
    third_party_integrations: List[str] = Field(default_factory=list)
    
    # Metadata
    template_pattern: str
    analyzed_url: str
    screenshot_path: Optional[str] = None
    analysis_timestamp: datetime = Field(default_factory=datetime.now)


# NEW MODELS FOR REPLICATION FOCUS

class ComponentSpec(BaseModel):
    """Individual component specification for replication."""
    name: str
    location: str
    functionality: str
    data_inputs: List[str] = Field(default_factory=list)
    trigger_events: List[str] = Field(default_factory=list)


class PageBlueprint(BaseModel):
    """Replication blueprint for a page template."""
    template_name: str
    template_pattern: str
    layout_engine: str
    design_system: DesignSystem
    components: List[ComponentSpec]
    
    # Metadata
    analyzed_url: str
    status: str = "success"
    error_message: Optional[str] = None
    analysis_timestamp: datetime = Field(default_factory=datetime.now)


class SiteArchitecture(BaseModel):
    """Complete site architecture blueprint."""
    target_url: HttpUrl
    crawl_timestamp: datetime
    
    # Discovery
    total_urls_discovered: int
    unique_templates_identified: int
    templates: List[URLTemplate]
    
    # Specifications
    template_specs: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Global
    global_navigation: List[NavigationItem] = Field(default_factory=list)
    tech_stack: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance
    analysis_duration_seconds: float
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }