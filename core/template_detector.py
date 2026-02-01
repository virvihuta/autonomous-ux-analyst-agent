"""
Pattern-based template detection engine.
"""
import re
from typing import List, Dict
from collections import defaultdict
from urllib.parse import urlparse
import logging

from models import URLTemplate

logger = logging.getLogger(__name__)


class TemplateDetector:
    """Groups URLs by structural patterns."""
    
    def detect_templates(self, urls: List[str]) -> List[URLTemplate]:
        """Identify unique page templates."""
        logger.info(f"Analyzing {len(urls)} URLs")
        
        pattern_groups = self._group_by_pattern(urls)
        templates = []
        
        for pattern, url_list in pattern_groups.items():
            template_type = self._infer_type(pattern)
            
            templates.append(URLTemplate(
                pattern=pattern,
                example_urls=url_list[:10],
                template_type=template_type,
                parameter_count=pattern.count('{'),
                total_matches=len(url_list)
            ))
        
        # Sort: simpler first, then by popularity
        templates.sort(key=lambda t: (t.parameter_count, -t.total_matches))
        
        logger.info(f"Identified {len(templates)} templates")
        return templates
    
    def _group_by_pattern(self, urls: List[str]) -> Dict[str, List[str]]:
        """Group similar URLs."""
        groups = defaultdict(list)
        
        for url in urls:
            pattern = self._extract_pattern(url)
            groups[pattern].append(url)
        
        # Filter singles except root pages
        return {p: u for p, u in groups.items() if len(u) > 1 or p.count('/') <= 2}
    
    def _extract_pattern(self, url: str) -> str:
        """Convert URL to pattern."""
        path = urlparse(url).path.rstrip('/')
        if not path:
            return '/'
        
        segments = []
        for seg in path.split('/'):
            if not seg:
                continue
            if seg.isdigit():
                segments.append('{id}')
            elif self._is_uuid(seg):
                segments.append('{uuid}')
            elif re.match(r'^\d{4}$', seg):
                segments.append('{year}')
            elif '-' in seg or '_' in seg:
                segments.append('{slug}')
            else:
                segments.append(seg)
        
        return '/' + '/'.join(segments)
    
    def _is_uuid(self, s: str) -> bool:
        """Check UUID pattern."""
        return bool(re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', s, re.I))
    
    def _infer_type(self, pattern: str) -> str:
        """Classify pattern."""
        if pattern == '/':
            return 'homepage'
        
        p_lower = pattern.lower()
        type_map = {
            'product': ['product', 'item'],
            'category': ['category', 'collection'],
            'article': ['article', 'post', 'blog'],
            'profile': ['user', 'profile'],
            'search': ['search'],
            'checkout': ['checkout', 'cart'],
            'auth': ['login', 'signup', 'register']
        }
        
        for page_type, keywords in type_map.items():
            if any(kw in p_lower for kw in keywords):
                return page_type
        
        return 'detail_page' if '{id}' in pattern else 'static_page'
    
    def get_representative_url(self, template: URLTemplate) -> str:
        """Best URL to analyze for this template."""
        return template.example_urls[0] if template.example_urls else None