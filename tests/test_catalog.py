"""Tests for DataProvider and catalog utilities."""

import json
from datetime import datetime
from typing import List

from opds2 import Catalog
from opds2.models import Contributor, Link, Metadata, Publication
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
    catalog = Catalog.create(metadata=Metadata(title="My Library"))
    
    assert catalog.metadata.title == "My Library"
    assert catalog.publications == []


def test_create_catalog_with_publications():
    """Test creating a catalog with publications."""
    pub = Publication(
        metadata=Metadata(title="Test Book"),
        links=[Link(href="https://example.com/book.epub")]
    )
    
    catalog = Catalog.create(
        metadata=Metadata(title="My Catalog"),
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
