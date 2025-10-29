"""Tests for DataProvider and catalog utilities."""

import json
from datetime import datetime
from typing import List

import pytest

from opds2.catalog import create_catalog, create_search_catalog, add_pagination
from opds2.models import Contributor, Link, Metadata, Publication, Catalog
from opds2.provider import DataProvider


class MockDataProvider(DataProvider):
    """Mock data provider for testing."""
    
    def __init__(self):
        self.books = [
            {
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "language": "en",
                "url": "https://example.com/gatsby.epub"
            },
            {
                "title": "To Kill a Mockingbird",
                "author": "Harper Lee",
                "language": "en",
                "url": "https://example.com/mockingbird.epub"
            },
            {
                "title": "1984",
                "author": "George Orwell",
                "language": "en",
                "url": "https://example.com/1984.epub"
            },
        ]
    
    def search(self, query: str, limit: int = 50, offset: int = 0) -> List[Publication]:
        """Search mock books."""
        # Simple case-insensitive search
        query_lower = query.lower()
        results = [
            book for book in self.books
            if query_lower in book["title"].lower() or query_lower in book["author"].lower()
        ]
        
        # Apply pagination
        results = results[offset:offset + limit]
        
        # Convert to Publication objects
        publications = []
        for book in results:
            metadata = Metadata(
                title=book["title"],
                author=[Contributor(name=book["author"], role="author")],
                language=[book["language"]]
            )
            links = [
                Link(href=book["url"], type="application/epub+zip", rel="http://opds-spec.org/acquisition")
            ]
            publications.append(Publication(metadata=metadata, links=links))
        
        return publications


def test_data_provider_search():
    """Test DataProvider search functionality."""
    provider = MockDataProvider()
    results = provider.search("gatsby")
    
    assert len(results) == 1
    assert results[0].metadata.title == "The Great Gatsby"


def test_data_provider_search_multiple_results():
    """Test DataProvider search with multiple results."""
    provider = MockDataProvider()
    results = provider.search("the")
    
    assert len(results) == 1  # "The Great Gatsby" (only title matches "the")


def test_data_provider_search_no_results():
    """Test DataProvider search with no results."""
    provider = MockDataProvider()
    results = provider.search("xyz123")
    
    assert len(results) == 0


def test_data_provider_search_pagination():
    """Test DataProvider search with pagination."""
    provider = MockDataProvider()
    
    # Get all results
    all_results = provider.search("")
    assert len(all_results) == 3
    
    # Get first result with limit
    results = provider.search("", limit=1)
    assert len(results) == 1
    
    # Get second result with offset
    results = provider.search("", limit=1, offset=1)
    assert len(results) == 1
    assert results[0].metadata.title == "To Kill a Mockingbird"


def test_create_catalog_basic():
    """Test creating a basic catalog."""
    catalog = create_catalog(title="My Library")
    
    assert catalog.metadata.title == "My Library"
    assert catalog.publications == []


def test_create_catalog_with_publications():
    """Test creating a catalog with publications."""
    pub = Publication(
        metadata=Metadata(title="Test Book"),
        links=[Link(href="https://example.com/book.epub")]
    )
    
    catalog = create_catalog(
        title="My Catalog",
        publications=[pub],
        self_link="https://example.com/catalog"
    )
    
    assert len(catalog.publications) == 1
    assert catalog.publications[0].metadata.title == "Test Book"
    assert len(catalog.links) == 1
    assert catalog.links[0].rel == "self"


def test_create_catalog_with_search_link():
    """Test creating a catalog with search link."""
    catalog = create_catalog(
        title="Searchable Catalog",
        self_link="https://example.com/catalog",
        search_link="https://example.com/search?q={searchTerms}"
    )
    
    assert len(catalog.links) == 2
    search_link = [link for link in catalog.links if link.rel == "search"][0]
    assert search_link.templated is True


def test_create_search_catalog():
    """Test creating a search catalog."""
    provider = MockDataProvider()
    catalog = create_search_catalog(
        provider=provider,
        query="gatsby",
        self_link="https://example.com/search?q=gatsby"
    )
    
    assert "gatsby" in catalog.metadata.title.lower()
    assert len(catalog.publications) == 1
    assert catalog.publications[0].metadata.title == "The Great Gatsby"


def test_create_search_catalog_no_results():
    """Test creating a search catalog with no results."""
    provider = MockDataProvider()
    catalog = create_search_catalog(
        provider=provider,
        query="xyz123"
    )
    
    assert "no results" in catalog.metadata.title.lower()
    assert catalog.metadata.numberOfItems == 0


def test_create_search_catalog_json():
    """Test creating a search catalog and exporting to JSON."""
    provider = MockDataProvider()
    catalog = create_search_catalog(
        provider=provider,
        query="orwell"
    )
    
    json_str = catalog.model_dump_json()
    data = json.loads(json_str)
    
    assert "@context" in data
    assert data["metadata"]["numberOfItems"] == 1
    assert len(data["publications"]) == 1
    assert data["publications"][0]["metadata"]["title"] == "1984"


def test_catalog_integration():
    """Integration test: create a full catalog with search."""
    provider = MockDataProvider()
    
    # Create main catalog
    catalog = create_catalog(
        title="Library Catalog",
        publications=[],
        self_link="https://example.com/catalog",
        search_link="https://example.com/search?q={searchTerms}",
        identifier="urn:uuid:1234-5678",
        modified=datetime(2024, 1, 1)
    )
    
    # Verify catalog structure
    assert catalog.metadata.title == "Library Catalog"
    assert catalog.metadata.identifier == "urn:uuid:1234-5678"
    assert len(catalog.links) == 2
    
    # Convert to JSON
    json_str = catalog.model_dump_json()
    data = json.loads(json_str)
    
    assert "@context" in data
    assert data["metadata"]["title"] == "Library Catalog"
    
    # Perform search
    search_catalog = create_search_catalog(provider, "gatsby")
    search_json = search_catalog.model_dump_json()
    search_data = json.loads(search_json)
    
    assert len(search_data["publications"]) == 1
    assert search_data["publications"][0]["metadata"]["title"] == "The Great Gatsby"


def test_add_pagination_basic():
    """Test adding pagination to a catalog."""
    # Create a basic catalog
    catalog = create_catalog(
        title="Test Catalog",
        publications=[
            Publication(
                metadata=Metadata(title=f"Book {i}"),
                links=[Link(href=f"https://example.com/book{i}.epub")]
            )
            for i in range(10)
        ]
    )
    
    # Add pagination
    total = 100
    limit = 10
    offset = 0
    base_url = "https://example.com/search"
    params = {"query": "test"}
    
    paginated_catalog = add_pagination(
        catalog=catalog,
        total=total,
        limit=limit,
        offset=offset,
        base_url=base_url,
        params=params
    )
    
    # Check metadata
    assert paginated_catalog.metadata.numberOfItems == 100
    assert paginated_catalog.metadata.itemsPerPage == 10
    assert paginated_catalog.metadata.currentPage == 1
    
    # Check links - should have self, first, next, and last
    link_rels = [link.rel for link in paginated_catalog.links]
    assert "self" in link_rels
    assert "first" in link_rels
    assert "next" in link_rels
    assert "last" in link_rels
    assert "previous" not in link_rels  # Not on first page


def test_add_pagination_middle_page():
    """Test adding pagination for a middle page."""
    catalog = create_catalog(title="Test Catalog")
    
    total = 100
    limit = 10
    offset = 20  # Page 3
    base_url = "https://example.com/search"
    params = {"query": "test"}
    
    paginated_catalog = add_pagination(
        catalog=catalog,
        total=total,
        limit=limit,
        offset=offset,
        base_url=base_url,
        params=params
    )
    
    # Check metadata
    assert paginated_catalog.metadata.currentPage == 3
    
    # Check links - should have all link types
    link_rels = [link.rel for link in paginated_catalog.links]
    assert "self" in link_rels
    assert "first" in link_rels
    assert "previous" in link_rels
    assert "next" in link_rels
    assert "last" in link_rels


def test_add_pagination_last_page():
    """Test adding pagination for the last page."""
    catalog = create_catalog(title="Test Catalog")
    
    total = 100
    limit = 10
    offset = 90  # Page 10 (last page)
    base_url = "https://example.com/search"
    params = {"query": "test"}
    
    paginated_catalog = add_pagination(
        catalog=catalog,
        total=total,
        limit=limit,
        offset=offset,
        base_url=base_url,
        params=params
    )
    
    # Check metadata
    assert paginated_catalog.metadata.currentPage == 10
    
    # Check links - should not have next or last
    link_rels = [link.rel for link in paginated_catalog.links]
    assert "self" in link_rels
    assert "first" in link_rels
    assert "previous" in link_rels
    assert "next" not in link_rels
    assert "last" not in link_rels


def test_add_pagination_preserves_existing_links():
    """Test that add_pagination preserves existing links in the catalog."""
    catalog = create_catalog(
        title="Test Catalog",
        search_link="https://example.com/search?q={searchTerms}"
    )
    
    initial_link_count = len(catalog.links)
    
    paginated_catalog = add_pagination(
        catalog=catalog,
        total=50,
        limit=10,
        offset=0,
        base_url="https://example.com/results",
        params={"query": "test"}
    )
    
    # Should have original links plus pagination links
    assert len(paginated_catalog.links) > initial_link_count
    
    # Original search link should still be present
    search_links = [link for link in paginated_catalog.links if link.rel == "search"]
    assert len(search_links) == 1


def test_add_pagination_url_format():
    """Test that pagination URLs are correctly formatted."""
    catalog = create_catalog(title="Test Catalog")
    
    total = 100
    limit = 10
    offset = 10  # Page 2
    base_url = "https://example.com/search"
    params = {"query": "python", "limit": "10"}
    
    paginated_catalog = add_pagination(
        catalog=catalog,
        total=total,
        limit=limit,
        offset=offset,
        base_url=base_url,
        params=params
    )
    
    # Check self link contains correct parameters
    self_link = [link for link in paginated_catalog.links if link.rel == "self"][0]
    assert "query=python" in self_link.href
    assert "limit=10" in self_link.href
    assert "page=2" in self_link.href
    
    # Check next link has page=3
    next_link = [link for link in paginated_catalog.links if link.rel == "next"][0]
    assert "page=3" in next_link.href


def test_paginator_model():
    """Test Paginator model creation."""
    from opds2.models import Paginator
    
    # Test with defaults
    paginator = Paginator()
    assert paginator.limit == 50
    assert paginator.page == 1
    assert paginator.offset == 0
    assert paginator.numfound is None
    assert paginator.sort is None
    
    # Test with custom values
    paginator = Paginator(
        limit=10,
        page=3,
        offset=20,
        numfound=100,
        sort="title"
    )
    assert paginator.limit == 10
    assert paginator.page == 3
    assert paginator.offset == 20
    assert paginator.numfound == 100
    assert paginator.sort == "title"


def test_create_catalog_with_pagination():
    """Test DataProvider.create_catalog with pagination parameter."""
    from opds2.models import Paginator
    from opds2.provider import DataProvider, DataProviderRecord
    
    class TestRecord(DataProviderRecord):
        title: str
        
        def metadata(self):
            return Metadata(title=self.title)
        
        def links(self):
            return [Link(href="/test", rel="self")]
        
        def images(self):
            return None
    
    class TestProvider(DataProvider):
        TITLE = "Test Library"
        CATALOG_URL = "/catalog"
        SEARCH_URL = "/search{?query}"
        
        @staticmethod
        def search(query, limit=50, offset=0, sort=None):
            records = [TestRecord(title=f"Book {i}") for i in range(1, 11)]
            return records, 100
    
    # Test without pagination
    catalog = TestProvider.create_catalog(
        publications=[Publication(metadata=Metadata(title="Test"), links=[Link(href="/test")])]
    )
    assert catalog.metadata.title == "Test Library"
    assert catalog.metadata.currentPage is None
    assert catalog.metadata.itemsPerPage is None
    
    # Test with pagination
    catalog_with_pagination = TestProvider.create_catalog(
        publications=[Publication(metadata=Metadata(title="Test"), links=[Link(href="/test")])],
        pagination=Paginator(
            limit=10,
            offset=20,
            numfound=100,
            sort="title"
        )
    )
    
    assert catalog_with_pagination.metadata.title == "Test Library"
    assert catalog_with_pagination.metadata.currentPage == 3
    assert catalog_with_pagination.metadata.itemsPerPage == 10
    assert catalog_with_pagination.metadata.numberOfItems == 100
    
    # Test custom title
    catalog_custom = TestProvider.create_catalog(
        publications=[],
        title="Custom Title"
    )
    assert catalog_custom.metadata.title == "Custom Title"
