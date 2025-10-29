"""Utilities for creating OPDS 2.0 catalogs and search feeds."""

from typing import List, Optional
from datetime import datetime, timezone
from urllib.parse import urlencode

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


def add_pagination(
    catalog: Catalog,
    total: int,
    limit: int,
    offset: int,
    base_url: str,
    params: dict[str, str]
) -> Catalog:
    """Add pagination links and metadata to an existing Catalog.
    
    Args:
        catalog: The catalog to add pagination to
        total: Total number of items available
        limit: Maximum number of items per page
        offset: Current offset for pagination
        base_url: Base URL for pagination links
        params: Query parameters to include in pagination links
        
    Returns:
        The catalog with pagination links and metadata added
    """
    page = (offset // limit) + 1 if limit else 1
    last_page = (total + limit - 1) // limit if limit else 1
    has_more = (offset + limit) < total

    links = list(catalog.links or [])
    
    def make_link(rel: str, page_num: int):
        href = f"{base_url}?{urlencode(params | {'page': str(page_num)})}"
        return Link(rel=rel, href=href, type="application/opds+json")

    # Always include self & first
    links.append(make_link("self", page))
    links.append(make_link("first", 1))

    if page > 1:
        links.append(make_link("previous", page - 1))
    if has_more:
        links.append(make_link("next", page + 1))
        links.append(make_link("last", last_page))

    catalog.links = links

    # Update metadata
    if not catalog.metadata:
        catalog.metadata = Metadata(title="")
    catalog.metadata.currentPage = page
    catalog.metadata.itemsPerPage = limit
    catalog.metadata.numberOfItems = total

    return catalog


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
