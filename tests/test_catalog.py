"""Tests for DataProvider and catalog utilities."""

import json
from datetime import datetime
from typing import List, Optional

from opds2 import Catalog
from opds2.models import Contributor, Link, Metadata, Publication
from opds2.provider import DataProvider


class MockDataProvider(DataProvider):
    """Mock data provider for testing."""
    
    TITLE = "Mock Library"
    BASE_URL = "https://example.com"
    SEARCH_URL = "/search{?query}"
    
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
    
    def search(self, query: str, limit: int = 50, offset: int = 0, sort=None) -> DataProvider.SearchResponse:
        """Search mock books."""
        # Simple case-insensitive search
        query_lower = query.lower()
        all_results = [
            book for book in self.books
            if query_lower in book["title"].lower() or query_lower in book["author"].lower()
        ]
        
        total = len(all_results)
        
        # Apply pagination
        results = all_results[offset:offset + limit]
        
        # Convert to DataProviderRecord objects
        from opds2.provider import DataProviderRecord
        
        class MockRecord(DataProviderRecord):
            model_config = {'extra': 'allow'}  # Allow extra fields
            
            def __init__(self, book_data):
                super().__init__(book_data=book_data)
            
            def metadata(self) -> Metadata:
                return Metadata(
                    title=self.book_data["title"],
                    author=[Contributor(name=self.book_data["author"], role="author")],
                    language=[self.book_data["language"]]
                )
            
            def links(self) -> List[Link]:
                return [
                    Link(href=self.book_data["url"], type="application/epub+zip", rel="http://opds-spec.org/acquisition")
                ]
            
            def images(self):
                return None
        
        records = [MockRecord(book) for book in results]
        
        return DataProvider.SearchResponse(
            provider=self,
            records=records,
            total=total,
            request=DataProvider.SearchRequest(
                query=query,
                limit=limit,
                offset=offset,
                sort=sort
            )
        )


# Helper functions for backward compatibility
def create_catalog(
    title: str = "Catalog",
    publications: Optional[List[Publication]] = None,
    self_link: Optional[str] = None,
    search_link: Optional[str] = None,
    identifier: Optional[str] = None,
    modified: Optional[datetime] = None,
) -> Catalog:
    """Helper function to create a catalog with a simple API."""
    metadata = Metadata(
        title=title,
        identifier=identifier,
        modified=modified,
    )
    return Catalog.create(
        metadata=metadata,
        publications=publications,
        self_link=self_link,
        search_link=search_link,
        paginate=False,
    )


def create_search_catalog(
    provider: DataProvider,
    query: str,
    limit: int = 50,
    offset: int = 0,
    self_link: Optional[str] = None,
) -> Catalog:
    """Helper function to create a search catalog."""
    search_response = provider.search(query, limit=limit, offset=offset)
    
    # Generate a title based on query and results
    if search_response.total == 0:
        title = f"No results found for '{query}'" if query else "No results found"
    else:
        title = f"Search results for '{query}'" if query else f"All results ({search_response.total} items)"
    
    metadata = Metadata(title=title)
    
    return Catalog.create(
        data=search_response,
        paginate=True,
        metadata=metadata,
        self_link=self_link,
    )


def test_data_provider_search():
    """Test DataProvider search functionality."""
    provider = MockDataProvider()
    results = provider.search("gatsby")
    
    assert len(results.records) == 1
    assert results.records[0].metadata().title == "The Great Gatsby"
    assert results.total == 1


def test_data_provider_search_multiple_results():
    """Test DataProvider search with multiple results."""
    provider = MockDataProvider()
    results = provider.search("the")
    
    assert len(results.records) == 1  # "The Great Gatsby" (only title matches "the")
    assert results.total == 1


def test_data_provider_search_no_results():
    """Test DataProvider search with no results."""
    provider = MockDataProvider()
    results = provider.search("xyz123")
    
    assert len(results.records) == 0
    assert results.total == 0


def test_data_provider_search_pagination():
    """Test DataProvider search with pagination."""
    provider = MockDataProvider()
    
    # Get all results
    all_results = provider.search("")
    assert len(all_results.records) == 3
    assert all_results.total == 3
    
    # Get first result with limit
    results = provider.search("", limit=1)
    assert len(results.records) == 1
    assert results.total == 3
    
    # Get second result with offset
    results = provider.search("", limit=1, offset=1)
    assert len(results.records) == 1
    assert results.records[0].metadata().title == "To Kill a Mockingbird"
    assert results.total == 3


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
