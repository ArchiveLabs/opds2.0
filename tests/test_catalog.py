"""Tests for DataProvider and catalog utilities."""

import json
from datetime import datetime

import pytest

from opds2.catalog import create_catalog, create_search_catalog
from opds2.models import Contributor, Link, Metadata, Publication
from opds2.provider import DataProvider
from opds2.types import ItemMapping, SearchResult


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
    
    def search(self, query: str, page: int = 1, rows: int = 50) -> SearchResult:
        """Search mock books."""
        # Simple case-insensitive search
        query_lower = query.lower()
        results = [
            book for book in self.books
            if not query or query_lower in book["title"].lower() or query_lower in book["author"].lower()
        ]
        
        # Apply pagination
        offset = (page - 1) * rows
        paginated = results[offset:offset + rows]
        
        return SearchResult(
            items=paginated,
            page=page,
            num_found=len(results),
            rows=rows
        )
    
    def get_item_mapping(self) -> ItemMapping:
        """Get item mapping for mock books."""
        return ItemMapping(
            title=lambda item: item.get("title"),
            author=lambda item: [item.get("author")] if item.get("author") else [],
            language=lambda item: [item.get("language")] if item.get("language") else None,
            acquisition_link=lambda item: item.get("url"),
            acquisition_type=lambda item: "application/epub+zip",
        )


def test_data_provider_search():
    """Test DataProvider search functionality."""
    provider = MockDataProvider()
    result = provider.search("gatsby")
    
    assert result.num_found == 1
    assert len(result.items) == 1
    assert result.items[0]["title"] == "The Great Gatsby"


def test_data_provider_search_multiple_results():
    """Test DataProvider search with multiple results."""
    provider = MockDataProvider()
    result = provider.search("the")
    
    assert result.num_found == 1  # "The Great Gatsby" (only title matches "the")
    assert len(result.items) == 1


def test_data_provider_search_no_results():
    """Test DataProvider search with no results."""
    provider = MockDataProvider()
    result = provider.search("xyz123")
    
    assert result.num_found == 0
    assert len(result.items) == 0


def test_data_provider_search_pagination():
    """Test DataProvider search with pagination."""
    provider = MockDataProvider()
    
    # Get all results
    all_results = provider.search("")
    assert all_results.num_found == 3
    assert len(all_results.items) == 3
    
    # Get first result with limit
    results = provider.search("", rows=1)
    assert len(results.items) == 1
    assert results.num_found == 3  # Total found is still 3
    
    # Get second result with page
    results = provider.search("", page=2, rows=1)
    assert len(results.items) == 1
    assert results.items[0]["title"] == "To Kill a Mockingbird"


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


def test_item_mapping():
    """Test ItemMapping functionality."""
    provider = MockDataProvider()
    mapping = provider.get_item_mapping()
    
    # Test mapping a single item
    test_item = {
        "title": "Test Book",
        "author": "Test Author",
        "language": "en",
        "url": "https://example.com/test.epub"
    }
    
    mapped = mapping.map_item(test_item)
    
    # Legacy field names are mapped to schema.org equivalents
    assert mapped["name"] == "Test Book"  # title -> name
    assert mapped["author"] == ["Test Author"]
    assert mapped["inLanguage"] == ["en"]  # language -> inLanguage
    assert mapped["url"] == "https://example.com/test.epub"  # acquisition_link -> url
    assert mapped["encodingFormat"] == "application/epub+zip"  # acquisition_type -> encodingFormat
