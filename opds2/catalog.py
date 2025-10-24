"""Utilities for creating OPDS 2.0 catalogs and search feeds."""

from typing import List, Optional
from datetime import datetime, timezone

from opds2.models import Catalog, Link, Metadata, Publication


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


def create_search_catalog(
    provider,
    query: str,
    limit: int = 50,
    offset: int = 0,
    self_link: Optional[str] = None,
) -> Catalog:
    """Create a catalog from search results.
    
    Args:
        provider: DataProvider instance to perform the search
        query: Search query string
        limit: Maximum number of results (default: 50)
        offset: Offset for pagination (default: 0)
        self_link: Optional self link URL
        
    Returns:
        Catalog with search results
    """
    publications = provider.search(query=query, limit=limit, offset=offset)
    
    title = f'Search results for "{query}"'
    if len(publications) == 0:
        title = f'No results found for "{query}"'
    
    metadata = Metadata(
        title=title,
        numberOfItems=len(publications),
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
