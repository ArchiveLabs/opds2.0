"""Integration test demonstrating the full OPDS 2.0 workflow."""

import json
from datetime import datetime, timezone
from typing import List, Optional

from pyopds2 import Catalog, Contributor, Link, Metadata, Publication
from pyopds2.provider import DataProvider, DataProviderRecord


class SimpleBook(DataProviderRecord):
    """Simple book record for testing."""
    title: str
    author: str
    url: str

    def metadata(self) -> Metadata:
        """Return book metadata."""
        return Metadata(
            title=self.title,
            author=[Contributor(name=self.author, role="author")]
        )

    def links(self) -> List[Link]:
        """Return book links."""
        return [
            Link(
                href=self.url,
                type="application/epub+zip",
                rel="http://opds-spec.org/acquisition",
            )
        ]

    def images(self) -> Optional[List[Link]]:
        """Return book images."""
        return None


class TestIntegration:
    """Full integration tests for OPDS 2.0 library."""

    def test_complete_workflow(self):
        """Test the complete workflow from DataProvider to JSON output."""

        # Step 1: Create a DataProvider implementation
        class SimpleProvider(DataProvider):
            TITLE = "Simple Library"
            BASE_URL = "https://example.com"
            SEARCH_URL = "/search{?query}"

            BOOKS = [
                {
                    "title": "Test Book 1",
                    "author": "Author One",
                    "url": "https://example.com/book1.epub",
                },
                {
                    "title": "Test Book 2",
                    "author": "Author Two",
                    "url": "https://example.com/book2.epub",
                },
            ]

            @staticmethod
            def search(
                query: str,
                limit: int = 50,
                offset: int = 0,
                sort: Optional[str] = None
            ) -> DataProvider.SearchResponse:
                """Search for books."""
                results = []
                for book in SimpleProvider.BOOKS:
                    if not query or query.lower() in book["title"].lower():
                        results.append(book)

                total = len(results)
                paginated = results[offset:offset + limit]
                records = [SimpleBook(**book) for book in paginated]

                return DataProvider.SearchResponse(
                    provider=SimpleProvider,
                    query=query,
                    limit=limit,
                    offset=offset,
                    sort=sort,
                    records=records,
                    total=total
                )

        # Step 2: Create a main catalog
        main_catalog = Catalog.create(
            metadata=Metadata(
                title="Main Library Catalog",
                identifier="urn:uuid:test-catalog",
                modified=datetime(2024, 1, 1, tzinfo=timezone.utc),
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

        # Verify main catalog structure
        assert main_catalog.metadata.title == "Main Library Catalog"
        assert main_catalog.metadata.identifier == "urn:uuid:test-catalog"
        assert len(main_catalog.links) == 2

        # Verify JSON output
        main_json = main_catalog.model_dump_json()
        main_data = json.loads(main_json)
        assert "@context" in main_data
        assert main_data["metadata"]["title"] == "Main Library Catalog"
        assert main_data["links"][1]["rel"] == "search"
        assert main_data["links"][1]["templated"] is True

        # Step 3: Perform a search
        search_results = SimpleProvider.search("Book 1", limit=10)
        search_catalog = Catalog.create(response=search_results)

        # Verify search results
        assert len(search_catalog.publications) == 1
        assert search_catalog.publications[0].metadata.title == "Test Book 1"
        assert search_catalog.metadata.numberOfItems == 1

        # Verify search JSON output
        search_json = search_catalog.model_dump_json()
        search_data = json.loads(search_json)
        assert "@context" in search_data
        assert search_data["metadata"]["numberOfItems"] == 1
        assert len(search_data["publications"]) == 1
        pub_title = search_data["publications"][0]["metadata"]["title"]
        assert pub_title == "Test Book 1"

        # Step 4: Get all publications
        all_results = SimpleProvider.search("")
        all_books_catalog = Catalog.create(response=all_results)

        assert len(all_books_catalog.publications) == 2

        # Verify complete JSON structure
        all_json = all_books_catalog.model_dump_json()
        all_data = json.loads(all_json)

        # Check JSON-LD context
        assert (all_data["@context"] ==
                "https://readium.org/webpub-manifest/context.jsonld")

        # Check metadata
        assert "metadata" in all_data
        assert all_data["metadata"]["numberOfItems"] == 2

        # Check publications
        assert "publications" in all_data
        assert len(all_data["publications"]) == 2

        # Check first publication structure
        pub = all_data["publications"][0]
        assert "metadata" in pub
        assert "title" in pub["metadata"]
        assert "author" in pub["metadata"]
        assert len(pub["metadata"]["author"]) == 1
        assert "name" in pub["metadata"]["author"][0]
        assert "links" in pub
        assert len(pub["links"]) == 1
        assert pub["links"][0]["type"] == "application/epub+zip"

    def test_catalog_with_publications_directly(self):
        """Test creating a catalog with publications directly (not via search)."""
        # Create publications manually
        pub1 = Publication(
            metadata=Metadata(
                title="Direct Book 1",
                author=[Contributor(name="Direct Author", role="author")],
                language=["en"],
            ),
            links=[
                Link(
                    href="https://example.com/direct1.epub",
                    type="application/epub+zip",
                )
            ],
        )

        pub2 = Publication(
            metadata=Metadata(
                title="Direct Book 2",
                author=[Contributor(name="Another Author", role="author")],
                language=["es"],
            ),
            links=[
                Link(
                    href="https://example.com/direct2.epub",
                    type="application/epub+zip",
                )
            ],
        )

        # Create catalog with these publications
        catalog = Catalog.create(
            metadata=Metadata(title="Direct Publications Catalog"),
            publications=[pub1, pub2],
            links=[Link(rel="self", href="https://example.com/direct")]
        )

        assert len(catalog.publications) == 2
        assert catalog.publications[0].metadata.title == "Direct Book 1"
        assert catalog.publications[1].metadata.title == "Direct Book 2"

        # Verify JSON
        json_str = catalog.model_dump_json()
        data = json.loads(json_str)

        assert (data["@context"] ==
                "https://readium.org/webpub-manifest/context.jsonld")
        assert len(data["publications"]) == 2
        assert data["publications"][0]["metadata"]["language"] == ["en"]
        assert data["publications"][1]["metadata"]["language"] == ["es"]

    def test_empty_catalog(self):
        """Test creating an empty catalog."""
        catalog = Catalog.create(
            metadata=Metadata(title="Empty Catalog")
        )

        assert catalog.metadata.title == "Empty Catalog"
        assert catalog.publications == []
        assert catalog.links == []

        # Verify JSON
        json_str = catalog.model_dump_json()
        data = json.loads(json_str)

        assert "@context" in data
        assert data["metadata"]["title"] == "Empty Catalog"

    def test_json_serialization_with_datetime(self):
        """Test that datetime objects serialize correctly to JSON."""
        catalog = Catalog.create(
            metadata=Metadata(
                title="Catalog with Date",
                modified=datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc),
            )
        )

        # Should not raise an exception
        json_str = catalog.model_dump_json()
        data = json.loads(json_str)

        assert data["metadata"]["modified"] is not None
        # Verify it's a string representation
        assert isinstance(data["metadata"]["modified"], str)
