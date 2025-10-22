"""Type definitions for OPDS 2.0 data structures.

This module contains base dataclasses for search results and item mappings.
Schema field names are based on schema.org vocabulary (Book, Person, etc.)
to promote interoperability and standardization.
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


# Schema.org-based field definitions for Book publications
# Based on https://schema.org/Book and related types
SCHEMA_ORG_FIELDS = {
    # Core Book properties (from schema.org/Book)
    "name": "The name/title of the book (schema.org/name)",
    "identifier": "Unique identifier such as ISBN, URI (schema.org/identifier)",
    "description": "Description or summary of the book (schema.org/description)",
    "inLanguage": "Language code(s) of the content (schema.org/inLanguage)",
    
    # Creator/Contributor properties (schema.org/Book)
    "author": "Author(s) of the book - Person or Organization (schema.org/author)",
    "publisher": "Publisher(s) - Person or Organization (schema.org/publisher)",
    
    # Temporal properties (schema.org/Book)
    "datePublished": "Date of first publication (schema.org/datePublished)",
    "dateModified": "Date of most recent modification (schema.org/dateModified)",
    
    # Media properties (schema.org/CreativeWork)
    "image": "URL to cover image (schema.org/image)",
    "thumbnailUrl": "URL to thumbnail image (schema.org/thumbnailUrl)",
    
    # Content/Subject properties (schema.org/CreativeWork)
    "about": "Subject matter of the book (schema.org/about)",
    "keywords": "Keywords or tags (schema.org/keywords)",
    "genre": "Genre of the creative work (schema.org/genre)",
    
    # Access/Encoding properties (schema.org/Book, CreativeWork)
    "url": "URL of the item/resource (schema.org/url)",
    "encoding": "A media object that encodes this book (schema.org/encoding)",
    "encodingFormat": "MIME type of the encoding (schema.org/encodingFormat)",
}

# Legacy field names mapped to schema.org equivalents for backwards compatibility
OPDS_RESERVED_FIELDS = {
    "title": "name",  # schema.org/name
    "identifier": "identifier",  # schema.org/identifier
    "description": "description",  # schema.org/description
    "language": "inLanguage",  # schema.org/inLanguage
    "author": "author",  # schema.org/author
    "publisher": "publisher",  # schema.org/publisher
    "published": "datePublished",  # schema.org/datePublished
    "modified": "dateModified",  # schema.org/dateModified
    "cover_url": "image",  # schema.org/image
    "thumbnail_url": "thumbnailUrl",  # schema.org/thumbnailUrl
    "acquisition_link": "url",  # schema.org/url
    "acquisition_type": "encodingFormat",  # schema.org/encodingFormat
    "subject": "about",  # schema.org/about (can also use keywords/genre)
}


@dataclass
class ItemMapping:
    """Defines how to map raw item data to schema.org-based fields.
    
    This class allows DataProviders to specify how their raw data
    should be transformed into standardized schema.org publication data.
    Fields follow schema.org vocabulary (Book, Person, CreativeWork types).
    
    Legacy field names (title, cover_url, etc.) are supported for backwards
    compatibility and are automatically mapped to schema.org equivalents.
    
    Example using schema.org field names:
        mapping = ItemMapping(
            name=lambda item: item.get("title"),
            author=lambda item: [item.get("author_name", "Unknown")],
            image=lambda item: f"https://covers.openlibrary.org/b/id/{item.get('cover_i')}-L.jpg" 
                if item.get('cover_i') else None
        )
    
    Example using legacy field names (backwards compatible):
        mapping = ItemMapping(
            title=lambda item: item.get("title"),  # Mapped to 'name'
            cover_url=lambda item: item.get("cover"),  # Mapped to 'image'
        )
    """
    # Schema.org field names (preferred)
    name: Optional[callable] = None  # Title (schema.org/name)
    identifier: Optional[callable] = None  # Unique identifier (schema.org/identifier)
    description: Optional[callable] = None  # Description (schema.org/description)
    inLanguage: Optional[callable] = None  # Language code(s) (schema.org/inLanguage)
    author: Optional[callable] = None  # Author(s) (schema.org/author)
    publisher: Optional[callable] = None  # Publisher(s) (schema.org/publisher)
    datePublished: Optional[callable] = None  # Publication date (schema.org/datePublished)
    dateModified: Optional[callable] = None  # Modification date (schema.org/dateModified)
    image: Optional[callable] = None  # Cover image URL (schema.org/image)
    thumbnailUrl: Optional[callable] = None  # Thumbnail URL (schema.org/thumbnailUrl)
    about: Optional[callable] = None  # Subject matter (schema.org/about)
    keywords: Optional[callable] = None  # Keywords/tags (schema.org/keywords)
    genre: Optional[callable] = None  # Genre (schema.org/genre)
    url: Optional[callable] = None  # Resource URL (schema.org/url)
    encoding: Optional[callable] = None  # Media encoding (schema.org/encoding)
    encodingFormat: Optional[callable] = None  # MIME type (schema.org/encodingFormat)
    
    # Legacy field names (for backwards compatibility)
    # These are automatically mapped to schema.org equivalents
    title: Optional[callable] = None  # Maps to 'name'
    language: Optional[callable] = None  # Maps to 'inLanguage'
    published: Optional[callable] = None  # Maps to 'datePublished'
    modified: Optional[callable] = None  # Maps to 'dateModified'
    cover_url: Optional[callable] = None  # Maps to 'image'
    thumbnail_url: Optional[callable] = None  # Maps to 'thumbnailUrl'
    acquisition_link: Optional[callable] = None  # Maps to 'url'
    acquisition_type: Optional[callable] = None  # Maps to 'encodingFormat'
    subject: Optional[callable] = None  # Maps to 'about'
    
    def map_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Map a raw item to schema.org-compatible fields.
        
        Args:
            item: Raw item dictionary from data source
            
        Returns:
            Dictionary with schema.org-compatible field names and values
        """
        result = {}
        
        # Process all schema.org fields
        for schema_field in SCHEMA_ORG_FIELDS.keys():
            mapper = getattr(self, schema_field, None)
            if mapper is not None and callable(mapper):
                value = mapper(item)
                if value is not None:
                    result[schema_field] = value
        
        # Handle legacy field mappings (backwards compatibility)
        for legacy_field, schema_field in OPDS_RESERVED_FIELDS.items():
            # Skip if it's already a schema.org field
            if legacy_field == schema_field:
                continue
            
            # Check if legacy field has a mapper
            legacy_mapper = getattr(self, legacy_field, None)
            if legacy_mapper is not None and callable(legacy_mapper):
                # Only use legacy mapper if schema.org field doesn't have one
                if schema_field not in result:
                    value = legacy_mapper(item)
                    if value is not None:
                        result[schema_field] = value
        
        return result
