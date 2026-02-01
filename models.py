"""
Pydantic models for structured data validation and output.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl


class UXElement(BaseModel):
    """Represents a key UX element identified on the page."""
    element_type: str = Field(..., description="Type of element (button, form, navigation, etc.)")
    description: str = Field(..., description="What this element does")
    location: str = Field(..., description="Where it appears on the page")
    quality_score: int = Field(..., ge=1, le=10, description="Quality rating 1-10")


class FrictionPoint(BaseModel):
    """Represents a UX friction point or usability issue."""
    issue: str = Field(..., description="Description of the friction point")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity level")
    recommendation: str = Field(..., description="How to fix it")


class PageAnalysis(BaseModel):
    """Analysis result for a single page."""
    page_type: str = Field(..., description="Type of page (landing, login, dashboard, etc.)")
    key_elements: List[UXElement] = Field(default_factory=list)
    ux_friction_points: List[FrictionPoint] = Field(default_factory=list)
    design_score: int = Field(..., ge=1, le=10, description="Overall design quality score")
    accessibility_notes: Optional[str] = None
    mobile_readiness: Optional[str] = None


class NavigationAction(BaseModel):
    """Recommended navigation action from the LLM."""
    action: Literal["click", "fill", "wait", "scroll", "complete"] = Field(...)
    target_description: Optional[str] = None
    selector_hint: Optional[str] = None
    reasoning: str = Field(..., description="Why this action should be taken")


class FinalReport(BaseModel):
    """Complete analysis report for the entire website exploration."""
    url: HttpUrl
    timestamp: str
    pages_analyzed: int
    page_analyses: List[PageAnalysis]
    overall_design_score: float = Field(..., ge=1.0, le=10.0)
    key_strengths: List[str]
    critical_issues: List[str]
    recommendations: List[str]
