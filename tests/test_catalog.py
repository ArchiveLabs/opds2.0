"""Tests for DataProvider and catalog utilities."""

import json
from datetime import datetime
from typing import List, Optional

from pyopds2 import Catalog
from pyopds2.models import Contributor, Link, Metadata, Publication
from pyopds2.provider import DataProvider, DataProviderRecord


class MockBook(DataProviderRecord):
    """Mock book record for testing."""
    title: str
    author: str
    language: str
    url: str

    def metadata(self) -> Metadata:
        """Return book metadata."""
        return Metadata(
            title=self.title,
            author=[Contributor(name=self.author, role="author")],
            language=[self.language]
        )

    def links(self) -> List[Link]:
        """Return book links."""
        return [
            Link(
                href=self.url,
                type="application/epub+zip",
                rel="http://opds-spec.org/acquisition"
            )
        ]

    def images(self) -> Optional[List[Link]]:
        """Return book images."""
        return None


class MockDataProvider(DataProvider):
    """Mock data provider for testing."""

    TITLE = "Mock Library"
    BASE_URL = "https://example.com"
    SEARCH_URL = "/search{?query}"

    BOOKS = [
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

    @staticmethod
    def search(
        query: str,
        limit: int = 50,
        offset: int = 0,
        sort: Optional[str] = None
    ) -> DataProvider.SearchResponse:
        """Search mock books."""
        # Simple case-insensitive search
        query_lower = query.lower()
        all_results = [
            book for book in MockDataProvider.BOOKS
            if (query_lower in book["title"].lower() or
                query_lower in book["author"].lower())
        ]

        total = len(all_results)

        # Apply pagination
        paginated_results = all_results[offset:offset + limit]

        # Convert to MockBook records
        records = [MockBook(**book) for book in paginated_results]

        return DataProvider.SearchResponse(
            provider=MockDataProvider,
            query=query,
            limit=limit,
            offset=offset,
            sort=sort,
            records=records,
            total=total
        )


def test_data_provider_search():
    """Test DataProvider search functionality."""
    result = MockDataProvider.search("gatsby")

    assert result.total == 1
    assert len(result.records) == 1
    assert result.records[0].title == "The Great Gatsby"


def test_data_provider_search_multiple_results():
    """Test DataProvider search with multiple results."""
    result = MockDataProvider.search("the")

    # "The Great Gatsby" (only title matches "the")
    assert result.total == 1


def test_data_provider_search_no_results():
    """Test DataProvider search with no results."""
    result = MockDataProvider.search("xyz123")

    assert result.total == 0
    assert len(result.records) == 0


def test_data_provider_search_pagination():
    """Test DataProvider search with pagination."""
    # Get all results
    all_results = MockDataProvider.search("")
    assert all_results.total == 3

    # Get first result with limit
    results = MockDataProvider.search("", limit=1)
    assert len(results.records) == 1

    # Get second result with offset
    results = MockDataProvider.search("", limit=1, offset=1)
    assert len(results.records) == 1
    assert results.records[0].title == "To Kill a Mockingbird"


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
        links=[Link(rel="self", href="https://example.com/catalog")]
    )

    assert len(catalog.publications) == 1
    assert catalog.publications[0].metadata.title == "Test Book"
    assert len(catalog.links) == 1
    assert catalog.links[0].rel == "self"


def test_create_catalog_with_search():
    """Test creating a catalog from search results."""
    search_result = MockDataProvider.search("gatsby")
    catalog = Catalog.create(response=search_result)

    assert len(catalog.publications) == 1
    assert catalog.publications[0].metadata.title == "The Great Gatsby"
    # Check that pagination links are added
    assert any(link.rel == "self" for link in catalog.links)


def test_create_catalog_with_search_pagination():
    """Test creating a catalog with paginated search results."""
    search_result = MockDataProvider.search("", limit=2, offset=0)
    catalog = Catalog.create(response=search_result)

    assert len(catalog.publications) == 2
    assert catalog.metadata.numberOfItems == 3
    assert catalog.metadata.currentPage == 1
    # Should have next and last links
    assert any(link.rel == "next" for link in catalog.links)
    assert any(link.rel == "last" for link in catalog.links)


def test_create_search_catalog_no_results():
    """Test creating a search catalog with no results."""
    search_result = MockDataProvider.search("xyz123")
    catalog = Catalog.create(response=search_result)

    assert catalog.metadata.numberOfItems == 0
    assert catalog.publications == []


def test_create_search_catalog_json():
    """Test creating a search catalog and exporting to JSON."""
    search_result = MockDataProvider.search("orwell")
    catalog = Catalog.create(response=search_result)

    json_str = catalog.model_dump_json()
    data = json.loads(json_str)

    assert "@context" in data
    assert data["metadata"]["numberOfItems"] == 1
    assert len(data["publications"]) == 1
    assert data["publications"][0]["metadata"]["title"] == "1984"


def test_catalog_integration():
    """Integration test: create a full catalog with search."""
    # Create main catalog with metadata
    catalog = Catalog.create(
        metadata=Metadata(
            title="Library Catalog",
            identifier="urn:uuid:1234-5678",
            modified=datetime(2024, 1, 1)
        ),
        publications=[],
        links=[
            Link(rel="self", href="https://example.com/catalog"),
            Link(
                rel="search",
                href="https://example.com/search?q={searchTerms}",
                templated=True
            )
        ]
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
    search_result = MockDataProvider.search("gatsby")
    search_catalog = Catalog.create(response=search_result)
    search_json = search_catalog.model_dump_json()
    search_data = json.loads(search_json)

    assert len(search_data["publications"]) == 1
    pub_title = search_data["publications"][0]["metadata"]["title"]
    assert pub_title == "The Great Gatsby"
