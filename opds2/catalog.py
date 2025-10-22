"""Utilities for creating OPDS 2.0 catalogs and search feeds."""

from typing import List, Optional
from datetime import datetime, timezone

from opds2.models import Catalog, Link, Metadata, Publication, Contributor
from opds2.provider import DataProvider


def create_catalog(
    title: str,
    publications: Optional[List[Publication]] = None,
    self_link: Optional[str] = None,
    search_link: Optional[str] = None,
    identifier: Optional[str] = None,
    modified: Optional[datetime] = None,
) -> Catalog:
    """Create an OPDS 2.0 catalog.
    
    Args:
        title: Title of the catalog
        publications: Optional list of publications to include
        self_link: Optional self link URL
        search_link: Optional search endpoint URL
        identifier: Optional unique identifier for the catalog
        modified: Optional last modified timestamp
        
    Returns:
        Catalog object
    """
    metadata = Metadata(title=title)
    
    if identifier:
        metadata.identifier = identifier
    if modified:
        metadata.modified = modified
    
    links = []
    if self_link:
        links.append(Link(href=self_link, rel="self", type="application/opds+json"))
    if search_link:
        links.append(Link(
            href=search_link,
            rel="search",
            type="application/opds+json",
            templated=True
        ))
    
    return Catalog(
        metadata=metadata,
        links=links,
        publications=publications or []
    )


def _map_item_to_publication(item_data: dict, provider: DataProvider) -> Publication:
    """Map a raw item to a Publication using the provider's mapping.
    
    Args:
        item_data: Raw item data from the provider
        provider: DataProvider instance with mapping configuration
        
    Returns:
        Publication object
    """
    # Get the mapping from the provider
    mapping = provider.get_item_mapping()
    
    # Apply the mapping to get OPDS-compatible fields
    mapped = mapping.map_item(item_data)
    
    # Build metadata
    metadata_kwargs = {}
    
    # Handle title (required)
    metadata_kwargs['title'] = mapped.get('title', 'Untitled')
    
    # Handle optional text fields
    for field in ['identifier', 'description', 'published', 'modified']:
        if field in mapped:
            metadata_kwargs[field] = mapped[field]
    
    # Handle list fields
    for field in ['language', 'subject']:
        if field in mapped:
            value = mapped[field]
            if value is not None:
                # Ensure it's a list
                metadata_kwargs[field] = value if isinstance(value, list) else [value]
    
    # Handle contributors (author, publisher, etc.)
    for role in ['author', 'publisher']:
        if role in mapped:
            contributors_data = mapped[role]
            if contributors_data:
                # Ensure it's a list
                if not isinstance(contributors_data, list):
                    contributors_data = [contributors_data]
                
                # Convert to Contributor objects
                contributors = []
                for contrib in contributors_data:
                    if isinstance(contrib, str):
                        contributors.append(Contributor(name=contrib, role=role))
                    elif isinstance(contrib, dict):
                        contributors.append(Contributor(**contrib, role=role))
                
                metadata_kwargs[role] = contributors
    
    metadata = Metadata(**metadata_kwargs)
    
    # Build links
    links = []
    
    # Add acquisition link if provided
    if 'acquisition_link' in mapped and mapped['acquisition_link']:
        link_type = mapped.get('acquisition_type', 'application/octet-stream')
        links.append(Link(
            href=mapped['acquisition_link'],
            type=link_type,
            rel="http://opds-spec.org/acquisition"
        ))
    
    # Build images list for cover/thumbnail
    images = []
    if 'cover_url' in mapped and mapped['cover_url']:
        images.append(Link(
            href=mapped['cover_url'],
            type="image/jpeg",
            rel="http://opds-spec.org/image"
        ))
    
    if 'thumbnail_url' in mapped and mapped['thumbnail_url']:
        images.append(Link(
            href=mapped['thumbnail_url'],
            type="image/jpeg",
            rel="http://opds-spec.org/image/thumbnail"
        ))
    
    return Publication(
        metadata=metadata,
        links=links,
        images=images if images else None
    )


def create_search_catalog(
    provider: DataProvider,
    query: str,
    page: int = 1,
    rows: int = 50,
    self_link: Optional[str] = None,
) -> Catalog:
    """Create a catalog from search results.
    
    Args:
        provider: DataProvider instance to perform the search
        query: Search query string
        page: Page number (1-indexed, default: 1)
        rows: Number of items per page (default: 50)
        self_link: Optional self link URL
        
    Returns:
        Catalog with search results
    """
    # Get search results from provider
    search_result = provider.search(query=query, page=page, rows=rows)
    
    # Map items to publications using list comprehension
    publications = [
        _map_item_to_publication(item, provider)
        for item in search_result.items
    ]
    
    # Create title based on results
    title = f'Search results for "{query}"'
    if search_result.num_found == 0:
        title = f'No results found for "{query}"'
    
    metadata = Metadata(
        title=title,
        numberOfItems=search_result.num_found,
        modified=datetime.now(timezone.utc)
    )
    
    links = []
    if self_link:
        links.append(Link(href=self_link, rel="self", type="application/opds+json"))
    
    return Catalog(
        metadata=metadata,
        links=links,
        publications=publications
    )
