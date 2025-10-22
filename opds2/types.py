"""Type definitions for OPDS 2.0 data structures.

This module contains base dataclasses for search results and item mappings.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    """Standardized search result returned by DataProviders.
    
    This provides a consistent interface for search results, separating
    the raw data retrieval from OPDS feed generation.
    
    Attributes:
        items: List of raw item dictionaries from the data source
        page: Current page number (1-indexed)
        num_found: Total number of items found matching the search
        rows: Number of items per page
    """
    items: List[Dict[str, Any]] = field(default_factory=list)
    page: int = 1
    num_found: int = 0
    rows: int = 50


# Reserved OPDS item field names that can be mapped from provider data
OPDS_RESERVED_FIELDS = {
    "title": "Title of the publication",
    "identifier": "Unique identifier (URI or URL)",
    "description": "Description or summary",
    "language": "Language code(s) as a list",
    "author": "Author name(s) as a list",
    "publisher": "Publisher name(s) as a list",
    "published": "Publication date",
    "modified": "Last modification date",
    "cover_url": "URL to cover image",
    "thumbnail_url": "URL to thumbnail image",
    "acquisition_link": "URL to acquire/download the resource",
    "acquisition_type": "MIME type of the acquisition resource",
    "subject": "Subject tags as a list",
}


@dataclass
class ItemMapping:
    """Defines how to map raw item data to OPDS-compatible fields.
    
    This class allows DataProviders to specify how their raw data
    should be transformed into standardized OPDS publication data.
    
    Example:
        mapping = ItemMapping(
            title=lambda item: item.get("title"),
            author=lambda item: [item.get("author_name", "Unknown")],
            cover_url=lambda item: f"https://covers.openlibrary.org/b/id/{item.get('cover_i')}-L.jpg" 
                if item.get('cover_i') else None
        )
    """
    title: Optional[callable] = None
    identifier: Optional[callable] = None
    description: Optional[callable] = None
    language: Optional[callable] = None
    author: Optional[callable] = None
    publisher: Optional[callable] = None
    published: Optional[callable] = None
    modified: Optional[callable] = None
    cover_url: Optional[callable] = None
    thumbnail_url: Optional[callable] = None
    acquisition_link: Optional[callable] = None
    acquisition_type: Optional[callable] = None
    subject: Optional[callable] = None
    
    def map_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Map a raw item to OPDS-compatible fields.
        
        Args:
            item: Raw item dictionary from data source
            
        Returns:
            Dictionary with OPDS-compatible field names and values
        """
        result = {}
        
        for field_name in OPDS_RESERVED_FIELDS.keys():
            mapper = getattr(self, field_name, None)
            if mapper is not None and callable(mapper):
                value = mapper(item)
                if value is not None:
                    result[field_name] = value
        
        return result
