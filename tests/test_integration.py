"""Integration test demonstrating the full OPDS 2.0 workflow."""

import json
from datetime import datetime, timezone

from opds2 import (
    Catalog,
    DataProvider,
    ItemMapping,
    SearchResult,
    create_catalog,
    create_search_catalog,
)


class TestIntegration:
    """Full integration tests for OPDS 2.0 library."""

    def test_complete_workflow(self):
        """Test the complete workflow from DataProvider to JSON output."""

        # Step 1: Create a DataProvider implementation
        class SimpleProvider(DataProvider):
            def search(self, query: str, page: int = 1, rows: int = 50) -> SearchResult:
                books = [
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

                # Filter and paginate
                filtered = [
                    book for book in books
                    if not query or query.lower() in book["title"].lower()
                ]
                
                offset = (page - 1) * rows
                paginated = filtered[offset:offset + rows]
                
                return SearchResult(
                    items=paginated,
                    page=page,
                    num_found=len(filtered),
                    rows=rows
                )
            
            def get_item_mapping(self) -> ItemMapping:
                return ItemMapping(
                    title=lambda item: item.get("title"),
                    author=lambda item: [item.get("author")] if item.get("author") else [],
                    acquisition_link=lambda item: item.get("url"),
                    acquisition_type=lambda item: "application/epub+zip",
                )

        provider = SimpleProvider()

        # Step 2: Create a main catalog
        main_catalog = create_catalog(
            title="Main Library Catalog",
            self_link="https://example.com/catalog",
            search_link="https://example.com/search?q={searchTerms}",
            identifier="urn:uuid:test-catalog",
            modified=datetime(2024, 1, 1, tzinfo=timezone.utc),
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
        search_results = create_search_catalog(
            provider=provider,
            query="Book 1",
            rows=10,
            self_link="https://example.com/search?q=Book+1",
        )

        # Verify search results
        assert len(search_results.publications) == 1
        assert search_results.publications[0].metadata.title == "Test Book 1"
        assert search_results.metadata.numberOfItems == 1

        # Verify search JSON output
        search_json = search_results.model_dump_json()
        search_data = json.loads(search_json)
        assert "@context" in search_data
        assert search_data["metadata"]["numberOfItems"] == 1
        assert len(search_data["publications"]) == 1
        assert (
            search_data["publications"][0]["metadata"]["title"] == "Test Book 1"
        )

        # Step 4: Get all publications
        all_books_catalog = create_search_catalog(
            provider=provider,
            query="",  # Empty query returns all
            self_link="https://example.com/all",
        )

        assert len(all_books_catalog.publications) == 2

        # Verify complete JSON structure
        all_json = all_books_catalog.model_dump_json()
        all_data = json.loads(all_json)

        # Check JSON-LD context
        assert all_data["@context"] == "https://readium.org/webpub-manifest/context.jsonld"

        # Check metadata
        assert "metadata" in all_data
        assert "title" in all_data["metadata"]
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
        from opds2.models import Publication, Metadata, Contributor, Link
        
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
        catalog = create_catalog(
            title="Direct Publications Catalog",
            publications=[pub1, pub2],
            self_link="https://example.com/direct",
        )

        assert len(catalog.publications) == 2
        assert catalog.publications[0].metadata.title == "Direct Book 1"
        assert catalog.publications[1].metadata.title == "Direct Book 2"

        # Verify JSON
        json_str = catalog.model_dump_json()
        data = json.loads(json_str)

        assert data["@context"] == "https://readium.org/webpub-manifest/context.jsonld"
        assert len(data["publications"]) == 2
        assert data["publications"][0]["metadata"]["language"] == ["en"]
        assert data["publications"][1]["metadata"]["language"] == ["es"]

    def test_empty_catalog(self):
        """Test creating an empty catalog."""
        catalog = create_catalog(title="Empty Catalog")

        assert catalog.metadata.title == "Empty Catalog"
        assert catalog.publications == []
        assert catalog.links == []

        # Verify JSON
        json_str = catalog.model_dump_json()
        data = json.loads(json_str)

        assert "@context" in data
        assert data["metadata"]["title"] == "Empty Catalog"
        assert data["publications"] == []

    def test_json_serialization_with_datetime(self):
        """Test that datetime objects serialize correctly to JSON."""
        catalog = create_catalog(
            title="Catalog with Date",
            modified=datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc),
        )

        # Should not raise an exception
        json_str = catalog.model_dump_json()
        data = json.loads(json_str)

        assert data["metadata"]["modified"] is not None
        # Verify it's a string representation
        assert isinstance(data["metadata"]["modified"], str)
    
    def test_search_result_and_mapping(self):
        """Test SearchResult and ItemMapping directly."""
        # Create a provider with specific mapping
        class TestProvider(DataProvider):
            def search(self, query: str, page: int = 1, rows: int = 50) -> SearchResult:
                items = [
                    {"title": "Book A", "author_name": "Author A", "cover_id": 123},
                    {"title": "Book B", "author_name": "Author B", "cover_id": 456},
                ]
                return SearchResult(items=items, page=page, num_found=2, rows=rows)
            
            def get_item_mapping(self) -> ItemMapping:
                return ItemMapping(
                    title=lambda item: item.get("title"),
                    author=lambda item: [item.get("author_name")] if item.get("author_name") else [],
                    cover_url=lambda item: f"https://example.com/cover/{item['cover_id']}.jpg" 
                        if item.get("cover_id") else None,
                )
        
        provider = TestProvider()
        
        # Test search result
        result = provider.search("test")
        assert result.num_found == 2
        assert result.page == 1
        assert result.rows == 50
        assert len(result.items) == 2
        
        # Test mapping
        mapping = provider.get_item_mapping()
        mapped = mapping.map_item(result.items[0])
        assert mapped["title"] == "Book A"
        assert mapped["author"] == ["Author A"]
        assert "cover_url" in mapped
        assert "123.jpg" in mapped["cover_url"]
