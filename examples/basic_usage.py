"""Example usage of the OPDS 2.0 library.

This example demonstrates:
1. Creating a custom DataProvider with the new architecture
2. Generating a catalog with search capability
3. Performing searches and generating search result catalogs
"""

import json
from typing import Dict, Any

from opds2 import (
    Catalog,
    DataProvider,
    ItemMapping,
    SearchResult,
    create_catalog,
    create_search_catalog,
)


class SimpleBookProvider(DataProvider):
    """A simple data provider with a small book collection.
    
    This demonstrates the new architecture where:
    1. search() returns SearchResult with raw data
    2. get_item_mapping() defines how to map fields to OPDS
    """

    def __init__(self):
        # Sample book data in a simple format
        self.books = [
            {
                "title": "Pride and Prejudice",
                "author": "Jane Austen",
                "language": "en",
                "description": "A romantic novel of manners",
                "url": "https://example.com/books/pride-prejudice.epub",
                "cover": "https://example.com/covers/pride.jpg",
            },
            {
                "title": "Moby Dick",
                "author": "Herman Melville",
                "language": "en",
                "description": "The saga of Captain Ahab",
                "url": "https://example.com/books/moby-dick.epub",
                "cover": "https://example.com/covers/moby.jpg",
            },
            {
                "title": "The Odyssey",
                "author": "Homer",
                "language": "en",
                "description": "Ancient Greek epic poem",
                "url": "https://example.com/books/odyssey.epub",
                "cover": "https://example.com/covers/odyssey.jpg",
            },
        ]

    def search(self, query: str, page: int = 1, rows: int = 50) -> SearchResult:
        """Search books by title or author.
        
        Returns raw search data in a SearchResult, not Publications.
        """
        query_lower = query.lower()
        
        # Filter books based on query
        filtered = [
            book
            for book in self.books
            if not query or query_lower in book["title"].lower()
            or query_lower in book["author"].lower()
        ]
        
        # Calculate pagination
        offset = (page - 1) * rows
        paginated = filtered[offset : offset + rows]
        
        return SearchResult(
            items=paginated,
            page=page,
            num_found=len(filtered),
            rows=rows
        )
    
    def get_item_mapping(self) -> ItemMapping:
        """Define how to map our book data to OPDS fields."""
        return ItemMapping(
            title=lambda item: item.get("title"),
            author=lambda item: [item.get("author")] if item.get("author") else [],
            language=lambda item: [item.get("language")] if item.get("language") else None,
            description=lambda item: item.get("description"),
            cover_url=lambda item: item.get("cover"),
            acquisition_link=lambda item: item.get("url"),
            acquisition_type=lambda item: "application/epub+zip",
        )


def main():
    """Run example demonstrations."""
    print("=" * 80)
    print("OPDS 2.0 Library Example")
    print("=" * 80)
    print()

    # Create a data provider
    provider = SimpleBookProvider()

    # Example 1: Create a basic catalog
    print("Example 1: Basic Catalog")
    print("-" * 80)
    catalog = create_catalog(
        title="My Book Collection",
        self_link="https://example.com/catalog",
        search_link="https://example.com/search?q={searchTerms}",
        identifier="urn:uuid:example-catalog-001",
    )
    print(json.dumps(json.loads(catalog.model_dump_json()), indent=2))
    print()

    # Example 2: Create a catalog with all books (via search)
    print("Example 2: Catalog with All Books")
    print("-" * 80)
    all_books_catalog = create_search_catalog(
        provider=provider,
        query="",  # Empty query returns all
        self_link="https://example.com/catalog/all",
    )
    print(json.dumps(json.loads(all_books_catalog.model_dump_json()), indent=2))
    print()

    # Example 3: Search catalog
    print("Example 3: Search Results for 'Pride'")
    print("-" * 80)
    search_catalog = create_search_catalog(
        provider=provider,
        query="Pride",
        self_link="https://example.com/search?q=Pride",
    )
    print(json.dumps(json.loads(search_catalog.model_dump_json()), indent=2))
    print()

    # Example 4: Another search
    print("Example 4: Search Results for 'Homer'")
    print("-" * 80)
    search_catalog2 = create_search_catalog(
        provider=provider,
        query="Homer",
        self_link="https://example.com/search?q=Homer",
    )
    print(json.dumps(json.loads(search_catalog2.model_dump_json()), indent=2))
    print()
    
    # Example 5: Demonstrate raw search result
    print("Example 5: Raw Search Result (before OPDS conversion)")
    print("-" * 80)
    raw_result = provider.search("Moby", page=1, rows=10)
    print(f"Total found: {raw_result.num_found}")
    print(f"Page: {raw_result.page}, Rows: {raw_result.rows}")
    print(f"Items returned: {len(raw_result.items)}")
    if raw_result.items:
        print("\nFirst item (raw):")
        print(json.dumps(raw_result.items[0], indent=2))
    print()


if __name__ == "__main__":
    main()
